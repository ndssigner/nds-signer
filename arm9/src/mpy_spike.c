/*
 * NDS-Signer - MicroPython feasibility spike (see docs/architecture.md)
 * SPDX-License-Identifier: MIT
 */
#include <nds.h>
#include <malloc.h>
#include <stdio.h>

#include "port/micropython_embed.h"
#include "py/cstack.h"
#include "ui.h"

#define MPY_HEAP_SIZE (4 * 1024 * 1024)

static const char *const s_scripts[] = {
	"import sys\n"
	"print(sys.implementation.name, sys.version.split(' ')[0])\n"
	"print(sys.implementation._machine)\n",

	/* secp256k1 field prime and a modular inverse via Fermat: the kind of big
	 * integer work embit does in pure Python */
	"p = 2**256 - 2**32 - 977\n"
	"a = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798\n"
	"inv = pow(a, p - 2, p)\n"
	"print('inv ok' if a * inv % p == 1 else 'inv FAIL')\n",

	"import gc\n"
	"gc.collect()\n"
	"print('heap free', gc.mem_free(), 'used', gc.mem_alloc())\n",
};

void mpySpikeRun(void)
{
	uiClearTop();
	printf("MicroPython spike\n\n");

	char *heap = malloc(MPY_HEAP_SIZE);
	if (!heap) {
		printf("heap alloc failed\n");
		return;
	}
	struct mallinfo mi = mallinfo();
	printf("C heap after alloc: %d KB used\n\n", mi.uordblks / 1024);

	/* The embed port sets the stack top but not its size: without this every
	 * stack check fails. Leave margin below the app thread's 128 KB stack. */
	int stackTop;
	mp_embed_init(heap, MPY_HEAP_SIZE, &stackTop);
	mp_cstack_init_with_top(&stackTop, 96 * 1024);

	for (unsigned i = 0; i < sizeof(s_scripts) / sizeof(s_scripts[0]); i++) {
		cpuStartTiming(0);
		mp_embed_exec_str(s_scripts[i]);
		u32 us = timerTicks2usec(cpuEndTiming());
		printf("  [%lu ms]\n", (unsigned long)(us / 1000));
	}

	mp_embed_deinit();
	free(heap);
	printf("\ndone\n");
}
