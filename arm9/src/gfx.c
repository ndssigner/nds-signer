/*
 * NDS-Signer - small 2D renderer for the graphical UI (see gfx.h)
 * SPDX-License-Identifier: MIT
 */
#include <nds.h>
#include <string.h>

#include "gfx.h"
#include "ui.h"

static u16 s_back[2][GFX_W * GFX_H] __attribute__((aligned(32)));

static inline u16 rgb15(u32 rgb)
{
	return RGB15((rgb >> 19) & 31, (rgb >> 11) & 31, (rgb >> 3) & 31) | BIT(15);
}

/* dst blended towards src by alpha/15 */
static inline u16 blend(u16 dst, u16 src, int alpha)
{
	if (alpha >= 15)
		return src;
	if (alpha <= 0)
		return dst;
	int r = (dst & 31) + (((src & 31) - (dst & 31)) * alpha) / 15;
	int g = ((dst >> 5) & 31) + ((((src >> 5) & 31) - ((dst >> 5) & 31)) * alpha) / 15;
	int b = ((dst >> 10) & 31) + ((((src >> 10) & 31) - ((dst >> 10) & 31)) * alpha) / 15;
	return (u16)(r | g << 5 | b << 10 | BIT(15));
}

static inline void plot(u16 *buf, int x, int y, u16 c, int alpha)
{
	if ((unsigned)x < GFX_W && (unsigned)y < GFX_H)
		buf[y * GFX_W + x] = blend(buf[y * GFX_W + x], c, alpha);
}

void gfxClear(int screen, u32 rgb)
{
	u16 c = rgb15(rgb);
	u32 pair = c | (u32)c << 16;
	dmaFillWords(pair, s_back[screen & 1], sizeof(s_back[0]));
}

/* Coverage (0-15) of pixel (px, py) by a corner arc of radius r centred at
 * (cx, cy), from 4x4 samples at the sub-pixel centres ((i + 0.5) / 4),
 * in integers scaled by 8. */
static int cornerCoverage(int px, int py, int cx, int cy, int r)
{
	int n = 0, limit = 64 * r * r;
	for (int sy = 0; sy < 4; sy++)
		for (int sx = 0; sx < 4; sx++) {
			int dx = (px - cx) * 8 + sx * 2 + 1, dy = (py - cy) * 8 + sy * 2 + 1;
			if (dx * dx + dy * dy <= limit)
				n++;
		}
	return n * 15 / 16;
}

static int roundedAlpha(int px, int py, int x, int y, int w, int h, int r)
{
	int cx = -1, cy = -1;
	if (px < x + r)
		cx = x + r;
	else if (px >= x + w - r)
		cx = x + w - r;
	if (py < y + r)
		cy = y + r;
	else if (py >= y + h - r)
		cy = y + h - r;
	if (cx < 0 || cy < 0)
		return 15;
	return cornerCoverage(px, py, cx, cy, r);
}

void gfxRect(int screen, int x, int y, int w, int h, u32 rgb, int radius)
{
	u16 *buf = s_back[screen & 1];
	u16 c = rgb15(rgb);
	if (radius * 2 > w)
		radius = w / 2;
	if (radius * 2 > h)
		radius = h / 2;
	for (int py = y; py < y + h; py++) {
		if ((unsigned)py >= GFX_H)
			continue;
		bool edgeRow = py < y + radius || py >= y + h - radius;
		for (int px = x; px < x + w; px++) {
			if ((unsigned)px >= GFX_W)
				continue;
			int a = 15;
			if (radius > 0 && edgeRow && (px < x + radius || px >= x + w - radius))
				a = roundedAlpha(px, py, x, y, w, h, radius);
			plot(buf, px, py, c, a);
		}
	}
}

void gfxFrame(int screen, int x, int y, int w, int h, u32 rgb, int radius, int thickness)
{
	u16 *buf = s_back[screen & 1];
	u16 c = rgb15(rgb);
	int ri = radius - thickness < 0 ? 0 : radius - thickness;
	for (int py = y; py < y + h; py++) {
		for (int px = x; px < x + w; px++) {
			if ((unsigned)px >= GFX_W || (unsigned)py >= GFX_H)
				continue;
			int outer = radius > 0 ? roundedAlpha(px, py, x, y, w, h, radius) : 15;
			bool inside = px >= x + thickness && px < x + w - thickness &&
			              py >= y + thickness && py < y + h - thickness;
			int inner = inside ? (ri > 0 ? roundedAlpha(px, py, x + thickness, y + thickness,
			                                            w - 2 * thickness, h - 2 * thickness, ri) : 15)
			                   : 0;
			int a = outer - inner;
			if (a > 0)
				plot(buf, px, py, c, a);
		}
	}
}

