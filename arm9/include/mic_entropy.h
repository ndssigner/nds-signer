/*
 * NDS-Signer - microphone noise as entropy for a new seed
 * SPDX-License-Identifier: MIT
 */
#ifndef NDS_SIGNER_MIC_ENTROPY_H
#define NDS_SIGNER_MIC_ENTROPY_H

#include <nds.h>

#define MIC_ENTROPY_SAMPLES 4096  /* 16-bit samples per buffer: 1/4 s at 16 kHz */

/* calico's micInit(), once (shared with tones_audio.c) */
void micEnsureInit(void);

/* Starts / stops recording (the microphone is off otherwise). Stopping
 * clears the buffers. */
bool micEntropyStart(void);
void micEntropyStop(void);

/* The buffer recorded last, once: copies it to `dst` (up to `len` bytes) and
 * returns its size in bytes, or 0 if no new buffer; `peak` = the largest
 * sample magnitude (0 for a flat buffer: every sample identical), `health`
 * = its health tests' result (MIC_HEALTH_*, mic_health.h). */
size_t micEntropyTake(u8 *dst, size_t len, int *peak, int *health);

/* Buffers recorded since start but never taken (each new one replaces one
 * not yet taken): the caller polled more slowly than every 1/4 s. */
unsigned micEntropyDropped(void);

#endif /* NDS_SIGNER_MIC_ENTROPY_H */
