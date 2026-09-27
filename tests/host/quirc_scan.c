/*
 * NDS-Signer - host tool: runs quirc (lib/quirc, as built for the ROM) on
 * 8-bit PGM images and prints one line per image: name, QR codes decoded
 * and their payloads in hex. Used by `make -C tests/host quirc` to compare
 * unmodified quirc with the ROM's build (QUIRC_FIXED_POINT_GRID and
 * QUIRC_LAZY_JIGGLE, with the same decode/refine/retry loop as the ROM).
 * SPDX-License-Identifier: MIT
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "quirc.h"

static unsigned char *read_pgm(const char *path, int *w, int *h)
{
	FILE *f = fopen(path, "rb");
	int maxval;
	unsigned char *img = NULL;

	if (!f)
		return NULL;
	if (fscanf(f, "P5 %d %d %d", w, h, &maxval) == 3 && maxval == 255 && fgetc(f) != EOF) {
		img = malloc((size_t)*w * *h);
		if (img && fread(img, 1, (size_t)*w * *h, f) != (size_t)*w * *h) {
			free(img);
			img = NULL;
		}
	}
	fclose(f);
	return img;
}

static int n_refined;

int main(int argc, char **argv)
{
	struct quirc *q = quirc_new();

	for (int a = 1; a < argc; a++) {
		int w, h;
		unsigned char *img = read_pgm(argv[a], &w, &h);
		const char *name = strrchr(argv[a], '/') ? strrchr(argv[a], '/') + 1 : argv[a];

		if (!img || quirc_resize(q, w, h) < 0) {
			printf("%s ERROR\n", name);
			free(img);
			continue;
		}
		memcpy(quirc_begin(q, NULL, NULL), img, (size_t)w * h);
		free(img);
		quirc_end(q);

		int count = quirc_count(q);
		printf("%s", name);
		for (int i = 0; i < count; i++) {
			struct quirc_code code;
			struct quirc_data data;

			quirc_decode_error_t err;
			int refined = 0;
retry:
			quirc_extract(q, i, &code);
			err = quirc_decode(&code, &data);
			if (err == QUIRC_ERROR_DATA_ECC) {
				quirc_flip(&code);
				err = quirc_decode(&code, &data);
			}
#ifdef QUIRC_LAZY_JIGGLE
			if (err && quirc_refine(q, i)) {
				refined = 1;
				goto retry;
			}
#endif
			n_refined += refined;
			if (err) {
				printf(" fail:%d", err);
				continue;
			}
			printf(" ok:");
			for (int j = 0; j < data.payload_len; j++)
				printf("%02x", data.payload[j]);
		}
		printf("\n");
	}
	quirc_destroy(q);
	fprintf(stderr, "grids refined after a failed quick read: %d\n", n_refined);
	return 0;
}
