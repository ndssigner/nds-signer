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
#define MICROPY_PY_SYS_STDFILES         (0)

/* The ARM NLR assembly targets newer cores; use the portable setjmp version */
#define MICROPY_NLR_SETJMP              (1)
