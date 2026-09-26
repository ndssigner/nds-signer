/*
 * NDS-Signer - MicroPython feasibility spike (see docs/architecture.md)
 * SPDX-License-Identifier: MIT
 *
 * Signs tests/vectors/psbt_base64_singlesig.txt with upstream embit (frozen,
 * unmodified) and compares with the result of embit 0.8.0 on CPython.
 * The test vectors below are public test data. Never use them with funds.
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
	{ "import embit",
	  "import gc\nfor m in ('hashlib','hmac','binascii','embit.util','embit.hashes','embit.ec','embit.bip32','embit.bip39','embit.networks','embit.psbt'):\n    try:\n        __import__(m)\n        print('ok', m)\n    except Exception as e:\n        print('FAIL', m, repr(e)[:60])\n        break\nfrom embit import bip39, bip32\nfrom embit.psbt import PSBT\nfrom embit.networks import NETWORKS\n" },
	{ "bip39 seed (pbkdf2)",
	  "seed = bip39.mnemonic_to_seed('height demise useless trap grow lion found off key clown transfer enroll')\n" },
	{ "bip32 root",
	  "root = bip32.HDKey.from_seed(seed, version=NETWORKS['test']['xprv'])\nprint('fp', root.my_fingerprint.hex())\n" },
	{ "parse psbt",
	  "psbt = PSBT.from_string('cHNidP8BAHICAAAAAQDo5ey+2HIrNUkExsFhsImv1OK1cYA9x/bRjYQD+0UaAQAAAAD9////Apg6AAAAAAAAF6kUVuVZEcdpQ2zgABa9dRUNYHD4VuaHgSYAAAAAAAAWABQaLE4t0JbDRg4pNnmcf+cAWIcyawAAAAAAAQEfqGEAAAAAAAAWABRyuw9od6yuS0yiZljV0X12wG9e5CIGA/ZlEZvQubb6PmcnK+vlnd8aftYnrQ8wHYSxsD8tDp61GIshjoFUAACAAQAAgAAAAIAAAAAAAAAAAAAAAA==')\nprint('inputs', len(psbt.inputs), 'outputs', len(psbt.outputs))\n" },
	{ "sign",
	  "n = psbt.sign_with(root)\nprint('signed', n)\n" },
	{ "compare",
	  "print('MATCH' if psbt.to_string() == 'cHNidP8BAHICAAAAAQDo5ey+2HIrNUkExsFhsImv1OK1cYA9x/bRjYQD+0UaAQAAAAD9////Apg6AAAAAAAAF6kUVuVZEcdpQ2zgABa9dRUNYHD4VuaHgSYAAAAAAAAWABQaLE4t0JbDRg4pNnmcf+cAWIcyawAAAAAAAQEfqGEAAAAAAAAWABRyuw9od6yuS0yiZljV0X12wG9e5CICA/ZlEZvQubb6PmcnK+vlnd8aftYnrQ8wHYSxsD8tDp61RzBEAiAlB9Dg15hrxxFXX6yhOGTcoB8pMmsbcl1l6uctCPpIfAIgQy2qLfkhXj8AeWAMkkvQPObqWliOQH/j55ko4seVjBoBIgYD9mURm9C5tvo+Zycr6+Wd3xp+1ietDzAdhLGwPy0OnrUYiyGOgVQAAIABAACAAAAAgAAAAAAAAAAAAAAA' else 'MISMATCH')\ngc.collect()\nprint('heap used', gc.mem_alloc() // 1024, 'KB')\n" },
	{ "seedsigner PSBTParser",
	  "import psbt_parser_summary as t\ns = t.summary('cHNidP8BAHICAAAAAQDo5ey+2HIrNUkExsFhsImv1OK1cYA9x/bRjYQD+0UaAQAAAAD9////Apg6AAAAAAAAF6kUVuVZEcdpQ2zgABa9dRUNYHD4VuaHgSYAAAAAAAAWABQaLE4t0JbDRg4pNnmcf+cAWIcyawAAAAAAAQEfqGEAAAAAAAAWABRyuw9od6yuS0yiZljV0X12wG9e5CIGA/ZlEZvQubb6PmcnK+vlnd8aftYnrQ8wHYSxsD8tDp61GIshjoFUAACAAQAAgAAAAIAAAAAAAAAAAAAAAA==', 'height demise useless trap grow lion found off key clown transfer enroll')\nprint(s)\nprint('SUMMARY MATCH' if s == 'spend_amount 24857\\nchange_amount 0\\nfee_amount 143\\nnum_inputs 1\\nnum_destinations 2\\nnum_change_outputs 0\\ndestination_addresses 2N1Agr9voB5g4BhaTihLCuGFTFbbPBHVt7T,tb1qrgkyutwsjmp5vr3fxeuecll8qpvgwvnth2wa5k\\nis_high_fee False' else 'SUMMARY MISMATCH')\n" },
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
