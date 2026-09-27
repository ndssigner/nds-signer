/*
 * NDS-Signer - small 2D renderer for the graphical UI (both screens)
 * SPDX-License-Identifier: MIT
 *
 * Each screen has a 256x192 RGB555 back buffer in main RAM; drawing goes
 * there and gfxPresent() copies it to the screen's bitmap background. Text
 * uses SeedSigner's fonts, rasterized with 4-bit anti-aliasing at build
 * time (tools/ttf_to_ndsfont.py, build/generated/gfx_fonts.c).
 * Colors are 0xRRGGBB.
 */
#ifndef NDS_SIGNER_GFX_H
#define NDS_SIGNER_GFX_H

#include <nds/ndstypes.h>
#include <stddef.h>

#include "gfx_fonts.h"

#define GFX_W 256
#define GFX_H 192
#define GFX_TOP 0
#define GFX_BOTTOM 1

void gfxClear(int screen, u32 rgb);
/* Filled rectangle; radius > 0 rounds its corners (anti-aliased). */
void gfxRect(int screen, int x, int y, int w, int h, u32 rgb, int radius);
/* Rectangle outline `thickness` pixels wide, corners rounded like gfxRect. */
void gfxFrame(int screen, int x, int y, int w, int h, u32 rgb, int radius, int thickness);
/* UTF-8 text with its line box's top-left corner at (x, y), clipped to
 * maxWidth pixels if > 0. Returns the width drawn. */
int gfxText(int screen, int x, int y, const char *utf8, size_t len, int font, u32 rgb, int maxWidth);
int gfxTextWidth(const char *utf8, size_t len, int font);
void gfxFontMetrics(int font, int *ascent, int *lineHeight);
/* Copies the back buffer to the screen. */
void gfxPresent(int screen);

#endif /* NDS_SIGNER_GFX_H */
