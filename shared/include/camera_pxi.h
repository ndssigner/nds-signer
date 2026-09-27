/*
 * NDS-Signer - ARM9 <-> ARM7 camera protocol (PXI)
 * SPDX-License-Identifier: MIT
 *
 * The DSi camera sensors (Aptina MT9V113) are configured over I2C, which is
 * only reachable from the ARM7. The ARM9 sends one command word per request on
 * PXI_CAMERA and blocks until the ARM7 replies.
 *
 * Adapted from Epicpkmn11/dsi-camera (public domain / Unlicense).
 */
#ifndef NDS_SIGNER_CAMERA_PXI_H
#define NDS_SIGNER_CAMERA_PXI_H

#ifdef __cplusplus
extern "C" {
#endif

#define PXI_CAMERA PxiChannel_User0

/* I2C bus addresses of the two sensors */
#define I2C_CAM_INNER 0x7A
#define I2C_CAM_OUTER 0x78

/* Value of the Aptina CHIP_VERSION register (0x0000) for the MT9V113 */
#define APTINA_CHIP_ID 0x2280

typedef enum {
	CAM_CMD_INIT,
	CAM_CMD_INNER_ACTIVATE,
	CAM_CMD_INNER_DEACTIVATE,
	CAM_CMD_OUTER_ACTIVATE,
	CAM_CMD_OUTER_DEACTIVATE,
	CAM_CMD_MODE_PREVIEW,
	CAM_CMD_MODE_CAPTURE,
	CAM_CMD_SET_EXPOSURE,  /* active sensor, see CAM_EXPOSURE() */
} CameraPxiCommand;

/* CAM_CMD_SET_EXPOSURE with its arguments in one PXI word (26 bits):
 * auto-exposure target luma (AE_BASETARGET) and metering window
 * (0 = whole frame, 1 = central half, where the QR code is aimed). */
#define CAM_EXPOSURE(target, center) \
	(CAM_CMD_SET_EXPOSURE | ((u32)(target) & 0xFF) << 8 | ((center) ? 1U : 0U) << 16)
#define CAM_CMD(word)             ((word) & 0xFF)
#define CAM_EXPOSURE_TARGET(word) (((word) >> 8) & 0xFF)
#define CAM_EXPOSURE_CENTER(word) (((word) >> 16) & 1)

/* Every command is answered with CAM_REPLY_OK, CAM_REPLY_ERROR, or (for
 * CAM_CMD_INIT) the chip id read back from the sensor. */
#define CAM_REPLY_OK    0x0001
#define CAM_REPLY_ERROR 0xDEAD

typedef enum {
	CAPTURE_MODE_PREVIEW = 1, /* 256x192, fits one screen */
	CAPTURE_MODE_CAPTURE = 2, /* 640x480 */
} CaptureMode;

#ifdef __cplusplus
}
#endif

#endif /* NDS_SIGNER_CAMERA_PXI_H */
