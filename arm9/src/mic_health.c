/*
 * NDS-Signer - health tests on microphone noise (NIST SP 800-90B §4.4)
 * SPDX-License-Identifier: MIT
 *
 * Both tests assume at least H = 2 bits of min-entropy in each 4-bit
 * sample, with a false-alarm rate of alpha = 2^-20 per test (§4.4.1-2):
 *   Repetition Count: cutoff 1 + ceil(20 / H) = 11 identical in a row;
 *   Adaptive Proportion: in each window of 512 samples, the first sample's
 *   value may appear at most 176 times (cutoff 177 = 1 + CRITBINOM(512,
 *   2^-H, 1 - alpha)).
 * They catch a source that has broken down (a stuck or two-valued ADC, a DC
 * offset with a little jitter), not one that is merely predictable: mains
 * hum's low bits look random to them. What the source really yields is
 * measured separately (docs/entropy.md). Plain C, no libnds, so the host
 * tests build it too (tests/host/test_mic_health.c).
 */
#include "mic_health.h"

#define RCT_CUTOFF 11
#define APT_WINDOW 512
#define APT_CUTOFF 177

int micHealth(const int16_t *s, size_t n)
{
	/* the lowest bit that varies across the buffer */
	unsigned diff = 0;
	for (size_t i = 1; i < n; i++)
		diff |= (uint16_t)s[i] ^ (uint16_t)s[0];
	if (!diff)
		return MIC_HEALTH_FLAT;
	unsigned shift = 0;
	while (!(diff & (1u << shift)))
		shift++;

	unsigned prev = 16, run = 0, first = 0, count = 0;
	for (size_t i = 0; i < n; i++) {
		unsigned v = ((uint16_t)s[i] >> shift) & 15;
		run = v == prev ? run + 1 : 1;
		prev = v;
		if (run >= RCT_CUTOFF)
			return MIC_HEALTH_RCT;
		if (i % APT_WINDOW == 0) {
			first = v;
			count = 1;
		} else if (v == first && ++count >= APT_CUTOFF) {
			return MIC_HEALTH_APT;
		}
	}
	return MIC_HEALTH_OK;
}
