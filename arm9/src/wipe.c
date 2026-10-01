/*
 * NDS-Signer - wipe on lid close / power button
 * SPDX-License-Identifier: MIT
 *
 * NDS-Signer never writes secrets to non-volatile memory, but RAM keeps its
 * contents while the console sleeps (lid closed) and for a moment after it
 * is switched off. So closing the lid does not suspend the app: everything
 * that may hold a seed, a passphrase or a PSBT is overwritten and the
 * console is turned off (the ARM7 never lets it sleep, see arm7/src/main.c).
 */
#include <nds.h>
#include <stddef.h>

#include "camera_pxi.h"
#include "gfx.h"
#include "qr_display.h"
#include "qr_scanner.h"
#include "ui.h"
#include "wipe.h"

extern void *g_mpyHeap;
extern size_t g_mpyHeapSize;

/* volatile: the stores must not be dropped as dead before the power off */
static void secureZero(void *p, size_t len)
{
	volatile u32 *w = (volatile u32 *)p;
	for (size_t i = 0; i < len / 4; i++)
		w[i] = 0;
}

void wipeAndPowerOff(void)
{
	/* screens first: nothing readable stays on them */
	setBrightness(3, -16);
	uiClearTop();
	uiClearBottom();
	gfxClear(GFX_TOP, 0);
	gfxClear(GFX_BOTTOM, 0);

	scannerWipe();
	qrDisplayWipe();
	if (g_mpyHeap)
		secureZero(g_mpyHeap, g_mpyHeapSize);
	DC_FlushAll();

	pxiSendAndReceive(PXI_CAMERA, CAM_CMD_POWER_OFF);
	for (;;)
		swiWaitForVBlank();
}
