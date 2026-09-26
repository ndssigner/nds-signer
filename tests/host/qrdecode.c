/*
 * NDS-Signer - host tool: decodes QR codes in a binary PGM (P5) image with the
 * same quirc the ROM uses. Prints each payload on its own line.
 * Used to verify screenshots of the emulator: tools/png_to_pgm.py | qrdecode
 * SPDX-License-Identifier: MIT
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "quirc.h"

int main(void)
{
	int w, h, maxval;
	if (scanf("P5 %d %d %d", &w, &h, &maxval) != 3 || maxval != 255) {
		fprintf(stderr, "expected a binary 8-bit PGM on stdin\n");
		return 2;
	}
	getchar(); /* single whitespace after the header */

	struct quirc *q = quirc_new();
	if (!q || quirc_resize(q, w, h) < 0)
		return 2;
	uint8_t *img = quirc_begin(q, NULL, NULL);
	if (fread(img, 1, (size_t)w * h, stdin) != (size_t)w * h)
		return 2;
	quirc_end(q);

	int found = 0;
	for (int i = 0; i < quirc_count(q); i++) {
		struct quirc_code code;
		struct quirc_data data;
		quirc_extract(q, i, &code);
		if (quirc_decode(&code, &data) == QUIRC_SUCCESS) {
			printf("%.*s\n", data.payload_len, (const char *)data.payload);
			found++;
		}
	}
	quirc_destroy(q);
	return found ? 0 : 1;
}
