# NDS-Signer: MicroPython user C module wrapping libsecp256k1.
# Wrapper from diybitcoinhardware/secp256k1-embedded (MIT); the library itself
# is the pinned submodule third_party/secp256k1 (bitcoin-core, MIT).
SECP256K1_MOD_DIR := $(USERMOD_DIR)
SECP256K1_LIB_DIR := $(USERMOD_DIR)/../../../third_party/secp256k1

# Only the wrapper defines Python objects (and qstrs); the library sources are
# compiled by mpy/Makefile.
SRC_USERMOD += $(SECP256K1_MOD_DIR)/libsecp256k1.c

CFLAGS_USERMOD += -I$(SECP256K1_LIB_DIR) -I$(SECP256K1_LIB_DIR)/src \
                  -I$(SECP256K1_MOD_DIR)/config -DHAVE_CONFIG_H
