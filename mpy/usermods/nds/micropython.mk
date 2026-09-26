# NDS-Signer native module `nds`: DSi hardware for the Python app (camera/QR
# scanning, text screens, keys, touch). DSi build only; host tests use the
# pure-Python simulator tests/host/sim/nds.py instead.
NDS_MOD_DIR := $(USERMOD_DIR)
SRC_USERMOD += $(NDS_MOD_DIR)/modnds.c


# The module only includes arm9/include/nds_bridge.h (plain C, no libnds), so
# the host preprocessor used for the qstr scan can read it.
CFLAGS_USERMOD += -I$(NDS_MOD_DIR)/../../../arm9/include
