/*
 * NDS-Signer - 16-bit register access to the Aptina camera sensors over I2C
 * SPDX-License-Identifier: Zlib (see src/aptina_i2c.c)
 */
#ifndef NDS_SIGNER_APTINA_I2C_H
#define NDS_SIGNER_APTINA_I2C_H

#include <nds/ndstypes.h>

/* Returns false if the sensor did not acknowledge after several retries. */
bool aptWriteRegister(u8 device, u16 reg, u16 data);

/* Returns 0xFFFF if the sensor did not acknowledge after several retries. */
u16 aptReadRegister(u8 device, u16 reg);

#endif /* NDS_SIGNER_APTINA_I2C_H */
