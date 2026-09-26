/*
 * NDS-Signer - host unit tests for the QR type detection port
 * SPDX-License-Identifier: MIT
 *
 * Expected results follow SeedSigner's DecodeQR.detect_segment_type().
 * Build and run with: make -C tests/host
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "qr_type.h"

static int s_failures;

static void check(const char *label, const void *data, size_t len, QrType expected)
{
	QrType got = qrDetectSegmentType(data, len);
	if (got != expected) {
		printf("FAIL %-40s expected %s, got %s\n", label, qrTypeName(expected), qrTypeName(got));
		s_failures++;
	} else {
		printf("ok   %-40s %s\n", label, qrTypeName(got));
	}
}

static void checkStr(const char *s, QrType expected)
{
	char label[41];
	snprintf(label, sizeof(label), "%s", s);
	check(label, s, strlen(s), expected);
}

static void checkFile(const char *path, QrType expected)
{
	FILE *f = fopen(path, "rb");
	if (!f) {
		printf("FAIL cannot open %s\n", path);
		s_failures++;
		return;
	}
	static char buf[4096];
	size_t len = fread(buf, 1, sizeof(buf), f);
	fclose(f);
	while (len && (buf[len - 1] == '\n' || buf[len - 1] == '\r'))
		len--;
	check(path, buf, len, expected);
}

int main(void)
{
	/* tests/vectors (see README there) */
	checkFile("../vectors/psbt_base64_singlesig.txt", QR_PSBT_BASE64);
	checkFile("../vectors/address_testnet.txt", QR_BITCOIN_ADDRESS);
	checkFile("../vectors/seedqr_12words.txt", QR_SEED_SEEDQR);
	checkFile("../vectors/plain_text.txt", QR_INVALID);

	/* UR / Specter / BBQr prefixes */
	checkStr("ur:crypto-psbt/hdcxlkahssqzwfvslofzoxwkrewngotktbmwjkwdcmnefsaaehrlolkskn", QR_PSBT_UR2);
	checkStr("UR:CRYPTO-PSBT/1-3/LPADAXCFAXHLCY", QR_PSBT_UR2);
	checkStr("ur:crypto-output/taadmutaaddlosaowkaxhdclaxwmfmdeiamecsdsemgtvsjzcncygrkowtrontzschgezokstswkkscfmklrtauteyaahdcxiehfonurdppfyntapejpproypegrdawkgmaewejlsfdtsrfybdehcsaankgdpyayatbhmwbbdkiabkgdgalfk", QR_OUTPUT_UR);
	checkStr("ur:crypto-account/oeadcyemrewytyaolttaadmutaaddloso", QR_ACCOUNT_UR);
	checkStr("ur:bytes/hdcxdwsatnzofxdydmfngdwmgmfweekebdpssnsbhlhhtngabbiefrcaamnbdbynlddpfytsweltme", QR_BYTES_UR);
	checkStr("p1of3 cHNidP8BAHICAAAAAQDo5ey+2HIrNUkExsFhsImv1OK1cYA9x/bRjYQD", QR_PSBT_SPECTER);
	checkStr("p1of2 {\"label\": \"wallet\"", QR_WALLET_SPECTER);
	checkStr("B$ZP0100FMUE4KXZZ7EFU", QR_PSBT_BBQR);

	/* Wallet descriptors */
	checkStr("{\"label\": \"My Multisig\", \"descriptor\": \"wsh(sortedmulti(2,...))\"}", QR_WALLET_SPECTER);
	checkStr("# Keystone Multisig setup file\nName: test", QR_WALLET_CONFIGFILE);
	checkStr("wsh(sortedmulti(1,[f3e46e9e/48h/1h/0h/2h]tpub...))", QR_WALLET_GENERIC);

	/* Addresses */
	checkStr("bc1q8wfyqsah7pfehz3yz6j8wz9r0ha5v3h4wcsk4p", QR_BITCOIN_ADDRESS);
	checkStr("BC1Q8WFYQSAH7PFEHZ3YZ6J8WZ9R0HA5V3H4WCSK4P", QR_BITCOIN_ADDRESS);
	checkStr("bitcoin:bc1q8wfyqsah7pfehz3yz6j8wz9r0ha5v3h4wcsk4p?amount=0.01", QR_BITCOIN_ADDRESS);
	checkStr("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", QR_BITCOIN_ADDRESS);
	checkStr("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy", QR_BITCOIN_ADDRESS);
	checkStr("mipcBbFg9gMiCh81Kj8tqqdgoZub1ZJRfn", QR_BITCOIN_ADDRESS);
	checkStr("bc1qshort", QR_INVALID);

	/* Misc */
	checkStr("signmessage m/84h/0h/0h/0/0 ascii:hello", QR_SIGN_MESSAGE);
	checkStr("settings::v1 name=Foo", QR_SETTINGS);

	/* Base64 that is not a PSBT */
	checkStr("SGVsbG8gd29ybGQhIQ==", QR_INVALID);

	/* SeedSigner quirk, kept on purpose: any other 16- or 32-byte payload,
	 * even plain text, is classified as a CompactSeedQR. */
	checkStr("SGVsbG8gd29ybGQh", QR_SEED_COMPACTSEEDQR);

	/* CompactSeedQR: raw 16 / 32 bytes, including invalid UTF-8 */
	static const unsigned char compact12[16] = {
		0x0e, 0x54, 0xb6, 0x41, 0x99, 0xa2, 0x26, 0x86, 0x8c, 0xd7, 0xff, 0x00, 0x10, 0x44, 0x80, 0x9f,
	};
	check("CompactSeedQR 12 words (16 bytes)", compact12, sizeof(compact12), QR_SEED_COMPACTSEEDQR);
	static unsigned char compact24[32];
	for (int i = 0; i < 32; i++)
		compact24[i] = (unsigned char)(i * 37 + 0x81);
	check("CompactSeedQR 24 words (32 bytes)", compact24, sizeof(compact24), QR_SEED_COMPACTSEEDQR);

	printf("\n%s: %d failure(s)\n", s_failures ? "FAILED" : "PASSED", s_failures);
	return s_failures ? EXIT_FAILURE : EXIT_SUCCESS;
}
