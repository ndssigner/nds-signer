/*
 * NDS-Signer - QR payload type detection
 * SPDX-License-Identifier: MIT
 *
 * Port of SeedSigner's QRType and DecodeQR.detect_segment_type()
 * (src/seedsigner/models/qr_type.py, decode_qr.py; MIT, (c) 2021 SeedSigner).
 * The order of the checks matches SeedSigner's, since it matters.
 */
#ifndef NDS_SIGNER_QR_TYPE_H
#define NDS_SIGNER_QR_TYPE_H

#include <stddef.h>
#include <stdint.h>

typedef enum {
	QR_PSBT_BASE64,
	QR_PSBT_SPECTER,
	QR_PSBT_BASE43,
	QR_PSBT_UR2,
	QR_PSBT_BBQR,

	QR_SEED_SEEDQR,
	QR_SEED_COMPACTSEEDQR,
	QR_SEED_UR2,
	QR_SEED_MNEMONIC,
	QR_SEED_FOUR_LETTER_MNEMONIC,

	QR_SETTINGS,

	QR_XPUB,
	QR_XPUB_SPECTER,
	QR_XPUB_UR,

	QR_BITCOIN_ADDRESS,

	QR_SIGN_MESSAGE,

	QR_WALLET_SPECTER,
	QR_WALLET_UR,
	QR_WALLET_CONFIGFILE,
	QR_WALLET_GENERIC,
	QR_OUTPUT_UR,
	QR_ACCOUNT_UR,
	QR_BYTES_UR,

	QR_INVALID,
} QrType;

QrType qrDetectSegmentType(const uint8_t *data, size_t len);

/* SeedSigner's string identifier, e.g. "psbt__base64" */
const char *qrTypeName(QrType type);

#endif /* NDS_SIGNER_QR_TYPE_H */