/* Next code point of a UTF-8 string (invalid bytes read as U+FFFD). */
static u32 nextCodepoint(const char **p, const char *end)
{
	const u8 *s = (const u8 *)*p;
	u32 cp = s[0];
	int extra = cp >= 0xF0 ? 3 : cp >= 0xE0 ? 2 : cp >= 0xC0 ? 1 : 0;
	if (cp >= 0x80 && extra == 0) {
		*p += 1;
		return 0xFFFD;
	}
	if ((const char *)s + extra >= end) {  /* truncated sequence */
		*p = end;
		return 0xFFFD;
	}
	cp &= extra ? (0x3F >> extra) : 0x7F;
	for (int i = 1; i <= extra; i++)
		cp = (cp << 6) | (s[i] & 0x3F);
	*p += 1 + extra;
	return cp;
}

static const GfxGlyph *findGlyph(const GfxFont *f, u32 cp)
{
	int lo = 0, hi = f->count - 1;
	while (lo <= hi) {
		int mid = (lo + hi) / 2;
		u32 m = f->glyphs[mid].codepoint;
		if (m == cp)
			return &f->glyphs[mid];
		if (m < cp)
			lo = mid + 1;
		else
			hi = mid - 1;
	}
	return NULL;
}

static const GfxGlyph *glyphOrFallback(const GfxFont *f, u32 cp)
{
	const GfxGlyph *g = findGlyph(f, cp);
	return g ? g : findGlyph(f, '?');
}

int gfxTextWidth(const char *utf8, size_t len, int font)
{
	if ((unsigned)font >= GFX_FONT_COUNT)
		return 0;
	const GfxFont *f = &g_gfxFonts[font];
	const char *p = utf8, *end = utf8 + len;
	int w = 0;
	while (p < end) {
		const GfxGlyph *g = glyphOrFallback(f, nextCodepoint(&p, end));
		if (g)
			w += g->advance;
	}
	return w;
}

void gfxFontMetrics(int font, int *ascent, int *lineHeight)
{
	if ((unsigned)font >= GFX_FONT_COUNT) {
		*ascent = *lineHeight = 0;
		return;
	}
	*ascent = g_gfxFonts[font].ascent;
	*lineHeight = g_gfxFonts[font].lineHeight;
}

int gfxText(int screen, int x, int y, const char *utf8, size_t len, int font, u32 rgb, int maxWidth)
{
	if ((unsigned)font >= GFX_FONT_COUNT)
		return 0;
	u16 *buf = s_back[screen & 1];
	u16 c = rgb15(rgb);
	const GfxFont *f = &g_gfxFonts[font];
	const char *p = utf8, *end = utf8 + len;
	int pen = x, baseline = y + f->ascent;
	while (p < end) {
		const GfxGlyph *g = glyphOrFallback(f, nextCodepoint(&p, end));
		if (!g)
			continue;
		if (maxWidth > 0 && pen + g->advance > x + maxWidth)
			break;
		const u8 *px = f->pixels + g->offset;
		int stride = (g->w + 1) / 2;
		for (int gy = 0; gy < g->h; gy++) {
			int sy = baseline - g->top + gy;
			for (int gx = 0; gx < g->w; gx++) {
				u8 two = px[gy * stride + gx / 2];
				int a = gx & 1 ? two >> 4 : two & 15;
				if (a)
					plot(buf, pen + g->left + gx, sy, c, a);
			}
		}
		pen += g->advance;
	}
	return pen - x;
}

void gfxPresent(int screen)
{
	u16 *dst = screen == GFX_TOP ? uiTopBitmap() : uiBottomBitmap();
	DC_FlushRange(s_back[screen & 1], sizeof(s_back[0]));
	dmaCopyWords(3, s_back[screen & 1], dst, sizeof(s_back[0]));
}
