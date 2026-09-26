# NDS-Signer: `unicodedata.normalize` for MicroPython, backed by utf8proc
# (third_party/utf8proc, MIT). SeedSigner normalizes mnemonics and BIP-39
# passphrases (NFKD/NFC); a wrong normalization would derive another seed.
UNICODEDATA_MOD_DIR := $(USERMOD_DIR)
UTF8PROC_DIR := $(USERMOD_DIR)/../../../third_party/utf8proc

SRC_USERMOD += $(UNICODEDATA_MOD_DIR)/modunicodedata.c
# utf8proc.c #includes utf8proc_data.c (the Unicode tables)
SRC_USERMOD_LIB_C += $(UTF8PROC_DIR)/utf8proc.c

CFLAGS_USERMOD += -I$(UTF8PROC_DIR) -DUTF8PROC_STATIC
