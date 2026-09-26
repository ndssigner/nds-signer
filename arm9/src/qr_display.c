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
