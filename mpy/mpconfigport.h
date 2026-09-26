/*
 * NDS-Signer - MicroPython configuration (embed port)
 * SPDX-License-Identifier: MIT
 *
 * SPIKE: see docs/architecture.md. Goal: run upstream embit and SeedSigner
 * Python unmodified on the DSi ARM9 (ARMv5TE, no FPU).
 */
#include <port/mpconfigport_common.h>

#define MICROPY_CONFIG_ROM_LEVEL        (MICROPY_CONFIG_ROM_LEVEL_EXTRA_FEATURES)

#define MICROPY_ENABLE_COMPILER         (1)
#define MICROPY_ENABLE_GC               (1)
#define MICROPY_HELPER_REPL             (0)
#define MICROPY_KBD_EXCEPTION           (0)

/* Bitcoin code needs arbitrary-precision integers */
#define MICROPY_LONGINT_IMPL            (MICROPY_LONGINT_IMPL_MPZ)

/* Soft-float single precision: the ARM9 has no FPU */
#define MICROPY_FLOAT_IMPL              (MICROPY_FLOAT_IMPL_FLOAT)

#define MICROPY_PY_SYS                  (1)
#define MICROPY_PY_GC                   (1)

/* No filesystem, no networking, no hardware access from Python */
#define MICROPY_PY_OS                   (0)
#define MICROPY_PY_IO                   (1)
#define MICROPY_READER_VFS              (0)
#define MICROPY_VFS                     (0)
#define MICROPY_PY_SELECT               (0)
#define MICROPY_PY_SOCKET               (0)
#define MICROPY_PY_NETWORK              (0)
#define MICROPY_PY_MACHINE              (0)
#define MICROPY_PY_TIME                 (0)
#define MICROPY_PY_THREAD               (0)

/* newlib does not expose SSIZE_MAX in this configuration; ssize_t is 32-bit */
#define MP_SSIZE_MAX                    (0x7fffffff)

#define MICROPY_HW_BOARD_NAME           "Nintendo DSi"
#define MICROPY_HW_MCU_NAME             "ARM946E-S"
#define MICROPY_PY_SYS_PLATFORM         "nds"

/* No interactive console */
#define MICROPY_PY_BUILTINS_INPUT       (0)
#define MICROPY_PY_BUILTINS_HELP        (0)

#define MICROPY_PY_UCTYPES              (0)
#define MICROPY_PY_SYS_STDFILES         (1)  /* logging needs sys.stderr */

/* The ARM NLR assembly targets newer cores; use the portable setjmp version */
#define MICROPY_NLR_SETJMP              (1)

/* Modules for embit */
#define MICROPY_PY_BINASCII             (1)
#define MICROPY_PY_BINASCII_CRC32       (0)
#define MICROPY_PY_HASHLIB              (0)  /* replaced by lib/mpy-usermods/uhashlib */
#define MODULE_HASHLIB_ENABLED          (1)
#define MICROPY_PY_RANDOM               (0)  /* see frozen/random.py */
#define MICROPY_PY_COLLECTIONS          (1)
#define MICROPY_PY_COLLECTIONS_ORDEREDDICT (1)

/* Frozen bytecode (manifest.py). The build also passes these as -D when
 * generating the package; guard against redefinition. */
#ifndef MICROPY_MODULE_FROZEN_MPY
#define MICROPY_MODULE_FROZEN_MPY       (1)
#endif
#ifndef MICROPY_QSTR_EXTRA_POOL
#define MICROPY_QSTR_EXTRA_POOL         mp_qstr_frozen_const_pool
#endif
#define MICROPY_ENABLE_EXTERNAL_IMPORT  (1)

/* All Python output goes to the on-screen console and to the NO$GBA debug
 * channel (melonDS writes it to its log), see ndsport.c */
void nds_print_strn(const char *str, size_t len);
#define MP_PLAT_PRINT_STRN(str, len)    nds_print_strn(str, len)
#define MODULE_SECP256K1_ENABLED        (1)  /* lib/mpy-usermods/secp256k1 */
#define MICROPY_PY_JSON                 (1)  /* SeedSigner settings */
/* SeedSigner uses match.groups(); tests/host/test_re_compat compares with CPython */
#define MICROPY_PY_RE_MATCH_GROUPS      (1)
#define MICROPY_PY_RE_MATCH_SPAN_START_END (1)
#define MICROPY_PY_RE                   (1)  /* extended by frozen/compat/re.py */
#define MICROPY_PY_DEFLATE              (1)  /* zlib, BBQr */
