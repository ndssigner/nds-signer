#---------------------------------------------------------------------------------
# NDS-Signer - MicroPython as a static library for the ARM9 (SPIKE)
#
# 1. Generates the embed package from third_party/micropython (pinned submodule)
# 2. Compiles it with the ARM9 flags into $(LIBDIR)/libmicropython.a
# Invoked from the top-level Makefile, inside the builder Docker image.
#---------------------------------------------------------------------------------
ifeq ($(strip $(DEVKITARM)),)
$(error "Please set DEVKITARM in your environment. export DEVKITARM=<path to>devkitARM")
endif
include $(DEVKITARM)/base_rules

TOPDIR   ?= $(CURDIR)/..
EMBED    := $(TOPDIR)/build/micropython_embed
OBJDIR   := $(TOPDIR)/build/micropython_obj
LIBDIR   := $(TOPDIR)/build
LIB      := $(LIBDIR)/libmicropython.a

ARCH     := -march=armv5te -mtune=arm946e-s
CFLAGS   := -std=gnu99 -O2 -g -ffunction-sections -fdata-sections $(ARCH) -DARM9 \
            -ffile-prefix-map=$(TOPDIR)=. \
            -I$(CURDIR) -I$(EMBED) -I$(DEVKITPRO)/libnds/include -I$(DEVKITPRO)/calico/include

.PHONY: all clean
all: $(LIB)

# The package is regenerated when the configuration changes. The generator
# needs a host compiler/Python, both present in the builder image.
USERMODS  := $(TOPDIR)/lib/mpy-usermods
SECP256K1 := $(TOPDIR)/third_party/secp256k1
USERMOD_C := $(wildcard $(USERMODS)/*/*.c $(USERMODS)/*/crypto/*.c $(USERMODS)/*/config/*.c) \
             $(SECP256K1)/src/secp256k1.c
SECP_GEN  := $(TOPDIR)/build/secp256k1_gen
CFLAGS    += -I$(USERMODS)/uhashlib/crypto \
             -I$(SECP256K1) -I$(SECP256K1)/src -I$(USERMODS)/secp256k1/config -DHAVE_CONFIG_H \
             -I$(SECP_GEN)

# libsecp256k1's precomputed generator table, built with its own host tool
$(SECP_GEN)/src/ecmult_static_context.h: $(SECP256K1)/src/gen_context.c
	@echo generating secp256k1 static context
	@mkdir -p $(SECP_GEN)/src
	@gcc -O2 -I$(SECP256K1) -I$(SECP256K1)/src -DECMULT_GEN_PREC_BITS=4 $< -o $(SECP_GEN)/gen_context
	@cd $(SECP_GEN) && ./gen_context

# Upstream SeedSigner Python, transformed for MicroPython at build time
FROZEN_PY := $(TOPDIR)/build/frozen_py
SS_MODULES := $(shell grep -v '^\#' seedsigner_modules.txt)

$(FROZEN_PY)/.stamp: seedsigner_modules.txt $(TOPDIR)/tools/upy_transform.py \
		$(addprefix $(TOPDIR)/third_party/seedsigner/src/,$(SS_MODULES))
	@echo transforming SeedSigner modules
	@rm -rf $(FROZEN_PY)
	@python3 $(TOPDIR)/tools/upy_transform.py --src $(TOPDIR)/third_party/seedsigner/src \
		--out $(FROZEN_PY) $(SS_MODULES)
	@touch $@

$(EMBED)/.stamp: mpconfigport.h micropython_embed.mk manifest.py $(wildcard frozen/*.py frozen/*/*.py) \
		$(USERMOD_C) $(FROZEN_PY)/.stamp
	@echo generating MicroPython embed package
	@$(MAKE) --no-print-directory -f micropython_embed.mk PACKAGE_DIR=$(EMBED) \
		CC=gcc CROSS_COMPILE= nds-embed-package >/dev/null
	@touch $@

$(LIB): $(EMBED)/.stamp $(wildcard *.c) $(SECP_GEN)/src/ecmult_static_context.h
	@mkdir -p $(OBJDIR)
	@echo compiling MicroPython
	@for f in $$(cd $(EMBED) && find py shared port extmod -name '*.c'); do \
		o=$(OBJDIR)/$$(echo $$f | tr / _ | sed 's/\.c$$/.o/'); \
		$(CC) $(CFLAGS) -c $(EMBED)/$$f -o $$o || exit 1; \
	done
	@for f in *.c; do \
		$(CC) $(CFLAGS) -Wall -c $$f -o $(OBJDIR)/nds_$${f%.c}.o || exit 1; \
	done
	@for f in $(USERMOD_C); do \
		o=$(OBJDIR)/usermod_$$(basename $${f%.c}).o; \
		$(CC) $(CFLAGS) -c $$f -o $$o || exit 1; \
	done
	@rm -f $@
	@$(AR) rcs $@ $(OBJDIR)/*.o
	@echo built ... $(notdir $@)

clean:
	@rm -rf $(EMBED) $(OBJDIR) $(LIB) $(SECP_GEN) $(FROZEN_PY) build-embed
