/*
 * NDS-Signer - QR payload type detection
 * SPDX-License-Identifier: MIT
 *
 * Port of SeedSigner's DecodeQR.detect_segment_type() (decode_qr.py, MIT).
 * Python regular expressions are replaced by small hand-written matchers; each
 * one quotes the regex it implements.
 *
 * Differences from SeedSigner, pending later phases:
 *  - is_base64_psbt() fully parses the PSBT; until the PSBT parser is ported we
 *    only check the BIP-174 magic bytes ("psbt" 0xFF) after base64 decoding.
 *  - SEED__MNEMONIC, SEED__FOUR_LETTER_MNEMONIC (need the BIP-39 wordlist) and
 *    PSBT__BASE43 (needs the PSBT parser) are not detected yet.
 */
#include <ctype.h>
#include <stdbool.h>
#include <string.h>

#include "qr_type.h"

static const char *const s_names[] = {
	[QR_PSBT_BASE64]               = "psbt__base64",
	[QR_PSBT_SPECTER]              = "psbt__specter",
	[QR_PSBT_BASE43]               = "psbt__base43",
	[QR_PSBT_UR2]                  = "psbt__ur2",
	[QR_PSBT_BBQR]                 = "psbt__bbqr",
	[QR_SEED_SEEDQR]               = "seed__seedqr",
	[QR_SEED_COMPACTSEEDQR]        = "seed__compactseedqr",
	[QR_SEED_UR2]                  = "seed__ur2",
	[QR_SEED_MNEMONIC]             = "seed__mnemonic",
	[QR_SEED_FOUR_LETTER_MNEMONIC] = "seed__four_letter_mnemonic",
	[QR_SETTINGS]                  = "settings",
	[QR_XPUB]                      = "xpub",
	[QR_XPUB_SPECTER]              = "xpub__specter",
	[QR_XPUB_UR]                   = "xpub__ur",
	[QR_BITCOIN_ADDRESS]           = "bitcoin_address",
	[QR_SIGN_MESSAGE]              = "sign_message",
	[QR_WALLET_SPECTER]            = "wallet__specter",
	[QR_WALLET_UR]                 = "wallet__ur",
	[QR_WALLET_CONFIGFILE]         = "wallet__configfile",
	[QR_WALLET_GENERIC]            = "wallet__generic",
	[QR_OUTPUT_UR]                 = "output__ur",
	[QR_ACCOUNT_UR]                = "account__ur",
	[QR_BYTES_UR]                  = "bytes__ur",
	[QR_INVALID]                   = "invalid",
};

const char *qrTypeName(QrType type)
{
	if ((unsigned)type >= sizeof(s_names) / sizeof(s_names[0]))
		return "invalid";
	return s_names[type];
}

/* A payload viewed as a (not NUL-terminated) string */
typedef struct {
	const char *s;
	size_t len;
} Str;

static bool startsWithNoCase(Str s, const char *prefix)
{
	size_t n = strlen(prefix);
	return s.len >= n && strncasecmp(s.s, prefix, n) == 0;
}

static bool startsWith(Str s, const char *prefix)
{
	size_t n = strlen(prefix);
	return s.len >= n && strncmp(s.s, prefix, n) == 0;
}

static bool contains(Str s, const char *needle)
{
	size_t n = strlen(needle);
	for (size_t i = 0; i + n <= s.len; i++)
		if (memcmp(s.s + i, needle, n) == 0)
			return true;
	return false;
}

static bool containsNoCase(Str s, const char *needle)
{
	size_t n = strlen(needle);
	for (size_t i = 0; i + n <= s.len; i++)
		if (strncasecmp(s.s + i, needle, n) == 0)
			return true;
	return false;
}

static bool isBase64Char(char c)
{
	return isalnum((unsigned char)c) || c == '+' || c == '/' || c == '=';
}

static int base64Value(char c)
{
	if (c >= 'A' && c <= 'Z') return c - 'A';
	if (c >= 'a' && c <= 'z') return c - 'a' + 26;
	if (c >= '0' && c <= '9') return c - '0' + 52;
	if (c == '+') return 62;
	if (c == '/') return 63;
	return -1;
}

/* Parses r'^p(\d+)of(\d+) ' (case-insensitive) and returns the offset just
 * past the space, or 0 if it does not match. */
