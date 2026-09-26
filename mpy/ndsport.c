/*
 * NDS-Signer - MicroPython port glue (SPIKE)
 * SPDX-License-Identifier: MIT
 *
 * There is no filesystem on purpose (stateless signer): modules only come
 * from the frozen bytecode built into the ROM, and open() always fails.
 */
#include "py/builtin.h"
#include "py/lexer.h"
#include "py/mperrno.h"
#include "py/runtime.h"

mp_import_stat_t mp_import_stat(const char *path)
{
	(void)path;
	return MP_IMPORT_STAT_NO_EXIST;
}

mp_lexer_t *mp_lexer_new_from_file(qstr filename)
{
	(void)filename;
	mp_raise_OSError(MP_ENOENT);
}

static mp_obj_t nds_open(size_t n_args, const mp_obj_t *args, mp_map_t *kwargs)
{
	(void)n_args;
	(void)args;
	(void)kwargs;
	mp_raise_OSError(MP_EPERM);
}
MP_DEFINE_CONST_FUN_OBJ_KW(mp_builtin_open_obj, 1, nds_open);

#include <stdio.h>
#include <nds/debug.h>

void nds_print_strn(const char *str, size_t len)
{
	printf("%.*s", (int)len, str);
	nocashWrite(str, len);
}
