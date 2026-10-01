/*
 * NDS-Signer - minimal touch UI toolkit for the text consoles
 * SPDX-License-Identifier: MIT
 */
#ifndef NDS_SIGNER_UI_H
#define NDS_SIGNER_UI_H

#include <nds.h>

/* Text consoles are 32x24 cells of 8x8 pixels */
#define UI_COLS 32
#define UI_ROWS 24

typedef struct {
	int col, row, width; /* in text cells; buttons are 3 rows high */
	const char *label;
} UiButton;

extern PrintConsole g_uiTop;
extern PrintConsole g_uiBottom;

/* Both screens: a 16-bit bitmap (graphical UI, camera, QR codes) with a
 * text console layer on top of it. */
void uiInit(void);
u16 *uiTopBitmap(void);
u16 *uiBottomBitmap(void);

void uiClearTop(void);    /* clears both the bitmap and the text layer */
void uiClearBottom(void);
void uiClearTopText(void); /* the text layer only: the bitmap shown stays */
void uiClearBottomText(void);

void uiDrawButtons(const UiButton *buttons, int count);

/* Tap handling: a button fires when the stylus is lifted over the same button
 * it went down on. Call once per frame after scanKeys(); returns the index of
 * the tapped button or -1. */
int uiPollButtons(const UiButton *buttons, int count);

/* Milliseconds since uiInit(), from the VBlank interrupt (~17 ms steps). */
u32 uiMillis(void);

/* Prints `text` centred on `row` of the currently selected console. */
void uiPrintCentered(int row, const char *text);

/* Word-wraps `text` into the currently selected console starting at `row`,
 * centring each line. Returns the row after the last line printed. */
int uiPrintWrapped(int row, const char *text);

/* Port of SeedSigner's WarningScreen (gui/screens/screen.py): title and
 * status headline + body text on the top screen, one button on the bottom.
 * `detail` (may be NULL) is an extra line below the text, used for dev info.
 * Returns when the button is tapped or A / B is pressed. */
void uiWarningScreen(const char *title, const char *statusHeadline,
                     const char *text, const char *detail, const char *buttonLabel);

#endif /* NDS_SIGNER_UI_H */
