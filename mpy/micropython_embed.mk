# NDS-Signer - generates the MicroPython embed package (C sources) from the
# pinned submodule. Invoked from mpy/Makefile, inside Docker.
MICROPYTHON_TOP = ../third_party/micropython

# C modules (lib/mpy-usermods/*/micropython.mk) and frozen Python (manifest.py)
USER_C_MODULES = $(CURDIR)/../lib/mpy-usermods
FROZEN_MANIFEST = $(CURDIR)/manifest.py
MICROPY_MANIFEST_PORT_DIR = $(CURDIR)

# extmod modules used by embit; the embed port only ships py/. They must be
# added to SRC_QSTR before the core rules are included.
EXTMOD_SRC = extmod/modbinascii.c extmod/modjson.c extmod/modre.c extmod/moddeflate.c
# C libraries #included by those modules
EXTMOD_LIBS = lib/re1.5 lib/uzlib
SHARED_SRC = shared/runtime/sys_stdio_mphal.c
SRC_QSTR += $(addprefix $(MICROPYTHON_TOP)/,$(EXTMOD_SRC) $(SHARED_SRC))

include $(MICROPYTHON_TOP)/ports/embed/embed.mk

# The embed package plus what embed.mk does not copy: extmod modules and the
# frozen bytecode.
.PHONY: nds-embed-package
nds-embed-package: micropython-embed-package $(BUILD)/frozen_content.c
	$(Q)$(CP) $(addprefix $(TOP)/,$(EXTMOD_SRC)) $(PACKAGE_DIR)/extmod/
	$(Q)$(CP) $(addprefix $(TOP)/,$(SHARED_SRC)) $(PACKAGE_DIR)/shared/runtime/
	$(Q)$(MKDIR) -p $(PACKAGE_DIR)/lib
	$(Q)$(CP) -r $(addprefix $(TOP)/,$(EXTMOD_LIBS)) $(PACKAGE_DIR)/lib/
	$(Q)$(CP) $(BUILD)/frozen_content.c $(PACKAGE_DIR)/port/
