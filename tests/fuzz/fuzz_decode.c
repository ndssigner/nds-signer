/*
 * NDS-Signer - libFuzzer harness: quirc_decode on an arbitrary grid of cells,
 * as arm9/src/qr_scanner.c's decodeGrid() calls it (a mirrored retry on an
 * ECC error), then the ROM's QR type detection on what decodes.
 * SPDX-License-Identifier: MIT
 *
 * Input: 1 byte picks the version (1-40), the rest are the cell bitmap.
 */
#include <stdint.h>
#include <string.h>

#include "qr_type.h"
#include "quirc.h"

int LLVMFuzzerTestOneInput(const uint8_t *in, size_t len)
{
	if (len < 1)
		return 0;
	static struct quirc_code code;
	static struct quirc_data data;
	memset(&code, 0, sizeof code);
	code.size = 17 + 4 * (1 + in[0] % 40);
	size_t n = len - 1 < sizeof code.cell_bitmap ? len - 1 : sizeof code.cell_bitmap;
	memcpy(code.cell_bitmap, in + 1, n);

	quirc_decode_error_t err = quirc_decode(&code, &data);
	if (err == QUIRC_ERROR_DATA_ECC) {
		quirc_flip(&code);
		err = quirc_decode(&code, &data);
	}
	if (err == QUIRC_SUCCESS)
		(void)qrDetectSegmentType(data.payload, (size_t)data.payload_len);
	return 0;
}
