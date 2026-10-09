/*
 * NDS-Signer - listening to ur-tones (github.com/ndssigner/ur-tones)
 * SPDX-License-Identifier: MIT
 */
#ifndef NDS_SIGNER_TONES_AUDIO_H
#define NDS_SIGNER_TONES_AUDIO_H

#include <stdbool.h>
#include <stddef.h>

/* Starts / stops listening: the microphone records continuously and the
 * ur-tones receiver (third_party/ur-tones/c) hears what it records. gain:
 * 0-3 = the amplifier's 20, 40, 80, 160 presets. Stopping clears every
 * buffer (a seed may have been heard). */
bool tonesListenStart(int gain);
void tonesListenStop(void);

/* Feeds what was recorded since the last call to the receiver (call it every
 * frame). `group` gets the next group of tones heard, if any (returns its
 * length, else 0); `live` the keys heard meanwhile; `level` the last tone
 * level in 0.1 dB; `buffers` recorded so far, `dropped` lost because nobody
 * called this in time. */
int tonesListenPoll(char *group, size_t cap, char *live, size_t livecap, int *level, unsigned *buffers,
                    unsigned *dropped);

/* Developer builds only (make DEVBUILD=1; elsewhere returns false): the
 * receiver hears these frames (newline-separated tones), synthesised in a
 * loop at the real pace, instead of the microphone: the whole path, from
 * tones to DecodeQR, timed on the console or the emulator. */
bool tonesLoopback(const char *groups);

/* Plays a frame's tones (or keypad tones) through the speaker, or the
 * headphones when plugged in: a pause, each tone and its gap, a final pause
 * (SPEC §1.1). Stops listening first. Call tonesPlayPoll() every frame: it
 * keeps the sound fed, returns 1 while playing and 0 at the end, with the
 * index of the tone being played out of `count`. Stopping (or the end)
 * clears the buffers. */
bool tonesPlayStart(const char *tones, unsigned tone_ms, unsigned gap_ms, unsigned pause_ms);
int tonesPlayPoll(unsigned *index, unsigned *count);
void tonesPlayStop(void);

#endif /* NDS_SIGNER_TONES_AUDIO_H */
