/*
 * NDS-Signer - QR code scanner (DSi camera + quirc)
 * SPDX-License-Identifier: MIT
 */
#include <nds.h>
#include <malloc.h>
#include <stdlib.h>
#include <string.h>

#include "camera.h"
#include "qr_scanner.h"
#include "qrcodegen.h"
#include "quirc.h"
#include "ui.h"

#define CAP_W 640
#define CAP_H 480
#define VF_W  256
#define VF_H  192

/* Rows of the viewfinder dimmed so the instructions text drawn over them
 * stays readable (like SeedSigner's ScanScreen instructions bar). */
#define VF_BAR_TOP    172
#define VF_BAR_BOTTOM 188

static u16 *s_capture[2];     /* YUV422 frames written by the camera DMA */
static int s_dmaBuffer;       /* index of the buffer the DMA is filling */
static bool s_streaming;
static struct quirc *s_quirc;
static u16 s_vfColumn[VF_W];  /* viewfinder x -> capture x */

static ScanStats s_stats;
static int s_quickFails;      /* frames in a row with an undecoded QR, see decode() */
static int s_refineWait;      /* frames left before refining again, see decode() */

#ifdef NDS_SIGNER_DEVBUILD
/* quirc_end() stage times (lib/quirc/identify.c QUIRC_STAGE_MARK), in timer
 * ticks of the cpuStartTiming() run that decode() has open */
static u32 s_stageTicks[7];
static u32 s_jiggleTicks;
u32 g_quircStageUs[5];  /* otsu, binarize, finder, grouping, jiggle (part of grouping) */

void scannerStageMark(int stage);
void scannerStageMark(int stage)
{
	s_stageTicks[stage] = cpuGetTiming();
	if (stage == 0)
		s_jiggleTicks = 0;
	else if (stage == 6)
		s_jiggleTicks += s_stageTicks[6] - s_stageTicks[5];
	else if (stage == 4) {
		for (int i = 0; i < 4; i++)
			g_quircStageUs[i] = timerTicks2usec(s_stageTicks[i + 1] - s_stageTicks[i]);
		g_quircStageUs[4] = timerTicks2usec(s_jiggleTicks);
	}
}
#endif
static struct quirc_data s_data;

bool scannerInit(void)
{
	for (int i = 0; i < 2; i++) {
		/* 32-byte aligned so cache maintenance never touches neighbours */
		s_capture[i] = memalign(32, CAP_W * CAP_H * sizeof(u16));
		if (!s_capture[i])
			goto fail;
	}

	s_quirc = quirc_new();
	if (!s_quirc || quirc_resize(s_quirc, CAP_W, CAP_H) < 0)
		goto fail;

	for (int x = 0; x < VF_W; x++)
		s_vfColumn[x] = x * CAP_W / VF_W;

	if (!cameraInit())
		goto fail;
	return true;

fail:
	scannerShutdown();
	return false;
}

void scannerShutdown(void)
{
	scannerStop();
	if (s_quirc) {
		quirc_destroy(s_quirc);
		s_quirc = NULL;
	}
	for (int i = 0; i < 2; i++) {
		free(s_capture[i]);
		s_capture[i] = NULL;
	}
	scannerClearPayload();
}

void scannerClearPayload(void)
{
	/* volatile so the compiler cannot drop the wipe as a dead store */
	volatile u8 *p = (volatile u8 *)&s_data;
	for (size_t i = 0; i < sizeof(s_data); i++)
		p[i] = 0;
}

bool scannerStart(void)
{
	if (!s_quirc || !cameraActivate(CAM_OUTER))
		return false;

	memset(&s_stats, 0, sizeof(s_stats));
	s_stats.startMs = uiMillis();
	s_quickFails = 0;
	s_refineWait = 0;
	s_dmaBuffer = 0;
	cameraTransferStart(s_capture[s_dmaBuffer], CAPTURE_MODE_CAPTURE);
	s_streaming = true;
	return true;
}

void scannerStop(void)
{
	if (!s_streaming)
		return;
	cameraTransferStop();
	cameraDeactivate();
	s_streaming = false;
}

/* Y channel -> quirc image, and a downscaled grayscale viewfinder */
static void processFrame(const u16 *yuv, u16 *viewfinder)
{
	uint8_t *img = quirc_begin(s_quirc, NULL, NULL);

	/* YUYV: bytes 0 and 2 of every 32-bit word are the luma of two pixels.
	 * Four pixels per iteration with word accesses: main RAM is slow, and
	 * byte/halfword accesses one pixel at a time took ~100 ms per frame. */
	const u32 *src = (const u32 *)yuv;
	u32 *dst = (u32 *)img;  /* quirc's image is malloc'ed: word aligned */
	for (int i = 0; i < CAP_W * CAP_H / 4; i++) {
		u32 w0 = src[2 * i], w1 = src[2 * i + 1];
		dst[i] = (w0 & 0xFF) | ((w0 >> 8) & 0xFF00) |
		         ((w1 & 0xFF) << 16) | ((w1 << 8) & 0xFF000000);
	}

	for (int y = 0; y < VF_H; y++) {
		const u8 *row = img + (y * CAP_H / VF_H) * CAP_W;
		u16 *dst = viewfinder + y * 256;
		int shift = (y >= VF_BAR_TOP && y < VF_BAR_BOTTOM) ? 5 : 3;
		for (int x = 0; x < VF_W; x++) {
			u16 g = row[s_vfColumn[x]] >> shift;
			dst[x] = RGB15(g, g, g) | BIT(15);
		}
	}
}

/* quirc is built with QUIRC_LAZY_JIGGLE: quirc_end() skips its perspective
 * fitness search (most of its time on the DS), and quirc_refine() runs it
 * for a grid on demand. It helps when the QR is seen at an angle, not when
 * the frame is blurred, so it is only used after REFINE_AFTER frames in a
 * row showed a QR code that the quick read could not decode, and kept while
 * it is what makes frames decode. */
