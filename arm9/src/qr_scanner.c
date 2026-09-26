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
#include "quirc.h"

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

	/* YUYV: the low byte of every 16-bit word is the pixel's luma */
	for (int i = 0; i < CAP_W * CAP_H; i++)
		img[i] = (u8)yuv[i];

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

static bool decode(void)
{
	cpuStartTiming(0);
	quirc_end(s_quirc);

	int count = quirc_count(s_quirc);
	bool found = false;
	s_stats.lastGrids = count;
	s_stats.lastError = 0;

	for (int i = 0; i < count && !found; i++) {
		struct quirc_code code;
		quirc_extract(s_quirc, i, &code);

		quirc_decode_error_t err = quirc_decode(&code, &s_data);
		if (err == QUIRC_ERROR_DATA_ECC) {
			/* The QR might be mirrored (e.g. shown on a phone front camera) */
			quirc_flip(&code);
			err = quirc_decode(&code, &s_data);
		}
		if (err == QUIRC_SUCCESS)
			found = true;
		else
			s_stats.lastError = err;
	}

	s_stats.lastDecodeUs = timerTicks2usec(cpuEndTiming());
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

	processFrame(frame, viewfinder);
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
