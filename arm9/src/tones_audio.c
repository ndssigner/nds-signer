/*
 * NDS-Signer - listening to and playing ur-tones (github.com/ndssigner/ur-tones)
 * SPDX-License-Identifier: MIT
 *
 * Listening: the microphone records continuously by DMA into two alternating buffers;
 * the interrupt only copies each full buffer into a queue, and the receiver
 * (third_party/ur-tones/c/ur_tones.c: integer Goertzel, no FPU needed) hears
 * them in the main loop, when Python polls. Experimental: the microphone and
 * its amplifier are on only while listening, and every buffer is cleared
 * when it stops, since what was heard may have been a seed.
 */
#include <nds.h>
#include <string.h>

#include "mic_entropy.h"
#include "sfx.h"
#include "tones_audio.h"
#include "ui.h"
#include "ur_tones.h"

#define BUF_SAMPLES 1024   /* 1/16 s at 16 kHz */
#define QUEUE 16           /* 1 s of slack */

static s16 s_dma[2][BUF_SAMPLES] __attribute__((aligned(32)));
static s16 s_queue[QUEUE][BUF_SAMPLES];
static volatile u32 s_head, s_tail, s_dropped;
static ut_listener s_listener;
static bool s_running;

#ifdef NDS_SIGNER_DEVBUILD
static char s_loop[8192];
static size_t s_loop_at, s_loop_len;
static ut_synth s_synth;
static char s_loop_group[700];
static bool s_loopback, s_synth_on;

bool tonesLoopback(const char *groups)
{
	size_t n = strlen(groups);
	if (n + 1 > sizeof s_loop)
		return false;
	memcpy(s_loop, groups, n + 1);
	s_loop_len = n;
	s_loop_at = 0;
	s_synth_on = false;
	s_loopback = n > 0;
	return true;
}

/* the next 1/60 s of the frames, as the microphone would have heard them */
static void loopbackFeed(void)
{
	int16_t pcm[SOUND_MIXER_FREQ_HZ / 2 / 60 + 1];
	size_t want = sizeof pcm / sizeof pcm[0], got = 0;
	while (got < want) {
		if (!s_synth_on) {
			size_t end = s_loop_at;
			while (end < s_loop_len && s_loop[end] != '\n') end++;
			size_t len = end - s_loop_at < sizeof s_loop_group - 1 ? end - s_loop_at : sizeof s_loop_group - 1;
			memcpy(s_loop_group, s_loop + s_loop_at, len);
			s_loop_group[len] = 0;
			s_loop_at = end + 1 >= s_loop_len ? 0 : end + 1;
			ut_synth_init(&s_synth, s_loop_group, SOUND_MIXER_FREQ_HZ / 2, 40, 20, 200);
			s_synth_on = true;
		}
		size_t n = ut_synth_read(&s_synth, pcm + got, want - got);
		got += n;
		if (!n) s_synth_on = false;
	}
	ut_listener_push(&s_listener, pcm, want);
}
#else
bool tonesLoopback(const char *groups)
{
	(void)groups;
	return false;
}
#endif

static void onBuffer(void *user, void *buf, size_t size)
{
	(void)user;
	DC_InvalidateRange(buf, size);
	if (s_head - s_tail >= QUEUE) {
		s_dropped++;
		return;
	}
	memcpy(s_queue[s_head % QUEUE], buf, size < sizeof s_queue[0] ? size : sizeof s_queue[0]);
	s_head++;
}

static void wipe(void)
{
	volatile u8 *p = (volatile u8 *)s_dma;
	for (size_t i = 0; i < sizeof s_dma; i++) p[i] = 0;
	p = (volatile u8 *)s_queue;
	for (size_t i = 0; i < sizeof s_queue; i++) p[i] = 0;
	p = (volatile u8 *)&s_listener;
	for (size_t i = 0; i < sizeof s_listener; i++) p[i] = 0;
}

bool tonesListenStart(int gain)
{
	static const unsigned GAINS[4] = {PmMicGain_20, PmMicGain_40, PmMicGain_80, PmMicGain_160};
	if (s_running)
		return true;
	tonesPlayStop();
	micEntropyStop();                     /* one user of the microphone at a time */
	micEnsureInit();
	if (!micSetDmaRate(MicRate_Div2))     /* SOUND_MIXER_FREQ_HZ / 2: about 16364 Hz */
		return false;
	micSetCallback(onBuffer, NULL);
	pmMicSetAmp(true, GAINS[gain < 0 ? 0 : gain > 3 ? 3 : gain]);
	s_head = s_tail = s_dropped = 0;
	ut_listener_init(&s_listener, SOUND_MIXER_FREQ_HZ / 2);
	if (!micStart(s_dma, sizeof s_dma[0], MicFmt_Pcm16, MicMode_DoubleBuffer)) {
		pmMicSetAmp(false, 0);
		return false;
	}
	s_running = true;
	return true;
}

void tonesListenStop(void)
{
	if (s_running) {
		micStop();
		pmMicSetAmp(false, 0);
		s_running = false;
	}
	wipe();
	s_head = s_tail = 0;
#ifdef NDS_SIGNER_DEVBUILD
	s_loopback = false;
#endif
}

