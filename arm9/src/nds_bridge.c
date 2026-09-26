/*
 * NDS-Signer - implementation of nds_bridge.h on top of libnds and the ARM9
 * modules (ui, qr_scanner).
 * SPDX-License-Identifier: MIT
 */
#include <nds.h>
#include <stdio.h>
#include <string.h>

#include "nds_bridge.h"
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
	return (uint32_t)(tickGetCount() * 1000 / TICK_FREQ);
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

void ndsbCameraStats(uint32_t *frames, uint32_t *decodeMs)
{
	const ScanStats *s = scannerStats();
	*frames = s->frames;
	*decodeMs = s->lastDecodeUs / 1000;
}

int ndsbQrShow(const char *text, size_t len, int border, int background)
{
	if (background < 0)
		background = 0;
	if (background > 255)
		background = 255;
	return qrDisplayShow(text, len, border, (u8)background);
}
