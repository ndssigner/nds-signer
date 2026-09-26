# NDS-Signer: MicroPython user C module wrapping libsecp256k1.
# Wrapper from diybitcoinhardware/secp256k1-embedded (MIT, ported to
# libsecp256k1 v0.8 by tools/port_mpy_usermod.py); the library itself is the
# pinned submodule third_party/secp256k1 (bitcoin-core, MIT).
SECP256K1_MOD_DIR := $(USERMOD_DIR)
SECP256K1_LIB_DIR := $(USERMOD_DIR)/../../../third_party/secp256k1

# Only the wrapper defines Python objects (and qstrs).
SRC_USERMOD += $(SECP256K1_MOD_DIR)/libsecp256k1.c
# Library sources: compiled by ports that use this file directly (unix port);
# the DSi build compiles them in mpy/Makefile with the same configuration.
SRC_USERMOD_LIB_C += $(SECP256K1_LIB_DIR)/src/secp256k1.c \
                     $(SECP256K1_LIB_DIR)/src/precomputed_ecmult.c \
                     $(SECP256K1_LIB_DIR)/src/precomputed_ecmult_gen.c \
                     $(SECP256K1_MOD_DIR)/config/ext_callbacks.c

CFLAGS_USERMOD += -I$(SECP256K1_LIB_DIR) -I$(SECP256K1_LIB_DIR)/src \
                  -DENABLE_MODULE_ECDH=1 -DENABLE_MODULE_RECOVERY=1 -DENABLE_MODULE_EXTRAKEYS=1 \
                  -DENABLE_MODULE_SCHNORRSIG=1 -DECMULT_WINDOW_SIZE=8 -DUSE_EXTERNAL_DEFAULT_CALLBACKS=1 \
                  -Wno-unused-function -Wno-pointer-sign
