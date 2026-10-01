/*---------------------------------------------------------------------------------

	default ARM7 core

		Copyright (C) 2005 - 2010
		Michael Noland (joat)
		Jason Rogers (dovoto)
		Dave Murphy (WinterMute)

	This software is provided 'as-is', without any express or implied
	warranty.  In no event will the authors be held liable for any
	damages arising from the use of this software.

	Permission is granted to anyone to use this software for any
	purpose, including commercial applications, and to alter it and
	redistribute it freely, subject to the following restrictions:

	1.	The origin of this software must not be misrepresented; you
		must not claim that you wrote the original software. If you use
		this software in a product, an acknowledgment in the product
		documentation would be appreciated but is not required.

	2.	Altered source versions must be plainly marked as such, and
		must not be misrepresented as being the original software.

	3.	This notice may not be removed or altered from any source
		distribution.

---------------------------------------------------------------------------------*/

/*
 * ALTERED SOURCE VERSION: NDS-Signer minimal ARM7 core.
 *
 * Security: compared with the default calico core, this ARM7 deliberately does
 * NOT start the wireless manager (wlmgr), the block-device driver for the
 * SD card / NAND (blk), the microphone or maxmod. Their code is not even
 * linked, so the ARM9 has no way to ask for network or storage access, or to
 * listen. The RTC is not needed either. The sound driver is started (output
 * only): optional UI feedback sounds, see arm9/src/sfx.c.
 *
 * On top of that, wirelessOff() powers the wireless hardware down at start
 * (the launcher may leave it on): both the DS (Mitsumi) and the DSi
 * (Atheros) chips, and the wireless LED.
 */
#include <nds.h>

#include "camera_server.h"

static void wirelessOff(void)
{
	pmPowerOff(POWCNT_WL_MITSUMI);
	if (systemIsTwlMode()) {
		REG_GPIO_WL &= ~GPIO_WL_ACTIVE;  // hold the Atheros chip in reset
		i2cLock();
		u8 led = i2cReadRegister8(I2cDev_MCU, McuReg_WifiLed);
		i2cWriteRegister8(I2cDev_MCU, McuReg_WifiLed, led & ~1);  // bit 0: LED on
		i2cUnlock();
	}
}

int main(void)
{
	// Read settings from NVRAM (touch screen calibration, etc.)
	envReadNvramSettings();

	// Set up extended keypad server (X/Y/hinge)
	keypadStartExtServer();

	// Configure and enable VBlank interrupt
	lcdSetIrqMask(DISPSTAT_IE_ALL, DISPSTAT_IE_VBLANK);
	irqEnable(IRQ_VBLANK);

	// Initialize power management
	pmInit();

	// No networking: the wireless hardware stays off
	wirelessOff();

	// Set up touch screen driver
	touchInit();
	touchStartServer(80, MAIN_THREAD_PRIO);

	// Sound driver (output only; handles the DSi audio codec)
	soundStartServer(MAIN_THREAD_PRIO - 0x10);

	// DSi camera (I2C) server
	cameraServerStart(MAIN_THREAD_PRIO);

	// Keep the ARM7 mostly idle
	while (pmMainLoop()) {
		threadWaitForVBlank();
	}

	return 0;
}
