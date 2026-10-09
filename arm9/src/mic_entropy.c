/*
 * NDS-Signer - microphone noise as entropy for a new seed
 * SPDX-License-Identifier: MIT
 *
 * Used only by the "New seed (scribble + mic)" screen: the microphone and
 * its amplifier are on only while that screen records, and every buffer is
 * cleared when it stops. Samples are never stored or sent anywhere: the
 * Python side hashes them (SHA-256 chain) into the seed's entropy.
 */
#include <nds.h>
#include <string.h>

#include "mic_entropy.h"

#define BUF_BYTES (MIC_ENTROPY_SAMPLES * sizeof(s16))

/* two buffers recorded alternately by DMA, plus the last complete one */
static s16 s_record[2][MIC_ENTROPY_SAMPLES] __attribute__((aligned(32)));
static s16 s_ready[MIC_ENTROPY_SAMPLES];
static volatile bool s_haveReady;
static bool s_running;

static void onBuffer(void *user, void *buf, size_t size)
{
	(void)user;
	DC_InvalidateRange(buf, size);
	memcpy(s_ready, buf, size < BUF_BYTES ? size : BUF_BYTES);
	s_haveReady = true;
}

/* micInit() once, for whichever user of the microphone comes first (this
 * file, or tones_audio.c) */
void micEnsureInit(void)
{
	static bool initialized;
	if (!initialized) {
		micInit();
		initialized = true;
	}
}

bool micEntropyStart(void)
{
	if (s_running)
		return true;
	micEnsureInit();
	if (!micSetDmaRate(MicRate_Div2))
		return false;
	micSetCallback(onBuffer, NULL);
	pmMicSetAmp(true, PmMicGain_80);
	s_haveReady = false;
	if (!micStart(s_record, BUF_BYTES, MicFmt_Pcm16, MicMode_DoubleBuffer)) {
		pmMicSetAmp(false, 0);
		return false;
	}
	s_running = true;
	return true;
}

void micEntropyStop(void)
{
	if (s_running) {
		micStop();
		pmMicSetAmp(false, 0);
		s_running = false;
	}
	volatile u8 *p = (volatile u8 *)s_record;
	for (size_t i = 0; i < sizeof(s_record); i++)
		p[i] = 0;
	p = (volatile u8 *)s_ready;
	for (size_t i = 0; i < sizeof(s_ready); i++)
		p[i] = 0;
	s_haveReady = false;
}

size_t micEntropyTake(u8 *dst, size_t len, int *peak)
{
	if (!s_haveReady)
		return 0;
	int irq = enterCriticalSection();
	size_t n = len < BUF_BYTES ? len : BUF_BYTES;
	memcpy(dst, s_ready, n);
	s_haveReady = false;
	leaveCriticalSection(irq);

	const s16 *s = (const s16 *)dst;
	int lo = 32767, hi = -32768, max = 0;
	for (size_t i = 0; i < n / 2; i++) {
		int v = s[i];
		if (v < lo) lo = v;
		if (v > hi) hi = v;
		if ((v < 0 ? -v : v) > max) max = v < 0 ? -v : v;
	}
	*peak = lo == hi ? 0 : (max ? max : 1);
	return n;
}
