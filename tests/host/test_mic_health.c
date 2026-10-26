/* Host test for arm9/src/mic_health.c: real-looking noise passes, the
 * failures the health tests are for do not. */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "mic_health.h"

#define N 4096

static uint64_t s_rng = 0x9e3779b97f4a7c15u;
static double uniform(void)
{
	s_rng ^= s_rng << 13; s_rng ^= s_rng >> 7; s_rng ^= s_rng << 17;
	return (s_rng >> 11) * (1.0 / 9007199254740992.0);
}
static double gauss(void)
{
	return sqrt(-2 * log(uniform() + 1e-300)) * cos(2 * M_PI * uniform());
}

static int s_fail;
static void check(const char *what, const int16_t *s, int want_ok)
{
	int h = micHealth(s, N);
	int ok = (h == MIC_HEALTH_OK) == want_ok;
	if (!ok)
		s_fail = 1;
	printf("%s %s: %d\n", ok ? "ok  " : "FAIL", what, h);
}

int main(void)
{
	static int16_t s[N];
	for (int i = 0; i < N; i++) s[i] = (int16_t)lround(300 * gauss());
	check("noise, sigma 300 LSB", s, 1);
	for (int i = 0; i < N; i++) s[i] = (int16_t)(lround(12 * gauss()) * 16);
	check("noise on a 12-bit ADC (low 4 bits always 0)", s, 1);
	for (int i = 0; i < N; i++) s[i] = (int16_t)(3000 * sin(2 * M_PI * 50 * i / 16364.0) + 300 * gauss());
	check("mains hum with noise", s, 1);
	for (int i = 0; i < N; i++) s[i] = 0;
	check("flat (dead microphone)", s, 0);
	for (int i = 0; i < N; i++) s[i] = (int16_t)(i & 1 ? 1200 : -800);
	check("stuck ADC alternating two values", s, 0);
	for (int i = 0; i < N; i++) s[i] = (int16_t)(1000 + lround(0.7 * gauss()));
	check("DC offset with +-1 LSB jitter", s, 0);
	for (int i = 0; i < N; i++) s[i] = (int16_t)(i < 2000 ? lround(300 * gauss()) : 512);
	check("noise, then stuck", s, 0);
	return s_fail;
}
