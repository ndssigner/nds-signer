/*
 * NDS-Signer - Air-gapped Bitcoin PSBT signer for Nintendo DSi / 3DS
 * SPDX-License-Identifier: MIT
 *
 * Phase 2: live camera feed on the top screen, touch input on the bottom one.
 * When no camera is available (DS mode, or an emulator without camera
 * support) a test pattern is shown instead so the UI stays usable.
 */
#include <nds.h>
#include <stdio.h>
#include <string.h>

#include "camera.h"

/* Bottom screen text console: 32x24 cells of 8x8 pixels */
#define CELL 8

typedef struct {
	int col, row, width; /* in text cells; buttons are 3 rows high */
	const char *label;
} Button;

enum { BTN_SWAP, BTN_EXIT, BTN_COUNT };

static const Button s_buttons[BTN_COUNT] = {
	[BTN_SWAP] = { 1, 19, 14, "Swap camera" },
	[BTN_EXIT] = { 17, 19, 14, "Exit" },
};

static PrintConsole s_bottom;
static u16 *s_topFramebuffer;

static void initScreens(void)
{
	/* Top: 16-bit bitmap the camera DMA writes straight into */
	videoSetMode(MODE_5_2D);
	vramSetBankA(VRAM_A_MAIN_BG);
	int bg = bgInit(3, BgType_Bmp16, BgSize_B16_256x256, 0, 0);
	s_topFramebuffer = bgGetGfxPtr(bg);

	/* Bottom: text console for status and touch buttons */
	videoSetModeSub(MODE_0_2D);
	vramSetBankC(VRAM_C_SUB_BG);
	consoleInit(&s_bottom, 0, BgType_Text4bpp, BgSize_T_256x256, 31, 0, false, true);

	lcdMainOnTop();
}

/* Color bars shown when there is no camera */
static void drawTestPattern(void)
{
	static const u16 bars[] = {
		RGB15(31, 31, 31), RGB15(31, 31, 0), RGB15(0, 31, 31), RGB15(0, 31, 0),
		RGB15(31, 0, 31), RGB15(31, 0, 0), RGB15(0, 0, 31), RGB15(0, 0, 0),
	};
	const int nbars = sizeof(bars) / sizeof(bars[0]);

	for (int y = 0; y < CAMERA_PREVIEW_HEIGHT; y++)
		for (int x = 0; x < CAMERA_PREVIEW_WIDTH; x++)
			s_topFramebuffer[y * 256 + x] =
				bars[x * nbars / CAMERA_PREVIEW_WIDTH] | BIT(15);
}

static void drawButton(const Button *b)
{
	int inner = b->width - 2;
	int pad = (inner - (int)strlen(b->label)) / 2;

	printf("\x1b[%d;%dH+", b->row, b->col);
	for (int i = 0; i < inner; i++) putchar('-');
	printf("+\x1b[%d;%dH|%*s%s%*s|", b->row + 1, b->col,
	       pad, "", b->label, inner - pad - (int)strlen(b->label), "");
	printf("\x1b[%d;%dH+", b->row + 2, b->col);
	for (int i = 0; i < inner; i++) putchar('-');
	putchar('+');
}

static int hitTest(const touchPosition *t)
{
	for (int i = 0; i < BTN_COUNT; i++) {
		const Button *b = &s_buttons[i];
		if (t->px >= b->col * CELL && t->px < (b->col + b->width) * CELL &&
		    t->py >= b->row * CELL && t->py < (b->row + 3) * CELL)
			return i;
	}
	return -1;
}

static const char *cameraName(Camera cam)
{
	switch (cam) {
	case CAM_INNER: return "inner";
	case CAM_OUTER: return "outer";
	default:        return "none (test pattern)";
	}
}

static void drawStatus(unsigned frames)
{
	printf("\x1b[4;0HCamera: %-24s", cameraName(cameraActive()));
	printf("\x1b[5;0HFrames: %-10u", frames);
}

static void drawTouch(const touchPosition *t, bool down)
{
	if (down)
		printf("\x1b[7;0HTouch:  x=%3d y=%3d   ", t->px, t->py);
	else
		printf("\x1b[7;0HTouch:  -              ");
}

int main(void)
{
	initScreens();
	consoleSelect(&s_bottom);

	printf("NDS-Signer  (camera test)\n");
	printf("%s mode\n", isDSiMode() ? "DSi" : "DS");

	bool haveCamera = cameraInit() && cameraActivate(CAM_OUTER);
	if (!haveCamera) {
		drawTestPattern();
		printf("\x1b[9;0HNo camera available.");
	}

	for (int i = 0; i < BTN_COUNT; i++)
		drawButton(&s_buttons[i]);

	unsigned frames = 0;
	bool transferring = false;
	int pressedButton = -1;

	for (;;) {
		swiWaitForVBlank();

		if (haveCamera && cameraActive() != CAM_NONE) {
			if (transferring && !cameraTransferActive()) {
				frames++;
				transferring = false;
			}
			if (!transferring) {
				cameraTransferStart(s_topFramebuffer, CAPTURE_MODE_PREVIEW);
				transferring = true;
			}
		}

		scanKeys();
		u32 down = keysDown();
		u32 held = keysHeld();

		touchPosition touch = { 0 };
		bool touching = held & KEY_TOUCH;
		if (touching)
			touchRead(&touch);
		drawTouch(&touch, touching);
		drawStatus(frames);

		/* A button fires when the stylus is lifted over the same button it
		 * went down on, like a regular touch UI. */
		if (down & KEY_TOUCH)
			pressedButton = hitTest(&touch);
		int released = -1;
		if (pressedButton >= 0 && !touching) {
			released = pressedButton;
			pressedButton = -1;
		} else if (pressedButton >= 0 && hitTest(&touch) != pressedButton) {
			pressedButton = -1; /* slid off the button: cancel */
		}

		if (released == BTN_EXIT || (down & KEY_START))
			break;

		if ((released == BTN_SWAP || (down & KEY_A)) && haveCamera) {
			Camera next = cameraActive() == CAM_INNER ? CAM_OUTER : CAM_INNER;
			cameraTransferStop();
			transferring = false;
			if (!cameraActivate(next))
				printf("\x1b[9;0HCamera switch failed.");
		}
	}

	/* Turn the camera (and its LED) off before returning to the loader */
	if (haveCamera)
		cameraDeactivate();

	return 0;
}
