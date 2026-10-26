/*
 * NDS-Signer - libFuzzer harness: the whole camera path on an arbitrary small
 * grayscale image, built as the ROM builds quirc (QUIRC_FIXED_POINT_GRID,
 * QUIRC_LAZY_JIGGLE): quirc_end, then every grid extracted, decoded (a
 * mirrored retry on an ECC error) and refined as qr_scanner.c's decodeGrid()
 * does, then the ROM's QR type detection.
 * SPDX-License-Identifier: MIT
 *
 * Input: width and height bytes (8-263 pixels each), then the pixels
 * (missing ones white).
 */
#include <stdint.h>
#include <string.h>

#include "qr_type.h"
#include "quirc.h"

static struct quirc *s_q;

int LLVMFuzzerTestOneInput(const uint8_t *in, size_t len)
{
	if (len < 2)
		return 0;
	int w = 8 + in[0], h = 8 + in[1];
	if (!s_q)
		s_q = quirc_new();
	if (!s_q || quirc_resize(s_q, w, h) < 0)
		return 0;
	uint8_t *img = quirc_begin(s_q, NULL, NULL);
	size_t px = (size_t)w * h, n = len - 2 < px ? len - 2 : px;
	memcpy(img, in + 2, n);
	memset(img + n, 255, px - n);
	quirc_end(s_q);

	static struct quirc_code code;
	static struct quirc_data data;
	for (int i = 0; i < quirc_count(s_q); i++) {
		for (int tries = 0; tries < 2; tries++) {
			quirc_extract(s_q, i, &code);
			quirc_decode_error_t err = quirc_decode(&code, &data);
			if (err == QUIRC_ERROR_DATA_ECC) {
				quirc_flip(&code);
				err = quirc_decode(&code, &data);
			}
			if (err == QUIRC_SUCCESS) {
				(void)qrDetectSegmentType(data.payload, (size_t)data.payload_len);
				break;
			}
			if (!quirc_refine(s_q, i))
				break;
		}
	}
	return 0;
}
