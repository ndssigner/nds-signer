/*
 * NDS-Signer - health tests on microphone noise (NIST SP 800-90B §4.4)
 * SPDX-License-Identifier: MIT
 */
#ifndef NDS_SIGNER_MIC_HEALTH_H
#define NDS_SIGNER_MIC_HEALTH_H

#include <stddef.h>
#include <stdint.h>

enum { MIC_HEALTH_OK = 0, MIC_HEALTH_FLAT = 1, MIC_HEALTH_RCT = 2, MIC_HEALTH_APT = 3 };

/* The Repetition Count and Adaptive Proportion tests on one buffer's
 * samples, reduced to their 4 lowest bits that vary (so an ADC whose low
 * bits are always zero is judged on the bits it has). MIC_HEALTH_OK, or why
 * the buffer failed: identical samples, a value repeated too often in a
 * row, or one value too common in a window. */
int micHealth(const int16_t *s, size_t n);

#endif /* NDS_SIGNER_MIC_HEALTH_H */
