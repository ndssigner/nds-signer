/*
 * NDS-Signer - `unicodedata` MicroPython module (normalize only), backed by
 * utf8proc. SPDX-License-Identifier: MIT
 *
 * SeedSigner applies unicodedata.normalize("NFKD"/"NFC", ...) to mnemonics and
 * BIP-39 passphrases (models/seed.py). BIP-39 requires NFKD; any deviation
 * would silently derive a different seed, so this must match CPython.
 * Checked against CPython by tests/host (make -C tests/host unicode).
 */
#include <stdlib.h>
#include <string.h>

#include "py/obj.h"
#include "py/runtime.h"

#include "utf8proc.h"

static mp_obj_t unicodedata_normalize(mp_obj_t form_in, mp_obj_t text_in)
{
	const char *form = mp_obj_str_get_str(form_in);
	size_t len;
	const char *text = mp_obj_str_get_data(text_in, &len);

	utf8proc_option_t options = UTF8PROC_STABLE;
	if (strcmp(form, "NFC") == 0)
		options |= UTF8PROC_COMPOSE;
	else if (strcmp(form, "NFD") == 0)
		options |= UTF8PROC_DECOMPOSE;
	else if (strcmp(form, "NFKC") == 0)
		options |= UTF8PROC_COMPOSE | UTF8PROC_COMPAT;
	else if (strcmp(form, "NFKD") == 0)
		options |= UTF8PROC_DECOMPOSE | UTF8PROC_COMPAT;
	else
		mp_raise_ValueError(MP_ERROR_TEXT("invalid normalization form"));

	utf8proc_uint8_t *out = NULL;
	utf8proc_ssize_t n = utf8proc_map((const utf8proc_uint8_t *)text, (utf8proc_ssize_t)len,
	                                  &out, options);
	if (n < 0) {
		free(out);
		mp_raise_ValueError(MP_ERROR_TEXT("unicode normalization failed"));
	}
	mp_obj_t result = mp_obj_new_str((const char *)out, (size_t)n);
	free(out);
	return result;
}
static MP_DEFINE_CONST_FUN_OBJ_2(unicodedata_normalize_obj, unicodedata_normalize);

static mp_obj_t unicodedata_is_normalized(mp_obj_t form_in, mp_obj_t text_in)
{
	mp_obj_t normalized = unicodedata_normalize(form_in, text_in);
	return mp_obj_new_bool(mp_obj_equal(normalized, text_in));
}
static MP_DEFINE_CONST_FUN_OBJ_2(unicodedata_is_normalized_obj, unicodedata_is_normalized);

static const mp_rom_map_elem_t unicodedata_module_globals_table[] = {
	{ MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_unicodedata) },
	{ MP_ROM_QSTR(MP_QSTR_normalize), MP_ROM_PTR(&unicodedata_normalize_obj) },
	{ MP_ROM_QSTR(MP_QSTR_is_normalized), MP_ROM_PTR(&unicodedata_is_normalized_obj) },
};
static MP_DEFINE_CONST_DICT(unicodedata_module_globals, unicodedata_module_globals_table);

const mp_obj_module_t unicodedata_user_cmodule = {
	.base = { &mp_type_module },
	.globals = (mp_obj_dict_t *)&unicodedata_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_unicodedata, unicodedata_user_cmodule);
