/*
 * NDS-Signer - DSi camera driver (ARM9 side)
 * SPDX-License-Identifier: MIT
 *
 * Adapted from Epicpkmn11/dsi-camera (public domain / Unlicense).
 * Register reference: https://problemkaputt.de/gbatek.htm#dsicameras
 */
#include <nds.h>

#include "camera.h"

#define REG_CAM_MCNT (*(vu16 *)0x04004200) /* module control */
#define REG_CAM_CNT  (*(vu16 *)0x04004202) /* data interface control */
#define REG_CAM_DAT  (*(vu32 *)0x04004204) /* data FIFO */

#define CAM_CNT_LINES_MASK  0x0003     /* scanlines per DMA block, minus 1 */
#define CAM_CNT_FLUSH       BIT(5)
#define CAM_CNT_IRQ         BIT(11)
#define CAM_CNT_RGB555      BIT(13)    /* convert YUV422 to RGB555 */
#define CAM_CNT_ENABLE      BIT(15)

#define CAMERA_NDMA 1

static Camera s_activeCamera   = CAM_NONE;
static CaptureMode s_activeMode = CAPTURE_MODE_PREVIEW;

static bool command(CameraPxiCommand cmd)
{
	return pxiSendAndReceive(PXI_CAMERA, cmd) == CAM_REPLY_OK;
}

bool cameraInit(void)
{
	if (!isDSiMode())
		return false;

	/* Wait until the ARM7 camera server is listening */
	pxiWaitRemote(PXI_CAMERA);

	REG_SCFG_CLK |= SCFG_CLK_CAM_IFACE;
	REG_CAM_MCNT = 0;
	swiDelay(0x1E);
	REG_SCFG_CLK |= SCFG_CLK_CAM_EXT;
	swiDelay(0x1E);
	REG_CAM_MCNT = BIT(1) | BIT(5);
	swiDelay(0x2008);
	REG_SCFG_CLK &= ~SCFG_CLK_CAM_EXT;
	REG_CAM_CNT &= ~CAM_CNT_ENABLE; /* allow changing params */
	REG_CAM_CNT |= CAM_CNT_FLUSH;
	REG_CAM_CNT = (REG_CAM_CNT & ~0x0300) | 0x0200;
	REG_CAM_CNT |= BIT(10);
	REG_CAM_CNT |= CAM_CNT_IRQ;
	REG_SCFG_CLK |= SCFG_CLK_CAM_EXT;
	swiDelay(0x14);

	/* Sensor setup ("aptina_code_list_init") runs on the ARM7 over I2C */
	u32 chipId = pxiSendAndReceive(PXI_CAMERA, CAM_CMD_INIT);

	REG_SCFG_CLK &= ~SCFG_CLK_CAM_EXT;
	REG_SCFG_CLK |= SCFG_CLK_CAM_EXT;
	swiDelay(0x14);

	return chipId == APTINA_CHIP_ID;
}

bool cameraActivate(Camera cam)
{
	if (s_activeCamera != CAM_NONE)
		cameraDeactivate();

	if (!command(cam == CAM_INNER ? CAM_CMD_INNER_ACTIVATE : CAM_CMD_OUTER_ACTIVATE))
		return false;

	s_activeCamera = cam;
	/* the mode is per sensor: send it to the one just activated (the inner
	 * camera would otherwise stream small preview frames until the scanner's
	 * watchdog sends it) */
	cameraForgetMode();
	return true;
}

bool cameraDeactivate(void)
{
	if (s_activeCamera == CAM_NONE)
		return true;

	cameraTransferStop();
	bool ok = command(s_activeCamera == CAM_INNER ? CAM_CMD_INNER_DEACTIVATE
	                                              : CAM_CMD_OUTER_DEACTIVATE);
	s_activeCamera = CAM_NONE;
	return ok;
}

Camera cameraActive(void)
{
	return s_activeCamera;
}

void cameraForgetMode(void)
{
	s_activeMode = 0;
}

void cameraTransferStart(u16 *dst, CaptureMode mode)
{
	const bool preview = mode == CAPTURE_MODE_PREVIEW;

	if (mode != s_activeMode) {
		command(preview ? CAM_CMD_MODE_PREVIEW : CAM_CMD_MODE_CAPTURE);
		s_activeMode = mode;
	}

	if (REG_CAM_CNT & CAM_CNT_ENABLE)
		cameraTransferStop();

	if (preview) /* RGB555, 4 scanlines (4*256*2 bytes = 512 words) per block */
		REG_CAM_CNT |= CAM_CNT_RGB555 | 3;
	else         /* raw YUV422, 1 scanline (640*2 bytes = 320 words) per block */
		REG_CAM_CNT &= ~(CAM_CNT_RGB555 | CAM_CNT_LINES_MASK);
	REG_CAM_CNT |= CAM_CNT_FLUSH;
	REG_CAM_CNT |= CAM_CNT_ENABLE;

	REG_NDMAxSAD(CAMERA_NDMA)  = (u32)&REG_CAM_DAT;
	REG_NDMAxDAD(CAMERA_NDMA)  = (u32)dst;
	REG_NDMAxTCNT(CAMERA_NDMA) = (preview ? 256 * 192 : 640 * 480) / 2; /* words */
	REG_NDMAxWCNT(CAMERA_NDMA) = preview ? 512 : 320;                   /* words */
	REG_NDMAxBCNT(CAMERA_NDMA) = 2;
	REG_NDMAxCNT(CAMERA_NDMA)  =
		NDMA_DST_MODE(NdmaMode_Increment) |
		NDMA_SRC_MODE(NdmaMode_Fixed) |
		NDMA_BLK_WORDS(16) |
		NDMA_TIMING(NdmaTiming_Camera) |
		NDMA_TX_MODE(NdmaTxMode_Timing) |
		NDMA_START;
}

void cameraTransferStop(void)
{
	REG_CAM_CNT &= ~CAM_CNT_ENABLE;
	/* Abort a half-finished frame, otherwise NDMA waits for data forever */
	REG_NDMAxCNT(CAMERA_NDMA) &= ~NDMA_START;
}

bool cameraTransferActive(void)
{
	return ndmaIsBusy(CAMERA_NDMA);
}