static size_t matchSpecterPrefix(Str s)
{
	size_t i = 0;
	if (i >= s.len || tolower((unsigned char)s.s[i++]) != 'p')
		return 0;
	size_t digits = i;
	while (i < s.len && isdigit((unsigned char)s.s[i])) i++;
	if (i == digits || i + 2 > s.len || strncasecmp(s.s + i, "of", 2) != 0)
		return 0;
	i += 2;
	digits = i;
	while (i < s.len && isdigit((unsigned char)s.s[i])) i++;
	if (i == digits || i >= s.len || s.s[i] != ' ')
		return 0;
	return i + 1;
}

/* r'^p(\d+)of(\d+) ([A-Za-z0-9+\/=]+$)' */
static bool isSpecterPsbt(Str s)
{
	size_t i = matchSpecterPrefix(s);
	if (i == 0 || i == s.len)
		return false;
	for (; i < s.len; i++)
		if (!isBase64Char(s.s[i]))
			return false;
	return true;
}

/* Stand-in for DecodeQR.is_base64_psbt(): valid base64 whose decoded bytes
 * start with the BIP-174 magic "psbt\xff". */
static bool isBase64Psbt(Str s)
{
	static const unsigned char magic[5] = { 'p', 's', 'b', 't', 0xFF };

	if (s.len < 8 || s.len % 4 != 0)
		return false;
	for (size_t i = 0; i < s.len; i++) {
		if (s.s[i] == '=') {
			/* padding only at the very end */
			if (s.len - i > 2 || (i + 1 < s.len && s.s[i + 1] != '='))
				return false;
		} else if (base64Value(s.s[i]) < 0) {
			return false;
		}
	}

	/* Decode the first 8 characters (6 bytes) */
	unsigned char out[6];
	for (int g = 0; g < 2; g++) {
		uint32_t v = 0;
		for (int k = 0; k < 4; k++)
			v = (v << 6) | (uint32_t)(base64Value(s.s[g * 4 + k]) & 0x3F);
		out[g * 3 + 0] = v >> 16;
		out[g * 3 + 1] = v >> 8;
		out[g * 3 + 2] = v;
	}
	return memcmp(out, magic, sizeof(magic)) == 0;
}

/* r"^B\$[2HZ]P[0-9A-Z]{4}" */
static bool isBbqrPsbt(Str s)
{
	if (s.len < 8 || s.s[0] != 'B' || s.s[1] != '$' || s.s[2] == '\0' ||
	    !strchr("2HZ", s.s[2]) || s.s[3] != 'P')
		return false;
	for (int i = 4; i < 8; i++)
		if (!isdigit((unsigned char)s.s[i]) && !isupper((unsigned char)s.s[i]))
			return false;
	return true;
}

/* r'^\{\"label\".*\"descriptor\"\:.*' on the string with '\n' and ' ' removed */
static bool isSpecterWalletJson(Str s)
{
	static const char label[] = "{\"label\"";
	static const char desc[]  = "\"descriptor\":";
	size_t li = 0, di = 0;
	bool labelDone = false;

	for (size_t i = 0; i < s.len; i++) {
		char c = s.s[i];
		if (c == '\n' || c == ' ')
			continue;
		if (!labelDone) {
			if (tolower((unsigned char)c) != tolower((unsigned char)label[li]))
				return false;
			if (label[++li] == '\0')
				labelDone = true;
		} else {
			/* naive substring search is fine: the needle has no repeated prefix */
			if (tolower((unsigned char)c) == tolower((unsigned char)desc[di])) {
				if (desc[++di] == '\0')
					return true;
			} else {
				di = tolower((unsigned char)c) == desc[0] ? 1 : 0;
			}
		}
	}
	return false;
}

/* re.search(r'\d{48,96}', s) */
static bool hasDigitRun48(Str s)
{
	size_t run = 0;
	for (size_t i = 0; i < s.len; i++) {
		run = isdigit((unsigned char)s.s[i]) ? run + 1 : 0;
		if (run >= 48)
			return true;
	}
	return false;
}

