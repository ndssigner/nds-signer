/*
 * NDS-Signer - Aptina MT9V113 camera sensor driver (ARM7)
 * SPDX-License-Identifier: MIT
 *
 * Adapted from Epicpkmn11/dsi-camera (public domain / Unlicense), which follows
 * GBATEK "DSi Aptina Camera Initialization":
 *   https://problemkaputt.de/gbatek.htm#dsiaptinacamerainitialization
 *
 * Changes for NDS-Signer:
 *  - every wait loop has a timeout, so a missing or badly emulated sensor
 *    reports an error instead of hanging the ARM7 forever;
 *  - errors are latched in s_ok and returned to the ARM9.
 */
#include <nds.h>

#include "aptina.h"
#include "aptina_i2c.h"

/* ~2 seconds at 60 Hz */
#define APT_TIMEOUT_FRAMES 120

static u8 s_currentDevice = I2C_CAM_INNER;

/* Cleared on the first I2C error or timeout of the current operation. Once
 * cleared, the remaining waits are skipped so a failure returns quickly. */
static bool s_ok;

static void aptWrite(u8 device, u16 reg, u16 data)
{
	if (s_ok && !aptWriteRegister(device, reg, data))
		s_ok = false;
}

/* Waits until (register & mask) == expected */
static void aptWaitFor(u8 device, u16 reg, u16 mask, u16 expected)
{
	for (int i = 0; s_ok && i < APT_TIMEOUT_FRAMES; i++) {
		if ((aptReadRegister(device, reg) & mask) == expected)
			return;
		threadWaitForVBlank();
	}
	s_ok = false;
}

static void aptWaitClr(u8 device, u16 reg, u16 mask) { aptWaitFor(device, reg, mask, 0); }
static void aptWaitSet(u8 device, u16 reg, u16 mask) { aptWaitFor(device, reg, mask, mask); }

static void aptClr(u8 device, u16 reg, u16 mask)
{
	aptWrite(device, reg, aptReadRegister(device, reg) & ~mask);
}

static void aptSet(u8 device, u16 reg, u16 mask)
{
	aptWrite(device, reg, aptReadRegister(device, reg) | mask);
}

/* The sensor's internal MCU variables are accessed through an address/data
 * register pair. */
static u16 aptReadMcu(u8 device, u16 reg)
{
	aptWrite(device, 0x098C, reg);
	return aptReadRegister(device, 0x0990);
}

static void aptWriteMcu(u8 device, u16 reg, u16 data)
{
	aptWrite(device, 0x098C, reg);
	aptWrite(device, 0x0990, data);
}

static void aptWaitMcuClr(u8 device, u16 reg, u16 mask)
{
	for (int i = 0; s_ok && i < APT_TIMEOUT_FRAMES; i++) {
		if ((aptReadMcu(device, reg) & mask) == 0)
			return;
		threadWaitForVBlank();
	}
	s_ok = false;
}

static void aptSetMcu(u8 device, u16 reg, u16 mask)
{
	aptWriteMcu(device, reg, aptReadMcu(device, reg) | mask);
}

static void setCameraLed(bool on)
{
	i2cLock();
	i2cWriteRegister8(I2cDev_MCU, McuReg_CamLed, on ? 1 : 0);
	i2cUnlock();
}

