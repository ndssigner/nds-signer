/*
 * NDS-Signer - short UI feedback sounds (see sfx.h)
 * SPDX-License-Identifier: MIT
 *
 * Each sound is a few notes of a sine wave with a decaying envelope,
 * rendered once as 8-bit PCM in main RAM and played by calico's ARM7 sound
 * driver in one-shot mode: the hardware stops the channel at the end, so a
 * sound never keeps playing while the CPU is busy (e.g. signing).
 */
#include <nds.h>
#include <malloc.h>
#include <math.h>
#include <string.h>

#include "sfx.h"

#define RATE 16384
#define CHANNELS 8   /* 0-7: PCM channels used round-robin */
#define VOLUME 1600  /* of 2047 */

typedef struct {
	u16 freq, ms;
} Note;

/* up to 3 notes per sound, freq 0 = end */
static const Note s_notes[SFX_COUNT][3] = {
	[SFX_CLICK] = {{1760, 28}},
	[SFX_KEY] = {{1320, 18}},
	[SFX_BACK] = {{990, 30}, {660, 40}},
	[SFX_SUCCESS] = {{880, 70}, {1320, 110}},
	[SFX_WARNING] = {{523, 90}, {523, 120}},
	[SFX_ERROR] = {{330, 110}, {220, 180}},
	[SFX_SCAN] = {{2349, 16}},
};

static s8 *s_pcm[SFX_COUNT];
static u32 s_words[SFX_COUNT];
static bool s_ready;
static int s_channel;

static void render(int id)
{
	u32 samples = 0;
	for (int n = 0; n < 3 && s_notes[id][n].freq; n++)
		samples += (u32)s_notes[id][n].ms * RATE / 1000;
	samples = (samples + 3) & ~3u;  /* whole words */
	s8 *pcm = memalign(32, samples);
	if (!pcm)
		return;
	memset(pcm, 0, samples);
	u32 pos = 0;
	for (int n = 0; n < 3 && s_notes[id][n].freq; n++) {
		u32 len = (u32)s_notes[id][n].ms * RATE / 1000;
		float step = 2.0f * (float)M_PI * s_notes[id][n].freq / RATE;
		for (u32 i = 0; i < len && pos < samples; i++, pos++) {
			float t = (float)i / len;
			float attack = i < 32 ? i / 32.0f : 1.0f;      /* no click at the start */
			float env = attack * expf(-4.0f * t);
			pcm[pos] = (s8)(110.0f * env * sinf(step * i));
		}
	}
	DC_FlushRange(pcm, samples);
	s_pcm[id] = pcm;
	s_words[id] = samples / 4;
}

void sfxInit(void)
{
	if (s_ready)
		return;
	soundInit();
	soundPowerOn();
	soundSetMixerVolume(127);
	for (int i = 0; i < SFX_COUNT; i++)
		render(i);
	s_ready = true;
}

void sfxPlay(int sfx)
{
	if ((unsigned)sfx >= SFX_COUNT)
		return;
	if (!s_ready)
		sfxInit();
	if (!s_pcm[sfx])
		return;
	s_channel = (s_channel + 1) % CHANNELS;
	soundPreparePcm(s_channel | SOUND_START, VOLUME, 64, soundTimerFromHz(RATE),
	                SoundMode_OneShot, SoundFmt_Pcm8, s_pcm[sfx], 0, s_words[sfx]);
}
