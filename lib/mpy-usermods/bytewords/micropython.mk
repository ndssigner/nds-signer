# NDS-Signer: native inner loop of SeedSigner's Bytewords "minimal" decoding
# (helpers/ur2/bytewords.py), the hot spot when scanning animated UR QR codes.
BYTEWORDS_MOD_DIR := $(USERMOD_DIR)
SRC_USERMOD += $(BYTEWORDS_MOD_DIR)/modbytewords.c