#define REFINE_AFTER 2
/* frames without refining after a refinement that did not decode: a QR code
 * cut by the frame edge or blurred keeps failing, at ~1 s per attempt */
#define REFINE_COOLDOWN 4

static bool decodeGrid(int index, bool refine, bool *refined)
{
	struct quirc_code code;

	for (;;) {
		quirc_extract(s_quirc, index, &code);
		quirc_decode_error_t err = quirc_decode(&code, &s_data);
		if (err == QUIRC_ERROR_DATA_ECC) {
			/* The QR might be mirrored (e.g. shown on a phone front camera) */
			quirc_flip(&code);
			err = quirc_decode(&code, &s_data);
		}
		if (err == QUIRC_SUCCESS)
			return true;
		s_stats.lastError = err;
		if (!refine || !quirc_refine(s_quirc, index))
			return false;
		*refined = true;
		s_stats.refines++;
	}
}

static bool decode(void)
{
	cpuStartTiming(0);
	quirc_end(s_quirc);
	u32 identifyUs = timerTicks2usec(cpuEndTiming());
	s_stats.sumIdentifyUs += identifyUs;

	cpuStartTiming(0);
	int count = quirc_count(s_quirc);
	bool found = false, refined = false;
	s_stats.lastGrids = count;
	s_stats.lastError = 0;

	bool refine = s_quickFails >= REFINE_AFTER && s_refineWait == 0;
	for (int i = 0; i < count && !found; i++)
		found = decodeGrid(i, refine, &refined);

	if (s_refineWait > 0)
		s_refineWait--;
	if (found)
		s_quickFails = refined ? REFINE_AFTER : 0;
	else if (count > 0) {
		s_quickFails++;
		if (refined)
			s_refineWait = REFINE_COOLDOWN;
	}

	u32 decodeUs = timerTicks2usec(cpuEndTiming());
	s_stats.sumDecodeUs += decodeUs;
	s_stats.lastDecodeUs = identifyUs + decodeUs;
	if (count > 0)
		s_stats.gridFrames++;
	if (found)
		s_stats.decoded++;
	return found;
}

ScanStatus scannerPoll(u16 *viewfinder)
{
	if (!s_streaming)
		return SCAN_ERROR;
	if (cameraTransferActive())
		return SCAN_IDLE;

	/* Frame complete: hand the other buffer to the DMA straight away */
	u16 *frame = s_capture[s_dmaBuffer];
	s_dmaBuffer ^= 1;
	cameraTransferStart(s_capture[s_dmaBuffer], CAPTURE_MODE_CAPTURE);

	/* The DMA wrote behind the CPU's back: drop stale cache lines */
	DC_InvalidateRange(frame, CAP_W * CAP_H * sizeof(u16));

	cpuStartTiming(0);
	processFrame(frame, viewfinder);
	s_stats.sumProcessUs += timerTicks2usec(cpuEndTiming());
	s_stats.frames++;

	return decode() ? SCAN_DECODED : SCAN_FRAME;
}

const u8 *scannerPayload(size_t *len)
{
	*len = s_data.payload_len;
	return s_data.payload;
}

const ScanStats *scannerStats(void)
{
	return &s_stats;
}

bool scannerBenchmark(const char *text, size_t len, int pixels, u32 *processUs,
                      u32 *identifyUs, u32 *decodeUs)
{
	static uint8_t qr[qrcodegen_BUFFER_LEN_MAX];
	static uint8_t temp[qrcodegen_BUFFER_LEN_MAX];
	static char str[qrcodegen_BUFFER_LEN_MAX];
	static u16 viewfinder[VF_W * VF_H];

	if (!s_quirc || s_streaming || len >= sizeof(str))
		return false;
	memcpy(str, text, len);
	str[len] = 0;
	if (!qrcodegen_encodeText(str, temp, qr, qrcodegen_Ecc_LOW,
	                          qrcodegen_VERSION_MIN, qrcodegen_VERSION_MAX,
	                          qrcodegen_Mask_AUTO, true))
		return false;

	/* A grey-ish frame like a camera's: dark modules 40, light 200 */
	int size = qrcodegen_getSize(qr);
	int scale = pixels / size < 1 ? 1 : pixels / size;
	int x0 = (CAP_W - size * scale) / 2, y0 = (CAP_H - size * scale) / 2;
	u16 *frame = s_capture[0];
	for (int y = 0; y < CAP_H; y++) {
		int my = y - y0 < 0 ? -1 : (y - y0) / scale;
		for (int x = 0; x < CAP_W; x++) {
			int mx = x - x0 < 0 ? -1 : (x - x0) / scale;
			bool dark = mx >= 0 && my >= 0 && mx < size && my < size &&
			            qrcodegen_getModule(qr, mx, my);
			frame[y * CAP_W + x] = 0x8000 | (dark ? 40 : 200);
		}
	}
	DC_FlushRange(frame, CAP_W * CAP_H * sizeof(u16));
	DC_InvalidateRange(frame, CAP_W * CAP_H * sizeof(u16));

	memset(&s_stats, 0, sizeof(s_stats));
	s_quickFails = 0;
	s_refineWait = 0;
	cpuStartTiming(0);
	processFrame(frame, viewfinder);
	*processUs = timerTicks2usec(cpuEndTiming());
	bool ok = decode();
	*identifyUs = s_stats.sumIdentifyUs;
	*decodeUs = s_stats.sumDecodeUs;
	ok = ok && s_data.payload_len == (int)len && memcmp(s_data.payload, text, len) == 0;
	scannerClearPayload();
	return ok;
}
