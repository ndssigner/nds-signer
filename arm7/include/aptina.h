/*
 * NDS-Signer - Aptina MT9V113 camera sensor driver (ARM7)
 * SPDX-License-Identifier: MIT
 */
#ifndef NDS_SIGNER_APTINA_H
#define NDS_SIGNER_APTINA_H

#include <nds/ndstypes.h>

#include "camera_pxi.h"

/* All functions return false if the sensor stopped responding (timeout). */
bool aptInit(u8 device);
bool aptActivate(u8 device);
bool aptDeactivate(u8 device);
bool aptSetMode(CaptureMode mode);

#endif /* NDS_SIGNER_APTINA_H */
