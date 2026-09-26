/*
 * NDS-Signer - runs the Python application (SPIKE, see docs/architecture.md):
 * SeedSigner's Controller and views on NDS-Signer's native screens.
 * SPDX-License-Identifier: MIT
 */
#include <nds.h>
#include <malloc.h>
#include <stdio.h>

#include "port/micropython_embed.h"
#include "py/cstack.h"
#include "ui.h"

#define MPY_HEAP_SIZE (6 * 1024 * 1024)

void mpyRunApp(void)
{
	char *heap = malloc(MPY_HEAP_SIZE);
	if (!heap) {
		consoleSelect(&g_uiTop);
		printf("Python heap alloc failed\n");
		return;
	}

	int stackTop;
	mp_embed_init(heap, MPY_HEAP_SIZE, &stackTop);
	/* the embed port sets the stack top but not its size */
	mp_cstack_init_with_top(&stackTop, 96 * 1024);

	mp_embed_exec_str("import nds_main\n");

	mp_embed_deinit();
	free(heap);
}
