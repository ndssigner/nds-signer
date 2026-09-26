/*
 * NDS-Signer - QR code scanner (DSi camera + quirc)
 * SPDX-License-Identifier: MIT
 *
 * Frames are captured at 640x480 in raw YUV422 so quirc gets the full-res
 * luma channel (dense PSBT QR codes need it); a 256x192 grayscale viewfinder
 * is rendered from the same frame. Two capture buffers are used so the camera
 * DMA fills one while the CPU decodes the other.
 */
#ifndef NDS_SIGNER_QR_SCANNER_H
#define NDS_SIGNER_QR_SCANNER_H

#include <nds/ndstypes.h>
#include <stddef.h>

typedef enum {
	SCAN_IDLE,     /* nothing new this call */
	SCAN_FRAME,    /* a frame was processed, no QR decoded */
	SCAN_DECODED,  /* a QR code was decoded: see scannerPayload() */
	SCAN_ERROR,    /* camera or memory failure */
} ScanStatus;

typedef struct {
	u32 frames;          /* frames processed since scannerStart() */
	u32 lastDecodeUs;    /* time spent in quirc for the last frame */
	int lastGrids;       /* QR candidates found in the last frame */
	int lastError;       /* last quirc decode error (0 = none) */
} ScanStats;

/* Allocates buffers (~1.5 MB) and powers up the camera. */
bool scannerInit(void);
void scannerShutdown(void);

/* Starts / stops streaming frames from the outer camera. */
bool scannerStart(void);
void scannerStop(void);

/* Call once per frame. Renders the viewfinder into `viewfinder`
 * (256x192 RGB555 bitmap, 256 pixels per line) when a frame is processed. */
ScanStatus scannerPoll(u16 *viewfinder);

/* Payload of the last SCAN_DECODED result (not NUL-terminated). */
const u8 *scannerPayload(size_t *len);

/* Wipes the last payload from RAM (it may be secret, e.g. a SeedQR). */
void scannerClearPayload(void);

const ScanStats *scannerStats(void);

#endif /* NDS_SIGNER_QR_SCANNER_H */
