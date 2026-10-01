/*
 * NDS-Signer - ARM7 PXI server answering camera requests from the ARM9
 * SPDX-License-Identifier: MIT
 *
 * Adapted from Epicpkmn11/dsi-camera (public domain / Unlicense).
 */
#include <nds.h>

#include "aptina.h"
#include "aptina_i2c.h"
#include "camera_pxi.h"
#include "camera_server.h"

static Thread s_cameraThread;
alignas(8) static u8 s_cameraThreadStack[1024];

static u32 reply(bool ok)
{
	return ok ? CAM_REPLY_OK : CAM_REPLY_ERROR;
}

static u32 handleCommand(u32 cmd)
{
	switch (cmd) {
	case CAM_CMD_INIT:
		/* Not a DSi (or cameras disabled): nothing to talk to */
		if (!isDSiMode())
			return CAM_REPLY_ERROR;
		if (!aptInit(I2C_CAM_INNER) || !aptInit(I2C_CAM_OUTER))
			return CAM_REPLY_ERROR;
		return aptReadRegister(I2C_CAM_INNER, 0x0000); /* CHIP_VERSION */
	case CAM_CMD_INNER_ACTIVATE:   return reply(aptActivate(I2C_CAM_INNER));
	case CAM_CMD_INNER_DEACTIVATE: return reply(aptDeactivate(I2C_CAM_INNER));
	case CAM_CMD_OUTER_ACTIVATE:   return reply(aptActivate(I2C_CAM_OUTER));
	case CAM_CMD_OUTER_DEACTIVATE: return reply(aptDeactivate(I2C_CAM_OUTER));
	case CAM_CMD_MODE_PREVIEW:     return reply(aptSetMode(CAPTURE_MODE_PREVIEW));
	case CAM_CMD_MODE_CAPTURE:     return reply(aptSetMode(CAPTURE_MODE_CAPTURE));
	case CAM_CMD_POWER_OFF:  /* no return */
		if (isDSiMode())
			mcuIssueShutdown();
		pmicIssueShutdown();
	default:                       return CAM_REPLY_ERROR;
	}
}

static int cameraThreadMain(void *arg)
{
	(void)arg;

	Mailbox mb;
	u32 slots[4];
	mailboxPrepare(&mb, slots, sizeof(slots) / sizeof(slots[0]));
	pxiSetMailbox(PXI_CAMERA, &mb);

	for (;;) {
		u32 cmd = mailboxRecv(&mb);
		pxiReply(PXI_CAMERA, handleCommand(cmd));
	}

	return 0;
}

void cameraServerStart(int prio)
{
	threadPrepare(&s_cameraThread, cameraThreadMain, NULL,
	              &s_cameraThreadStack[sizeof(s_cameraThreadStack)], prio);
	threadStart(&s_cameraThread);
}
