/*
 * NDS-Signer - plain C interface between the MicroPython `nds` module
 * (mpy/usermods/nds/modnds.c) and the ARM9 code. No libnds types here, so the
 * module can be preprocessed by the host compiler (MicroPython qstr scan).
 */
#ifndef NDS_SIGNER_NDS_BRIDGE_H
#define NDS_SIGNER_NDS_BRIDGE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define NDSB_COLS 32
#define NDSB_ROWS 24

/* libnds KEY_* bit values */
#define NDSB_KEY_A      (1u << 0)
#define NDSB_KEY_B      (1u << 1)
#define NDSB_KEY_SELECT (1u << 2)
#define NDSB_KEY_START  (1u << 3)
#define NDSB_KEY_RIGHT  (1u << 4)
#define NDSB_KEY_LEFT   (1u << 5)
#define NDSB_KEY_UP     (1u << 6)
#define NDSB_KEY_DOWN   (1u << 7)
#define NDSB_KEY_R      (1u << 8)
#define NDSB_KEY_L      (1u << 9)
#define NDSB_KEY_X      (1u << 10)
#define NDSB_KEY_Y      (1u << 11)
#define NDSB_KEY_TOUCH  (1u << 12)

enum { NDSB_TOP = 0, NDSB_BOTTOM = 1 };

/* Text: col < 0 centres; text is clipped to the row. */
void ndsbPrint(int screen, int row, int col, const char *text, size_t len);
void ndsbClear(int screen);

/* Input: ndsbFrame() waits for VBlank and samples keys. */
void ndsbFrame(void);
uint32_t ndsbKeysDown(void);
uint32_t ndsbKeysHeld(void);
bool ndsbTouch(int *x, int *y);
uint32_t ndsbTicksMs(void);

/* Camera / QR scanning (see qr_scanner.h) */
bool ndsbCameraInit(void);
bool ndsbCameraStart(void);
/* 1 = payload decoded (copied into buf, *len set), 0 = nothing yet,
 * -1 = camera error. buf must hold 8896 bytes (QUIRC_MAX_PAYLOAD). */
int ndsbCameraPoll(uint8_t *buf, size_t *len);
void ndsbCameraStop(void);
void ndsbCameraStats(uint32_t *frames, uint32_t *decodeMs);

#define NDSB_MAX_PAYLOAD 8896

#endif /* NDS_SIGNER_NDS_BRIDGE_H */
