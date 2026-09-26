/*
 * NDS-Signer - MicroPython feasibility spike (see docs/architecture.md)
 * SPDX-License-Identifier: MIT
 *
 * Runs the host test scripts (tests/host/..._check.py) unchanged on the DSi:
 * upstream SeedSigner + embit, frozen, against the CPython reference vectors.
 */
#include <nds.h>
#include <malloc.h>
#include <stdio.h>

#include "port/micropython_embed.h"
#include "py/cstack.h"
#include "ui.h"

#define MPY_HEAP_SIZE (4 * 1024 * 1024)

typedef struct {
	const char *name;
	const char *code;
} Step;

static const Step s_steps[] = {
	{ "seedsigner_check",
	  "import seedsigner_check\n" },
	{ "decode_qr_check",
	  "import decode_qr_check\n" },
	{ "verdict",
	  "import sys\nref = 'psbt-base64 status=3 type=psbt__base64 complete=True parts=1 psbt_sha256=a120fc689ed50aee'\nprint('\\n=== seedsigner_check:', 'PASSED' if seedsigner_check.failures == 0 else 'FAILED')\n" },
};

void mpySpikeRun(void)
{
	uiClearTop();
	printf("MicroPython + embit spike\n\n");

	char *heap = malloc(MPY_HEAP_SIZE);
	if (!heap) {
		printf("heap alloc failed\n");
		return;
	}

	/* The embed port sets the stack top but not its size: without this every
	 * stack check fails. Leave margin below the app thread's 128 KB stack. */
	int stackTop;
	mp_embed_init(heap, MPY_HEAP_SIZE, &stackTop);
	mp_cstack_init_with_top(&stackTop, 96 * 1024);

	u32 totalMs = 0;
	for (unsigned i = 0; i < sizeof(s_steps) / sizeof(s_steps[0]); i++) {
		printf("> %s\n", s_steps[i].name);
		cpuStartTiming(0);
		mp_embed_exec_str(s_steps[i].code);
		u32 ms = timerTicks2usec(cpuEndTiming()) / 1000;
		totalMs += ms;
		printf("  [%lu ms]\n", (unsigned long)ms);
	}
	printf("\ntotal %lu ms\n", (unsigned long)totalMs);

	mp_embed_deinit();
	free(heap);
}
