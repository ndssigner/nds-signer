/*
 * NDS-Signer - implementation of nds_bridge.h on top of libnds and the ARM9
 * modules (ui, qr_scanner).
 * SPDX-License-Identifier: MIT
 */
#include <nds.h>
#include <malloc.h>
#include <stdio.h>
#include <string.h>

#include "nds_bridge.h"
#include "gfx.h"
#include "sfx.h"
#include "qr_display.h"
#include "qr_scanner.h"
#include "ui.h"

void ndsbPrint(int screen, int row, int col, const char *text, size_t len)
{
	if (row < 0 || row >= UI_ROWS)
		return;
	if (len > UI_COLS)
		len = UI_COLS;
	if (col < 0)
		col = (UI_COLS - (int)len) / 2;
	if (col >= UI_COLS)
		return;
	if (col + (int)len > UI_COLS)
		len = UI_COLS - col;
	consoleSelect(screen == NDSB_TOP ? &g_uiTop : &g_uiBottom);
	printf("\x1b[%d;%dH%.*s", row, col, (int)len, text);
}

void ndsbClear(int screen)
{
	/* the graphical UI's back buffer too, so a screen starts from black */
	gfxClear(screen == NDSB_TOP ? GFX_TOP : GFX_BOTTOM, 0);
	if (screen == NDSB_TOP)
		uiClearTop();
	else
		uiClearBottom();
}

void ndsbFrame(void)
{
	swiWaitForVBlank();
	scanKeys();
}

uint32_t ndsbKeysDown(void) { return keysDown(); }
uint32_t ndsbKeysHeld(void) { return keysHeld(); }

bool ndsbTouch(int *x, int *y)
{
	if (!(keysHeld() & KEY_TOUCH))
		return false;
	touchPosition t;
	touchRead(&t);
	*x = t.px;
	*y = t.py;
	return true;
}

uint32_t ndsbTicksMs(void)
{
	return uiMillis();
}

static bool s_haveCamera;

bool ndsbCameraInit(void)
{
	static bool done;
	if (!done) {
		s_haveCamera = scannerInit();
		done = true;
	}
	return s_haveCamera;
}

bool ndsbCameraStart(void)
{
	return s_haveCamera && scannerStart();
}

int ndsbCameraPoll(uint8_t *buf, size_t *len)
{
	ScanStatus st = scannerPoll(uiTopBitmap());
	if (st == SCAN_ERROR)
		return -1;
	if (st != SCAN_DECODED)
		return 0;
	const u8 *payload = scannerPayload(len);
	memcpy(buf, payload, *len);
	scannerClearPayload();
	return 1;
}

void ndsbCameraStop(void)
{
	scannerStop();
}

void ndsbCameraStats(uint32_t stats[NDSB_CAMERA_STATS])
{
	const ScanStats *s = scannerStats();
	stats[0] = s->frames;
	stats[1] = s->lastDecodeUs / 1000;
	stats[2] = s->gridFrames;
	stats[3] = s->decoded;
	stats[4] = s->sumProcessUs;
	stats[5] = s->sumIdentifyUs;
	stats[6] = s->sumDecodeUs;
	stats[7] = uiMillis() - s->startMs;
	stats[8] = s->refines;
	stats[9] = s->restarts;
}

#ifdef NDS_SIGNER_DEVBUILD
extern u32 g_quircStageUs[5];
#endif

int ndsbScanBenchmark(const char *text, size_t len, int pixels, uint32_t times[8])
{
	if (!ndsbCameraInit())
		return -1;
	int ok = scannerBenchmark(text, len, pixels, &times[0], &times[1], &times[2]) ? 1 : 0;
	for (int i = 0; i < 5; i++)
#ifdef NDS_SIGNER_DEVBUILD
		times[3 + i] = g_quircStageUs[i];
#else
		times[3 + i] = 0;
#endif
	return ok;
}

int ndsbQrShow(const char *text, size_t len, int border, int background)
{
	if (background < 0)
		background = 0;
	if (background > 255)
		background = 255;
	return qrDisplayShow(text, len, border, (u8)background);
}

void ndsbGfxClear(int screen, uint32_t rgb) { gfxClear(screen, rgb); }
void ndsbGfxRect(int screen, int x, int y, int w, int h, uint32_t rgb, int radius)
{
	gfxRect(screen, x, y, w, h, rgb, radius);
}
void ndsbGfxFrame(int screen, int x, int y, int w, int h, uint32_t rgb, int radius, int thickness)
{
	gfxFrame(screen, x, y, w, h, rgb, radius, thickness);
}
int ndsbGfxText(int screen, int x, int y, const char *utf8, size_t len, int font, uint32_t rgb,
                int maxWidth)
{
	return gfxText(screen, x, y, utf8, len, font, rgb, maxWidth);
}
int ndsbGfxTextWidth(const char *utf8, size_t len, int font) { return gfxTextWidth(utf8, len, font); }
void ndsbGfxFontMetrics(int font, int *ascent, int *lineHeight) { gfxFontMetrics(font, ascent, lineHeight); }
void ndsbGfxPresent(int screen) { gfxPresent(screen); }
int ndsbGfxFontCount(void) { return GFX_FONT_COUNT; }
void ndsbSound(int sfx) { sfxPlay(sfx); }

int ndsbQrTranscribe(const uint8_t *data, size_t len, bool binary, int zoneModules,
                     int zoneX, int zoneY)
{
	return qrTranscribeShow(data, len, binary, zoneModules, zoneX, zoneY);
}

#ifndef NDS_SIGNER_VERSION
#define NDS_SIGNER_VERSION "unknown"
#endif

const char *ndsbVersion(void)
{
	return NDS_SIGNER_VERSION;
}

void ndsbInfo(NdsbInfo *info)
{
	struct mallinfo mi = mallinfo();
	info->dsiMode = isDSiMode();
	info->cameraOk = s_haveCamera;
	info->cHeapKB = (uint32_t)mi.uordblks / 1024;
	info->uptimeS = uiMillis() / 1000;
}
