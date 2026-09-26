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
#include "py/mphal.h"
#include "py/stream.h"
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

/* sys.stdout / sys.stderr (shared/runtime/sys_stdio_mphal.c) */
mp_uint_t mp_hal_stdout_tx_strn(const char *str, size_t len)
{
	nds_print_strn(str, len);
	return len;
}

/* There is no keyboard stream: reading sys.stdin always fails. */
int mp_hal_stdin_rx_chr(void)
{
	mp_raise_OSError(MP_EPERM);
}

uintptr_t mp_hal_stdio_poll(uintptr_t poll_flags)
{
	/* stdout/stderr are always writable, stdin never readable */
	return poll_flags & MP_STREAM_POLL_WR;
}
