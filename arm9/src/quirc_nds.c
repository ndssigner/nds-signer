/*
 * NDS-Signer - DS-specific helpers for quirc (lib/quirc)
 * SPDX-License-Identifier: MIT
 *
 * QUIRC_DIV_ROUND for the fixed-point grid mapping (QUIRC_FIXED_POINT_GRID):
 * the ARM946E-S has no divide instruction and libgcc's 64-bit division is
 * about as slow as the soft-float math it replaces, so the DS's hardware
 * divider (64/64 bits, ~34 cycles) is used instead.
 */
#include <nds.h>
#include <stdint.h>

int quircNdsDivRound(int64_t n, int64_t d);

/* round(n / d) for d > 0, halves up (same as quirc's portable version) */
int quircNdsDivRound(int64_t n, int64_t d)
{
	int64_t t = 2 * n + d, d2 = 2 * d;
	bool negative = t < 0;
	int64_t q;

	if (negative)
		t = -t + d2 - 1;  /* floor for negative t: -ceil(-t / d2) */

	/* nothing else uses the divider, but an IRQ handler could: keep it ours */
	u32 ime = REG_IME;
	REG_IME = 0;
	REG_DIVCNT = DIV_64_64;
	REG_DIV_NUMER = t;
	REG_DIV_DENOM = d2;
	while (REG_DIVCNT & DIV_BUSY)
		;
	q = REG_DIV_RESULT;
	REG_IME = ime;

	return (int)(negative ? -q : q);
}
