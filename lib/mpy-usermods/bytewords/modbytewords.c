/*
 * NDS-Signer - `_bytewords` MicroPython module. SPDX-License-Identifier: MIT
 *
 * decode_minimal(s, bytewords) does what SeedSigner's
 * helpers/ur2/bytewords.py does in decode(s, 0, 2) before the checksum
 * check: split s into 2-letter words and map each one with decode_word().
 * It returns the bytes, checksum included. Any invalid word raises
 * ValueError('Invalid Bytewords.'), as upstream does.
 *
 * `bytewords` is upstream's BYTEWORDS string (256 words of 4 letters). The
 * lookup table is built from it the same way decode_word() builds
 * WORD_ARRAY, indexed by the first and last letters.
 *
 * Python spends ~0.4 ms per byte in decode_word() on the DSi (~100 ms per
 * scanned QR part). The overlay's helpers/ur2/__init__.py installs this
 * version. tests/host/bytewords_check.py compares it with upstream's.
 */
#include <string.h>

#include "py/obj.h"
#include "py/objstr.h"
#include "py/runtime.h"

#define DIM 26

static mp_obj_t bytewords_decode_minimal(mp_obj_t s_in, mp_obj_t words_in)
{
	size_t len, words_len;
	const char *s = mp_obj_str_get_data(s_in, &len);
	const char *words = mp_obj_str_get_data(words_in, &words_len);
	int16_t table[DIM * DIM];

	if (words_len != 256 * 4)
		mp_raise_ValueError(MP_ERROR_TEXT("bytewords table"));
	for (int i = 0; i < DIM * DIM; i++)
		table[i] = -1;
	for (int i = 0; i < 256; i++) {
		int x = words[i * 4] - 'a', y = words[i * 4 + 3] - 'a';
		if (x < 0 || x >= DIM || y < 0 || y >= DIM)
			mp_raise_ValueError(MP_ERROR_TEXT("bytewords table"));
		table[y * DIM + x] = (int16_t)i;
	}

	/* upstream: partition(s, 2) -> an odd length leaves a 1-letter word;
	 * non-ASCII characters are never valid letters (MicroPython's
	 * str.lower() only maps ASCII), so working on bytes is equivalent */
	if (len % 2)
		goto invalid;
	vstr_t out;
	vstr_init_len(&out, len / 2);
	for (size_t i = 0; i < len / 2; i++) {
		int a = (unsigned char)s[2 * i], b = (unsigned char)s[2 * i + 1];
		if (a >= 'A' && a <= 'Z')
			a += 'a' - 'A';
		if (b >= 'A' && b <= 'Z')
			b += 'a' - 'A';
		int x = a - 'a', y = b - 'a';
		if (x < 0 || x >= DIM || y < 0 || y >= DIM || table[y * DIM + x] < 0) {
			vstr_clear(&out);
			goto invalid;
		}
		out.buf[i] = (char)table[y * DIM + x];
	}
	mp_obj_t result = mp_obj_new_bytearray(out.len, out.buf);
	vstr_clear(&out);
	return result;

invalid:
	mp_raise_ValueError(MP_ERROR_TEXT("Invalid Bytewords."));
}
static MP_DEFINE_CONST_FUN_OBJ_2(bytewords_decode_minimal_obj, bytewords_decode_minimal);

static const mp_rom_map_elem_t bytewords_module_globals_table[] = {
	{ MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR__bytewords) },
	{ MP_ROM_QSTR(MP_QSTR_decode_minimal), MP_ROM_PTR(&bytewords_decode_minimal_obj) },
};
static MP_DEFINE_CONST_DICT(bytewords_module_globals, bytewords_module_globals_table);

const mp_obj_module_t bytewords_user_cmodule = {
	.base = { &mp_type_module },
	.globals = (mp_obj_dict_t *)&bytewords_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR__bytewords, bytewords_user_cmodule);