bool aptInit(u8 device)
{
	const bool inner = device == I2C_CAM_INNER;

	s_ok = true;
	aptWrite(device, 0x001A, 0x0003);  // RESET_AND_MISC_CONTROL (issue reset)   ;\reset
	aptWrite(device, 0x001A, 0x0000);  // RESET_AND_MISC_CONTROL (release reset) ;/
	aptWrite(device, 0x0018, 0x4028);  // STANDBY_CONTROL (wakeup)               ;\.
	aptWrite(device, 0x001E, 0x0201);  // PAD_SLEW                               ; wakeup
	aptWrite(device, 0x0016, 0x42DF);  // CLOCKS_CONTROL                         ;
	aptWaitClr(device, 0x0018, 0x4000); // STANDBY_CONTROL (wait for WakeupDone) ;
	aptWaitSet(device, 0x301A, 0x0004); // UNDOC_CORE_301A (wait for WakeupDone) ;/
	aptWriteMcu(device, 0x02F0, 0x0000); // UNDOC! RAM?
	aptWriteMcu(device, 0x02F2, 0x0210); // UNDOC! RAM?
	aptWriteMcu(device, 0x02F4, 0x001A); // UNDOC! RAM?
	aptWriteMcu(device, 0x2145, 0x02F4); // UNDOC! SEQ?
	aptWriteMcu(device, 0xA134, 0x0001); // UNDOC! SEQ?
	aptSetMcu(device, 0xA115, 0x0002);   // SEQ_CAP_MODE (set bit1=video)
	aptWriteMcu(device, 0x2755, 0x0002); // MODE_OUTPUT_FORMAT_A (bit5=0=YUV)    ;\select
	aptWriteMcu(device, 0x2757, 0x0002); // MODE_OUTPUT_FORMAT_B                 ;/YUV mode
	aptWrite(device, 0x0014, 0x2145);    // PLL_CONTROL                          ;\.
	aptWrite(device, 0x0010, 0x0111);    // PLL_DIVIDERS                         ; match
	aptWrite(device, 0x0012, 0x0000);    // PLL_P_DIVIDERS                       ; PLL
	aptWrite(device, 0x0014, 0x244B);    // PLL_CONTROL                          ; to DSi
	aptWrite(device, 0x0014, 0x304B);    // PLL_CONTROL                          ; timings
	aptWaitSet(device, 0x0014, 0x8000);  // PLL_CONTROL (wait for PLL Lock okay) ;
	aptClr(device, 0x0014, 0x0001);      // PLL_CONTROL (disable PLL Bypass)     ;/
	aptWriteMcu(device, 0x2703, 0x0100); // MODE_OUTPUT_WIDTH_A              ;\Size A
	aptWriteMcu(device, 0x2705, 0x00C0); // MODE_OUTPUT_HEIGHT_A             ;/ 256x192
	aptWriteMcu(device, 0x2707, 0x0280); // MODE_OUTPUT_WIDTH_B              ;\Size B
	aptWriteMcu(device, 0x2709, 0x01E0); // MODE_OUTPUT_HEIGHT_B             ;/ 640x480
	aptWriteMcu(device, 0x2715, 0x0001); // MODE_SENSOR_ROW_SPEED_A          ;\.
	aptWriteMcu(device, 0x2719, 0x001A); // MODE_SENSOR_FINE_CORRECTION_A    ;
	aptWriteMcu(device, 0x271B, 0x006B); // MODE_SENSOR_FINE_IT_MIN_A        ; Sensor A
	aptWriteMcu(device, 0x271D, 0x006B); // MODE_SENSOR_FINE_IT_MAX_MARGIN_A ;
	aptWriteMcu(device, 0x271F, 0x02C0); // MODE_SENSOR_FRAME_LENGTH_A       ;
	aptWriteMcu(device, 0x2721, 0x034B); // MODE_SENSOR_LINE_LENGTH_PCK_A    ;/
	aptWriteMcu(device, 0xA20B, 0x0000); // AE_MIN_INDEX                     ;\AE min/max
	aptWriteMcu(device, 0xA20C, 0x0006); // AE_MAX_INDEX                     ;/
	aptWriteMcu(device, 0x272B, 0x0001); // MODE_SENSOR_ROW_SPEED_B          ;\.
	aptWriteMcu(device, 0x272F, 0x001A); // MODE_SENSOR_FINE_CORRECTION_B    ;
	aptWriteMcu(device, 0x2731, 0x006B); // MODE_SENSOR_FINE_IT_MIN_B        ; Sensor B
	aptWriteMcu(device, 0x2733, 0x006B); // MODE_SENSOR_FINE_IT_MAX_MARGIN_B ;
	aptWriteMcu(device, 0x2735, 0x02C0); // MODE_SENSOR_FRAME_LENGTH_B       ;
	aptWriteMcu(device, 0x2737, 0x034B); // MODE_SENSOR_LINE_LENGTH_PCK_B    ;/
	aptSet(device, 0x3210, 0x0008);      // COLOR_PIPELINE_CONTROL (PGA pixel shading..)
	aptWriteMcu(device, 0xA208, 0x0000); // UNDOC! RESERVED_AE_08
	aptWriteMcu(device, 0xA24C, 0x0020); // AE_TARGETBUFFERSPEED
	aptWriteMcu(device, 0xA24F, 0x0070); // AE_BASETARGET
	/* Read mode: x-flip on the inner camera */
	aptWriteMcu(device, 0x2717, inner ? 0x0024 : 0x0025); // MODE_SENSOR_READ_MODE_A
	aptWriteMcu(device, 0x272D, inner ? 0x0024 : 0x0025); // MODE_SENSOR_READ_MODE_B
	aptWriteMcu(device, 0xA202, inner ? 0x0022 : 0x0000); // AE_WINDOW_POS
	aptWriteMcu(device, 0xA203, inner ? 0x00BB : 0x00FF); // AE_WINDOW_SIZE
	aptSet(device, 0x0016, 0x0020);      // CLOCKS_CONTROL (set bit5=1, reserved)
	aptWriteMcu(device, 0xA115, 0x0072); // SEQ_CAP_MODE (was already manipulated above)
	aptWriteMcu(device, 0xA11F, 0x0001); // SEQ_PREVIEW_1_AWB
	aptWrite(device, 0x326C, inner ? 0x0900 : 0x1000); // APERTURE_PARAMETERS
	aptWriteMcu(device, 0xAB22, inner ? 0x0001 : 0x0002); // HG_LL_APCORR1
	aptWriteMcu(device, 0xA103, 0x0006);   // SEQ_CMD (06h=RefreshMode)
	aptWaitMcuClr(device, 0xA103, 0x000F); // SEQ_CMD (wait above to become ZERO)
	aptWriteMcu(device, 0xA103, 0x0005);   // SEQ_CMD (05h=Refresh)
	aptWaitMcuClr(device, 0xA103, 0x000F); // SEQ_CMD (wait above to become ZERO)

	return s_ok;
}

