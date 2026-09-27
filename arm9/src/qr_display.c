/*
 * NDS-Signer - draws QR codes on the top screen (Project Nayuki's qrcodegen)
 * SPDX-License-Identifier: MIT
 */
#include <nds.h>
#include <string.h>

#include "qr_display.h"
#include "qrcodegen.h"
#include "ui.h"

#define SCREEN_W 256
#define SCREEN_H 192

/* Static buffers: encoding needs up to ~7 KB, too much for the stack */
static uint8_t s_qr[qrcodegen_BUFFER_LEN_MAX];
static uint8_t s_temp[qrcodegen_BUFFER_LEN_MAX];
static char s_text[qrcodegen_BUFFER_LEN_MAX];

/* The frame is composed off-screen and copied to VRAM in one DMA burst right
 * after VBlank, so a half-drawn QR is never visible (no tearing/flicker). */
static u16 s_frame[SCREEN_W * SCREEN_H] __attribute__((aligned(32)));

int qrDisplayShow(const char *text, size_t len, int border, u8 background)
{
	if (len >= sizeof(s_text))
		return 0;
	memcpy(s_text, text, len);
	s_text[len] = '\0';

	if (!qrcodegen_encodeText(s_text, s_temp, s_qr, qrcodegen_Ecc_LOW,
	                          qrcodegen_VERSION_MIN, qrcodegen_VERSION_MAX,
	                          qrcodegen_Mask_AUTO, true))
		return 0;

	int size = qrcodegen_getSize(s_qr);
	int total = size + 2 * border;
	int scale = SCREEN_H / total;
	if (scale < 1)
		scale = 1;
	int x0 = (SCREEN_W - total * scale) / 2 + border * scale;
	int y0 = (SCREEN_H - total * scale) / 2 + border * scale;

	u16 light = RGB15(background >> 3, background >> 3, background >> 3) | BIT(15);
	u16 dark = RGB15(0, 0, 0) | BIT(15);
	u16 *fb = s_frame;

	/* Build each module row once, then copy it `scale` times */
	static u16 line[SCREEN_W];
	for (int x = 0; x < SCREEN_W; x++)
		line[x] = light;
	for (int y = 0; y < SCREEN_H; y++)
		memcpy(fb + y * 256, line, sizeof(line));

	for (int my = 0; my < size; my++) {
		for (int mx = 0; mx < size; mx++) {
			u16 c = qrcodegen_getModule(s_qr, mx, my) ? dark : light;
			for (int k = 0; k < scale; k++)
				line[x0 + mx * scale + k] = c;
		}
		for (int k = 0; k < scale; k++)
			memcpy(fb + (y0 + my * scale + k) * 256 + x0, line + x0, size * scale * sizeof(u16));
	}

	DC_FlushRange(s_frame, sizeof(s_frame));
	swiWaitForVBlank();
	dmaCopyWords(3, s_frame, uiTopBitmap(), sizeof(s_frame));
	return size;
}

#define ZOOM_PX 24  /* pixels per module when zoomed, as upstream */

int qrTranscribeShow(const u8 *data, size_t len, bool binary, int zoneModules,
                     int zoneX, int zoneY)
{
	if (len >= sizeof(s_text))
		return 0;
	bool ok;
	if (binary) {
		memcpy(s_temp, data, len);
		ok = qrcodegen_encodeBinary(s_temp, len, s_qr, qrcodegen_Ecc_LOW,
		                            qrcodegen_VERSION_MIN, qrcodegen_VERSION_MAX,
		                            qrcodegen_Mask_AUTO, false);
	} else {
		memcpy(s_text, data, len);
		s_text[len] = '\0';
		ok = qrcodegen_encodeText(s_text, s_temp, s_qr, qrcodegen_Ecc_LOW,
		                          qrcodegen_VERSION_MIN, qrcodegen_VERSION_MAX,
		                          qrcodegen_Mask_AUTO, false);
	}
	if (!ok)
		return 0;

	const int size = qrcodegen_getSize(s_qr);
	const u16 white = RGB15(31, 31, 31) | BIT(15);
	const u16 black = RGB15(0, 0, 0) | BIT(15);
	const u16 dimWhite = RGB15(14, 14, 14) | BIT(15);
	const u16 dimBlack = RGB15(4, 4, 4) | BIT(15);
	const u16 gridLine = RGB15(20, 20, 20) | BIT(15);
	int scale, x0, y0;

	if (zoneModules <= 0) {
		/* whole code, 1 module of quiet zone on each side */
		scale = SCREEN_H / (size + 2);
		x0 = (SCREEN_W - size * scale) / 2;
		y0 = (SCREEN_H - size * scale) / 2;
	} else {
		/* the zone's top-left module goes to the centred zone window */
		scale = ZOOM_PX;
		x0 = (SCREEN_W - zoneModules * scale) / 2 - zoneX * zoneModules * scale;
		y0 = (SCREEN_H - zoneModules * scale) / 2 - zoneY * zoneModules * scale;
	}

	for (int py = 0; py < SCREEN_H; py++) {
		u16 *row = s_frame + py * SCREEN_W;
		int my = py - y0 < 0 ? -1 : (py - y0) / scale;
		for (int px = 0; px < SCREEN_W; px++) {
			int mx = px - x0 < 0 ? -1 : (px - x0) / scale;
			bool dark = mx >= 0 && my >= 0 && mx < size && my < size &&
			            qrcodegen_getModule(s_qr, mx, my);
			u16 c = dark ? black : white;
			if (zoneModules > 0) {
				bool inZone = mx >= 0 && my >= 0 &&
				              mx / zoneModules == zoneX && my / zoneModules == zoneY &&
				              px - x0 >= 0 && py - y0 >= 0;
				if (!inZone)
					c = dark ? dimBlack : dimWhite;
				else if ((px - x0) % scale == 0 || (py - y0) % scale == 0)
					c = gridLine;  /* thin lines to count modules */
			}
			row[px] = c;
		}
	}

	DC_FlushRange(s_frame, sizeof(s_frame));
	swiWaitForVBlank();
	dmaCopyWords(3, s_frame, uiTopBitmap(), sizeof(s_frame));
	return size;
}
