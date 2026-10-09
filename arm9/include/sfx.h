/*
 * NDS-Signer - short UI feedback sounds (optional, see the "Sound effects"
 * setting in mpy/overlay/seedsigner/gui/__init__.py)
 * SPDX-License-Identifier: MIT
 */
#ifndef NDS_SIGNER_SFX_H
#define NDS_SIGNER_SFX_H

typedef enum {
	SFX_CLICK,      /* a button */
	SFX_KEY,        /* a keyboard key, list navigation */
	SFX_BACK,
	SFX_SUCCESS,
	SFX_WARNING,
	SFX_ERROR,
	SFX_SCAN,       /* a QR code (or animated part) read */
	SFX_COUNT
} Sfx;

/* Powers up the sound hardware (once; also used by the tones player). */
void sfxInit(void);

/* Plays a sound; the first call powers up the sound hardware. */
void sfxPlay(int sfx);

#endif /* NDS_SIGNER_SFX_H */
