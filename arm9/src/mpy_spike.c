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
	{ "10in: seed + root",
	  "from seedsigner.models.seed import Seed\nseed10 = Seed('abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split())\nroot10 = bip32.HDKey.from_seed(seed10.seed_bytes, version=NETWORKS['test']['xprv'])\n" },
	{ "10in: PSBTParser",
	  "from seedsigner.models.psbt_parser import PSBTParser\nfrom seedsigner.models.settings import SettingsConstants\np10 = PSBT.from_string('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')\npp = PSBTParser(p=p10, seed=seed10, network=SettingsConstants.TESTNET)\nprint('SUMMARY10', 'MATCH' if t.summary('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', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about') == 'spend_amount 50000\\nchange_amount 48300\\nfee_amount 1700\\nnum_inputs 10\\nnum_destinations 1\\nnum_change_outputs 1\\ndestination_addresses tb1q0gzpnp4yhr20p7tqdrqmm7872w0unmawzka9zu\\nis_high_fee False' else 'MISMATCH')\n" },
	{ "10in: sign",
	  "print('signed', p10.sign_with(root10))\n" },
	{ "10in: compare",
	  "print('SIGN10', 'MATCH' if p10.to_string() == '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' else 'MISMATCH')\ngc.collect()\nprint('heap used', gc.mem_alloc() // 1024, 'KB')\n" },
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