int tonesListenPoll(char *group, size_t cap, char *live, size_t livecap, int *level, unsigned *buffers,
                    unsigned *dropped)
{
	if (s_running) {
#ifdef NDS_SIGNER_DEVBUILD
		if (s_loopback) {
			s_tail = s_head;      /* the microphone's buffers are ignored */
			loopbackFeed();
		}
#endif
		while (s_tail != s_head) {
			ut_listener_push(&s_listener, s_queue[s_tail % QUEUE], BUF_SAMPLES);
			s_tail++;
		}
	}
	*level = s_listener.level;
	*dropped = s_dropped;
	*buffers = s_tail;
	ut_listener_live(&s_listener, live, livecap);
	int n = ut_listener_group(&s_listener, group, cap);
	return n > 0 ? n : 0;
}

/* ---- playing ------------------------------------------------------------
 * The synthesiser (ut_synth) writes into a ring buffer that one sound channel
 * plays in a loop; the main loop keeps it filled about a second ahead. The
 * sound driver cannot say where it is playing, but its timer and calico's
 * tick counter run from the same clock, so the time since the start says
 * exactly which sample is playing. */

#define PLAY_CH 15
#define PLAY_RATE 16384
#define RING 16384          /* samples: 1 s of slack */
#define GUARD 2048          /* never write this close to what is playing: 1/8 s */

static s16 s_ring[RING] __attribute__((aligned(32)));
static char s_play[UT_MAX_FRAME + 1];
static ut_synth s_synth;
static u32 s_f0;
static u64 s_written, s_end;
static unsigned s_timer;
static bool s_playing, s_synth_done;

#define FRAME_CYCLES 560190u   /* 263 lines x 355 dots x 6 cycles */

static u64 played(void)
{
	return (u64)(uiFrames() - s_f0) * FRAME_CYCLES / (2u * s_timer);
}

static void fill(u64 upto)
{
	while (s_written < upto) {
		size_t at = (size_t)(s_written % RING);
		size_t n = RING - at;
		if (n > upto - s_written)
			n = (size_t)(upto - s_written);
		size_t got = s_synth_done ? 0 : ut_synth_read(&s_synth, s_ring + at, n);
		if (got < n) {
			if (!s_synth_done) {
				s_synth_done = true;
				s_end = s_written + got;
			}
			memset(s_ring + at + got, 0, (n - got) * sizeof s_ring[0]);
		}
		DC_FlushRange(s_ring + at, n * sizeof s_ring[0]);
		s_written += n;
	}
}

static void wipePlay(void)
{
	volatile u8 *p = (volatile u8 *)s_ring;
	for (size_t i = 0; i < sizeof s_ring; i++) p[i] = 0;
	DC_FlushRange(s_ring, sizeof s_ring);
	p = (volatile u8 *)s_play;
	for (size_t i = 0; i < sizeof s_play; i++) p[i] = 0;
	p = (volatile u8 *)&s_synth;
	for (size_t i = 0; i < sizeof s_synth; i++) p[i] = 0;
}

bool tonesPlayStart(const char *tones, unsigned tone_ms, unsigned gap_ms, unsigned pause_ms)
{
	size_t n = strlen(tones);
	if (!n || n > UT_MAX_FRAME)
		return false;
	tonesPlayStop();
	tonesListenStop();                    /* never both: the speaker would feed the microphone */
	sfxInit();
	memcpy(s_play, tones, n + 1);
	s_timer = soundTimerFromHz(PLAY_RATE);
	/* the real rate, so that the tones are exactly on their frequencies */
	ut_synth_init(&s_synth, s_play, SOUND_CLOCK / s_timer, tone_ms, gap_ms, pause_ms);
	s_written = s_end = 0;
	s_synth_done = false;
	fill(RING - GUARD);
	soundPreparePcm(PLAY_CH | SOUND_START, 2047, 64, s_timer, SoundMode_Repeat, SoundFmt_Pcm16,
	                s_ring, 0, sizeof s_ring / 4);
	s_f0 = uiFrames();
	s_playing = true;
	return true;
}

int tonesPlayPoll(unsigned *index, unsigned *count)
{
	*count = (unsigned)s_synth.count;
	*index = 0;
	if (!s_playing)
		return 0;
	u64 p = played();
	if (s_synth_done && p >= s_end) {
		tonesPlayStop();
		*index = *count;
		return 0;
	}
	fill(p + RING - GUARD);
	u64 step = s_synth.tone_n + s_synth.gap_n;
	if (p > s_synth.pause_n && step)
		*index = (unsigned)((p - s_synth.pause_n) / step);
	if (*index > *count)
		*index = *count;
	return 1;
}

void tonesPlayStop(void)
{
	if (s_playing) {
		soundStop(1u << PLAY_CH);
		s_playing = false;
	}
	unsigned count = (unsigned)s_synth.count;
	wipePlay();
	s_synth.count = count;              /* for the last poll's count only */
}
