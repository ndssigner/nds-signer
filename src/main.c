/*
 * NDS-Signer - Air-gapped Bitcoin PSBT signer for Nintendo DSi / 3DS
 * SPDX-License-Identifier: MIT
 *
 * Phase 1: bring up both screens with a text console and wait for START.
 */
#include <nds.h>
#include <stdio.h>

static PrintConsole topScreen;
static PrintConsole bottomScreen;

static void initScreens(void)
{
	/* Main engine drives the top LCD, sub engine the bottom (touch) LCD. */
	videoSetMode(MODE_0_2D);
	videoSetModeSub(MODE_0_2D);
	vramSetBankA(VRAM_A_MAIN_BG);
	vramSetBankC(VRAM_C_SUB_BG);
	lcdMainOnTop();

	consoleInit(&topScreen, 3, BgType_Text4bpp, BgSize_T_256x256, 31, 0, true, true);
	consoleInit(&bottomScreen, 3, BgType_Text4bpp, BgSize_T_256x256, 31, 0, false, true);
}

int main(void)
{
	initScreens();

	consoleSelect(&topScreen);
	printf("NDS-Signer Init\n");
	printf("\nRunning in %s mode\n", isDSiMode() ? "DSi" : "DS");

	consoleSelect(&bottomScreen);
	printf("Press START to exit\n");

	for (;;) {
		swiWaitForVBlank();
		scanKeys();
		if (keysDown() & KEY_START)
			break;
	}

	return 0;
}
