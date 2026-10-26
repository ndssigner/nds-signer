/*
 * NDS-Signer - wipe on lid close / power button
 * SPDX-License-Identifier: MIT
 */
#ifndef NDS_SIGNER_WIPE_H
#define NDS_SIGNER_WIPE_H

#include <stddef.h>

/* Clears all memory that may hold secrets (the Python heap with seeds and
 * PSBTs, camera, microphone, tones and QR buffers, the app thread's stack,
 * both screens) and turns the console off. Called on the app thread when the
 * lid is closed or the power button is pressed. */
void wipeAndPowerOff(void) __attribute__((noreturn));

/* Overwrites len bytes at p with zeros (any length and alignment); the
 * stores are never optimised away. */
void secureZero(void *p, size_t len);

#endif /* NDS_SIGNER_WIPE_H */
