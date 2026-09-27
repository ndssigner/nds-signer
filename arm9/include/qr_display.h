/*
 * NDS-Signer - draws QR codes on the top screen (Project Nayuki's qrcodegen)
 * SPDX-License-Identifier: MIT
 */
#ifndef NDS_SIGNER_QR_DISPLAY_H
#define NDS_SIGNER_QR_DISPLAY_H

#include <nds/ndstypes.h>
#include <stddef.h>

/* Encodes `text` (ECC level L, like SeedSigner) and draws it centred on the
 * top screen with the largest integer module size that fits, surrounded by
 * `border` modules of background. `background` is a gray level 0-255
 * (SeedSigner's QR brightness setting). Returns the QR size in modules, or 0
 * if the text does not fit in a QR code. */
int qrDisplayShow(const char *text, size_t len, int border, u8 background);

/* SeedQR transcription, like SeedSigner's SeedTranscribeSeedQR screens:
 * ECC level L exactly (no boost, so the size matches the SeedQR templates),
 * `binary` data for CompactSeedQR. zoneModules == 0 draws the whole QR code;
 * otherwise zone (zoneX, zoneY) of zoneModules x zoneModules modules is drawn
 * at 24 px per module in the middle of the screen, with thin lines between
 * its modules and the neighbouring zones dimmed. Returns the size in
 * modules, or 0 if the data does not fit. */
int qrTranscribeShow(const u8 *data, size_t len, bool binary, int zoneModules,
                     int zoneX, int zoneY);

#endif /* NDS_SIGNER_QR_DISPLAY_H */
