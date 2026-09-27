/*
 * NDS-Signer - DSi camera driver (ARM9 side)
 * SPDX-License-Identifier: MIT
 *
 * The ARM9 owns the camera data interface (CAM_* registers + NDMA) while the
 * ARM7 configures the sensors over I2C (see shared/include/camera_pxi.h).
 * Adapted from Epicpkmn11/dsi-camera (public domain / Unlicense).
 */
#ifndef NDS_SIGNER_CAMERA_H
#define NDS_SIGNER_CAMERA_H

#include <nds/ndstypes.h>

#include "camera_pxi.h"

#define CAMERA_PREVIEW_WIDTH  256
#define CAMERA_PREVIEW_HEIGHT 192

typedef enum {
	CAM_NONE,
	CAM_INNER, /* facing the user */
	CAM_OUTER, /* facing away: the one used to scan QR codes */
} Camera;

/* Powers up the camera interface and both sensors. Returns false when not
 * running on a DSi or the sensors do not answer (e.g. unsupported emulator). */
bool cameraInit(void);

/* Activates a camera; the previously active one is deactivated first. */
bool cameraActivate(Camera cam);

/* Deactivates the active camera (turns the outer camera LED off). */
bool cameraDeactivate(void);

Camera cameraActive(void);

/* Auto-exposure of the active camera: target luma (AE_BASETARGET) and
 * metering on the whole frame or its central half. */
bool cameraSetExposure(u8 target, bool center);

/* Starts one frame transfer into dst using NDMA channel 1.
 * PREVIEW: 256x192 RGB555 (can target VRAM directly).
 * CAPTURE: 640x480 raw YUV422. */
void cameraTransferStart(u16 *dst, CaptureMode mode);
void cameraTransferStop(void);
bool cameraTransferActive(void);

#endif /* NDS_SIGNER_CAMERA_H */