/* DecodeQR.is_bitcoin_address():
 *   r'^bitcoin\:.*'  or  r'^((bc1|tb1|bcr|[123]|[mn])[a-zA-HJ-NP-Z0-9]{25,62})$'
 * (both case-insensitive, so the I/O exclusion in the character class is
 * ineffective in SeedSigner too; kept identical on purpose). */
static bool isBitcoinAddress(Str s)
{
	if (startsWithNoCase(s, "bitcoin:"))
		return true;

	size_t p;
	if (startsWithNoCase(s, "bc1") || startsWithNoCase(s, "tb1") || startsWithNoCase(s, "bcr"))
		p = 3;
	else if (s.len > 0 && s.s[0] != '\0' && strchr("123mnMN", s.s[0]))
		p = 1;
	else
		return false;

	size_t body = s.len - p;
	if (body < 25 || body > 62)
		return false;
	for (size_t i = p; i < s.len; i++)
		if (!isalnum((unsigned char)s.s[i]))
			return false;
	return true;
}

/* Python's bytes.decode('utf-8') succeeds */
static bool isValidUtf8(const uint8_t *p, size_t len)
{
	size_t i = 0;
	while (i < len) {
		uint8_t c = p[i];
		size_t n;
		uint32_t cp;
		if (c < 0x80)                { i++; continue; }
		else if ((c & 0xE0) == 0xC0) { n = 1; cp = c & 0x1F; }
		else if ((c & 0xF0) == 0xE0) { n = 2; cp = c & 0x0F; }
		else if ((c & 0xF8) == 0xF0) { n = 3; cp = c & 0x07; }
		else return false;
		for (size_t k = 1; k <= n; k++) {
			if (i + k >= len || (p[i + k] & 0xC0) != 0x80)
				return false;
			cp = (cp << 6) | (p[i + k] & 0x3F);
		}
		/* reject overlong forms, surrogates and out-of-range code points */
		if ((n == 1 && cp < 0x80) || (n == 2 && cp < 0x800) || (n == 3 && cp < 0x10000) ||
		    (cp >= 0xD800 && cp <= 0xDFFF) || cp > 0x10FFFF)
			return false;
		i += n + 1;
	}
	return true;
}

QrType qrDetectSegmentType(const uint8_t *data, size_t len)
{
	Str s = { (const char *)data, len };

	/* SeedSigner only runs the text checks if the bytes decode as UTF-8 */
	bool isText = isValidUtf8(data, len);

	if (isText) {
		/* PSBT */
		if (startsWithNoCase(s, "UR:CRYPTO-PSBT/"))    return QR_PSBT_UR2;
		if (startsWithNoCase(s, "UR:CRYPTO-OUTPUT/"))  return QR_OUTPUT_UR;
		if (startsWithNoCase(s, "UR:CRYPTO-ACCOUNT/")) return QR_ACCOUNT_UR;
		if (isSpecterPsbt(s))                          return QR_PSBT_SPECTER;
		if (startsWithNoCase(s, "UR:BYTES/"))          return QR_BYTES_UR;
		if (isBase64Psbt(s))                           return QR_PSBT_BASE64;
		if (isBbqrPsbt(s))                             return QR_PSBT_BBQR;

		/* Wallet descriptor */
		if (matchSpecterPrefix(s))                     return QR_WALLET_SPECTER;
		if (isSpecterWalletJson(s))                    return QR_WALLET_SPECTER;
		if (containsNoCase(s, "multisig setup file"))  return QR_WALLET_CONFIGFILE;
		if (contains(s, "sortedmulti"))                return QR_WALLET_GENERIC;

		/* Seed */
		if (hasDigitRun48(s))                          return QR_SEED_SEEDQR;

		if (isBitcoinAddress(s))                       return QR_BITCOIN_ADDRESS;
		if (startsWith(s, "signmessage"))              return QR_SIGN_MESSAGE;
		if (startsWith(s, "settings::"))               return QR_SETTINGS;

		/* TODO(seeds phase): SEED__MNEMONIC / SEED__FOUR_LETTER_MNEMONIC
		 * TODO(psbt phase):  PSBT__BASE43 */
	}

	/* 32 bytes for 24-word CompactSeedQR; 16 bytes for 12-word CompactSeedQR */
	if (len == 32 || len == 16)
		return QR_SEED_COMPACTSEEDQR;

	return QR_INVALID;
}
