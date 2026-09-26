/*
 * NDS-Signer - minimal touch UI toolkit for the text consoles
 * SPDX-License-Identifier: MIT
 */
#include <stdio.h>
#include <string.h>

#include "ui.h"

#define CELL 8

PrintConsole g_uiTop;
PrintConsole g_uiBottom;

static u16 *s_topBitmap;
static int s_pressed = -1;

void uiInit(void)
{
	/* Top: VRAM A+B form 256 KB of main BG memory.
	 *   0 KB .. 2 KB   text map      (map base 0)
	 *  16 KB .. 24 KB  font tiles    (tile base 1)
	 *  32 KB .. 160 KB 256x256x16bpp bitmap (bitmap base 2) */
	videoSetMode(MODE_5_2D);
	vramSetBankA(VRAM_A_MAIN_BG_0x06000000);
	vramSetBankB(VRAM_B_MAIN_BG_0x06020000);
	consoleInit(&g_uiTop, 0, BgType_Text4bpp, BgSize_T_256x256, 0, 1, true, true);
	int bg = bgInit(3, BgType_Bmp16, BgSize_B16_256x256, 2, 0);
	s_topBitmap = bgGetGfxPtr(bg);

	/* Bottom: text console */
	videoSetModeSub(MODE_0_2D);
	vramSetBankC(VRAM_C_SUB_BG);
	consoleInit(&g_uiBottom, 0, BgType_Text4bpp, BgSize_T_256x256, 31, 0, false, true);

	lcdMainOnTop();
	uiClearTop();
}

u16 *uiTopBitmap(void)
{
	return s_topBitmap;
}

void uiClearTop(void)
{
	dmaFillHalfWords(RGB15(0, 0, 0) | BIT(15), s_topBitmap, 256 * 192 * 2);
	consoleSelect(&g_uiTop);
	consoleClear();
}

void uiClearBottom(void)
{
	consoleSelect(&g_uiBottom);
	consoleClear();
	s_pressed = -1;
}

static void drawButton(const UiButton *b)
{
	int inner = b->width - 2;
	int len = (int)strlen(b->label);
	int pad = (inner - len) / 2;

	printf("\x1b[%d;%dH+", b->row, b->col);
	for (int i = 0; i < inner; i++) putchar('-');
	printf("+\x1b[%d;%dH|%*s%s%*s|", b->row + 1, b->col, pad, "", b->label,
	       inner - pad - len, "");
	printf("\x1b[%d;%dH+", b->row + 2, b->col);
	for (int i = 0; i < inner; i++) putchar('-');
	putchar('+');
}

void uiDrawButtons(const UiButton *buttons, int count)
{
	consoleSelect(&g_uiBottom);
	for (int i = 0; i < count; i++)
		drawButton(&buttons[i]);
}

static int hitTest(const UiButton *buttons, int count, const touchPosition *t)
{
	for (int i = 0; i < count; i++) {
		const UiButton *b = &buttons[i];
		if (t->px >= b->col * CELL && t->px < (b->col + b->width) * CELL &&
		    t->py >= b->row * CELL && t->py < (b->row + 3) * CELL)
			return i;
	}
	return -1;
}

int uiPollButtons(const UiButton *buttons, int count)
{
	bool touching = keysHeld() & KEY_TOUCH;
	touchPosition t = { 0 };
	if (touching)
		touchRead(&t);

	if (keysDown() & KEY_TOUCH) {
		s_pressed = hitTest(buttons, count, &t);
		return -1;
	}
	if (s_pressed < 0)
		return -1;

	if (!touching) {
		int tapped = s_pressed;
		s_pressed = -1;
		return tapped;
	}
	if (hitTest(buttons, count, &t) != s_pressed)
		s_pressed = -1; /* slid off the button: cancel */
	return -1;
}

void uiPrintCentered(int row, const char *text)
{
	int len = (int)strlen(text);
	int col = len >= UI_COLS ? 0 : (UI_COLS - len) / 2;
	printf("\x1b[%d;%dH%s", row, col, text);
}

int uiPrintWrapped(int row, const char *text)
{
	char line[UI_COLS + 1];

	while (*text && row < UI_ROWS) {
		/* take as many whole words as fit in one row */
		int len = (int)strlen(text);
		int take = len;
		if (take > UI_COLS) {
			take = UI_COLS;
			while (take > 0 && text[take] != ' ')
				take--;
			if (take == 0)
				take = UI_COLS; /* single word longer than a row */
		}
		memcpy(line, text, take);
		line[take] = '\0';
		uiPrintCentered(row++, line);

		text += take;
		while (*text == ' ')
			text++;
	}
	return row;
}

void uiWarningScreen(const char *title, const char *statusHeadline,
                     const char *text, const char *detail, const char *buttonLabel)
{
	const UiButton button = { 4, 19, 24, buttonLabel };

	uiClearTop();
	uiPrintCentered(1, title);
	uiPrintCentered(6, "/!\\");
	uiPrintCentered(8, statusHeadline);
	int row = uiPrintWrapped(10, text);
	if (detail)
		uiPrintWrapped(row + 2, detail);

	uiClearBottom();
	uiDrawButtons(&button, 1);

	for (;;) {
		swiWaitForVBlank();
		scanKeys();
		if (uiPollButtons(&button, 1) == 0 || (keysDown() & (KEY_A | KEY_B)))
			break;
	}
	uiClearTop();
}
