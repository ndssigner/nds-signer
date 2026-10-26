/*
 * NDS-Signer - libFuzzer harness: the ROM's QR type detection
 * (arm9/src/qr_type.c) on arbitrary payloads.
 * SPDX-License-Identifier: MIT
 */
#include <stdint.h>

#include "qr_type.h"

int LLVMFuzzerTestOneInput(const uint8_t *in, size_t len)
{
	(void)qrDetectSegmentType(in, len);
	return 0;
}