bool aptActivate(u8 device)
{
	s_ok = true;
	aptClr(device, 0x0018, 0x0001);     // STANDBY_CONTROL (bit0=0=wakeup)       ;\.
	aptWaitClr(device, 0x0018, 0x4000); // STANDBY_CONTROL (wait for WakeupDone) ; Wakeup
	aptWaitSet(device, 0x301A, 0x0004); // UNDOC_CORE_301A (wait for WakeupDone) ;/
	aptWrite(device, 0x3012, 0x0010);   // COARSE_INTEGRATION_TIME (higher = brighter)
	aptSet(device, 0x001A, 0x0200);     // RESET_AND_MISC_CONTROL (Parallel On)
	/* The outer camera LED tells bystanders the camera is recording: keep it. */
	if (s_ok && device == I2C_CAM_OUTER)
		setCameraLed(true);

	if (s_ok)
		s_currentDevice = device;
	return s_ok;
}

bool aptDeactivate(u8 device)
{
	s_ok = true;
	aptClr(device, 0x001A, 0x0200);     // RESET_AND_MISC_CONTROL (Parallel Off)
	aptSet(device, 0x0018, 0x0001);     // STANDBY_CONTROL (set bit0=1=Standby)   ;\.
	aptWaitSet(device, 0x0018, 0x4000); // STANDBY_CONTROL (wait for StandbyDone) ; Standby
	aptWaitClr(device, 0x301A, 0x0004); // UNDOC_CORE_301A (wait for StandbyDone) ;/
	if (device == I2C_CAM_OUTER)
		setCameraLed(false);

	s_currentDevice = I2C_CAM_INNER;
	return s_ok;
}

bool aptSetMode(CaptureMode mode)
{
	s_ok = true;
	aptWriteMcu(s_currentDevice, 0xA103, mode);
	aptWaitMcuClr(s_currentDevice, 0xA103, 0xFFFF);
	return s_ok;
}
