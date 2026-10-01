/*
 * NDS-Signer - wipe on lid close / power button
 * SPDX-License-Identifier: MIT
 */
#ifndef NDS_SIGNER_WIPE_H
#define NDS_SIGNER_WIPE_H

/* Clears all memory that may hold secrets (the Python heap with seeds and
 * PSBTs, camera and QR buffers, both screens) and turns the console off.
 * Called when the lid is closed or the power button is pressed. */
void wipeAndPowerOff(void) __attribute__((noreturn));

#endif /* NDS_SIGNER_WIPE_H */
