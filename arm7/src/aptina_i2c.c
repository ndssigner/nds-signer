/*---------------------------------------------------------------------------------

	I2C control for the ARM7

	Copyright (C) 2011
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
 * ALTERED SOURCE VERSION.
 * Based on libnds's i2c.twl.c, modified by Pk11 (2020, Epicpkmn11/dsi-camera)
 * to work with the 16-bit addresses and data of the Aptina camera sensors.
 * Modified for NDS-Signer: each transaction holds calico's I2C bus mutex,
 * since calico's own power-management code shares the same bus.
 */

#include "aptina_i2c.h"

#include <nds.h>

enum {
	I2C_NONE  = 0x00,
	I2C_STOP  = 0x01,
	I2C_START = 0x02,
	I2C_ACK   = 0x10,
	I2C_READ  = 0x20,
};

#define I2C_RETRIES 8

static inline void aptWaitBusy(void)
{
	while (REG_I2C_CNT & 0x80)
		;
}

static inline bool aptGetResult(void)
{
	aptWaitBusy();
	return (REG_I2C_CNT >> 4) & 0x01;
}

static u8 aptGetData(u8 flags)
{
	REG_I2C_CNT = 0xC0 | flags;
	aptWaitBusy();
	return REG_I2C_DATA;
}

static bool aptSendByte(u8 data, u8 flags)
{
	aptWaitBusy();
	REG_I2C_DATA = data;
	REG_I2C_CNT  = 0xC0 | flags;
	return aptGetResult();
}

bool aptWriteRegister(u8 device, u16 reg, u16 data)
{
	bool ok = false;

	i2cLock();
	for (int i = 0; i < I2C_RETRIES && !ok; i++) {
		ok = aptSendByte(device, I2C_START) &&
		     aptSendByte(reg >> 8, I2C_NONE) &&
		     aptSendByte(reg & 0xFF, I2C_NONE) &&
		     aptSendByte(data >> 8, I2C_NONE) &&
		     aptSendByte(data & 0xFF, I2C_STOP);
		if (!ok)
			REG_I2C_CNT = 0xC5; /* abort + stop */
	}
	i2cUnlock();

	return ok;
}

u16 aptReadRegister(u8 device, u16 reg)
{
	u16 value = 0xFFFF;

	i2cLock();
	for (int i = 0; i < I2C_RETRIES; i++) {
		if (aptSendByte(device, I2C_START) &&
		    aptSendByte(reg >> 8, I2C_NONE) &&
		    aptSendByte(reg & 0xFF, I2C_STOP) &&
		    aptSendByte(device | 1, I2C_START)) {
			value = aptGetData(I2C_READ | I2C_ACK) << 8;
			value |= aptGetData(I2C_READ | I2C_STOP);
			break;
		}
		REG_I2C_CNT = 0xC5; /* abort + stop */
	}
	i2cUnlock();

	return value;
}
