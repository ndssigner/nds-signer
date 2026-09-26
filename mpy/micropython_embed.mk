# NDS-Signer - generates the MicroPython embed package (C sources) from the
# pinned submodule. Invoked from mpy/Makefile, inside Docker.
MICROPYTHON_TOP = ../third_party/micropython

# C modules (lib/mpy-usermods/*/micropython.mk) and frozen Python (manifest.py)
USER_C_MODULES = $(CURDIR)/../lib/mpy-usermods
FROZEN_MANIFEST = $(CURDIR)/manifest.py
MICROPY_MANIFEST_PORT_DIR = $(CURDIR)

# extmod modules used by embit; the embed port only ships py/. They must be
# added to SRC_QSTR before the core rules are included.
EXTMOD_SRC = extmod/modbinascii.c
SRC_QSTR += $(addprefix $(MICROPYTHON_TOP)/,$(EXTMOD_SRC))

include $(MICROPYTHON_TOP)/ports/embed/embed.mk

# The embed package plus what embed.mk does not copy: extmod modules and the
# frozen bytecode.
.PHONY: nds-embed-package
nds-embed-package: micropython-embed-package $(BUILD)/frozen_content.c
	$(Q)$(CP) $(addprefix $(TOP)/,$(EXTMOD_SRC)) $(PACKAGE_DIR)/extmod/
	$(Q)$(CP) $(BUILD)/frozen_content.c $(PACKAGE_DIR)/port/
