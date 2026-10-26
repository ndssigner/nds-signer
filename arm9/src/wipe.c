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
#include <stdalign.h>
#include <stddef.h>
#include <stdint.h>

#include "camera_pxi.h"
#include "gfx.h"
#include "qr_display.h"
#include "mic_entropy.h"
#include "qr_scanner.h"
#include "tones_audio.h"
#include "ui.h"
#include "wipe.h"

extern void *g_mpyHeap;
extern size_t g_mpyHeapSize;
extern u8 g_appStack[];
extern const size_t g_appStackSize;

/* The stack the last steps run on, once the app's own stack is cleared */
#define WIPE_STACK_SIZE 1024
alignas(8) static u8 s_wipeStack[WIPE_STACK_SIZE];

/* volatile: the stores must not be dropped as dead before the power off.
 * Words where p is aligned, bytes at either end, so no length or alignment
 * leaves bytes behind. */
void secureZero(void *p, size_t len)
{
	volatile u8 *b = (volatile u8 *)p;
	while (len && ((uintptr_t)b & 3)) {
		*b++ = 0;
		len--;
	}
	volatile u32 *w = (volatile u32 *)b;
	for (size_t i = 0; i < len / 4; i++)
		w[i] = 0;
	b = (volatile u8 *)(w + len / 4);
	for (size_t i = 0; i < (len & 3); i++)
		b[i] = 0;
}

/* Runs on s_wipeStack: the app's stack, where any C function (libsecp256k1,
 * hashlib, the seed PIN) may have left key material in its locals, is
 * cleared whole, the frames that called the wipe included */
static void __attribute__((noreturn, noinline)) wipeStackAndPowerOff(void)
{
	secureZero(g_appStack, g_appStackSize);
	DC_FlushAll();

	pxiSendAndReceive(PXI_CAMERA, CAM_CMD_POWER_OFF);
	for (;;)
		swiWaitForVBlank();
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
	micEntropyStop();
	tonesWipe();
	qrDisplayWipe();
	if (g_mpyHeap)
		secureZero(g_mpyHeap, g_mpyHeapSize);

	/* never returns, so nothing on the app's stack is needed any more */
	__asm__ volatile("mov sp, %0\n\tbx %1"
	                 :: "r"(&s_wipeStack[WIPE_STACK_SIZE]), "r"(wipeStackAndPowerOff)
	                 : "memory");
	__builtin_unreachable();
}
