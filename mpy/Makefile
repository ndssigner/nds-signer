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
             $(wildcard $(CURDIR)/usermods/*/*.c) \
             $(SECP256K1)/src/secp256k1.c $(SECP256K1)/src/precomputed_ecmult.c \
             $(SECP256K1)/src/precomputed_ecmult_gen.c \
             $(TOPDIR)/third_party/utf8proc/utf8proc.c
# libsecp256k1 configuration (same as lib/mpy-usermods/secp256k1/micropython.mk)
SECP_DEFS := -DENABLE_MODULE_ECDH=1 -DENABLE_MODULE_RECOVERY=1 -DENABLE_MODULE_EXTRAKEYS=1 \
             -DENABLE_MODULE_SCHNORRSIG=1 -DECMULT_WINDOW_SIZE=8 -DUSE_EXTERNAL_DEFAULT_CALLBACKS=1
CFLAGS    += -I$(USERMODS)/uhashlib/crypto -I$(SECP256K1) -I$(SECP256K1)/src $(SECP_DEFS) \
             -I$(TOPDIR)/arm9/include -I$(TOPDIR)/shared/include -I$(TOPDIR)/build/generated \
             -I$(TOPDIR)/third_party/utf8proc -DUTF8PROC_STATIC

# Upstream SeedSigner Python, transformed for MicroPython at build time
FROZEN_PY := $(TOPDIR)/build/frozen_py
SS_MODULES := $(shell grep -v '^\#' seedsigner_modules.txt)

OVERLAY := $(shell find overlay -name '*.py')

L10N := $(TOPDIR)/third_party/seedsigner/src/seedsigner/resources/seedsigner-translations/l10n

$(FROZEN_PY)/.stamp: seedsigner_modules.txt $(TOPDIR)/tools/upy_transform.py \
		$(TOPDIR)/tools/po_to_py.py $(TOPDIR)/tools/ttf_to_ndsfont.py $(wildcard $(TOPDIR)/l10n/*.po) $(wildcard $(L10N)/*/LC_MESSAGES/*.po) \
		$(shell find $(TOPDIR)/third_party/urtypes/src -name '*.py') $(wildcard $(TOPDIR)/tests/vectors/*.txt) \
		$(TOPDIR)/tools/gen_gui_api.py $(TOPDIR)/tools/screen_api.py $(OVERLAY) \
		$(addprefix $(TOPDIR)/third_party/seedsigner/src/,$(SS_MODULES))
	@echo transforming SeedSigner modules
	@rm -rf $(FROZEN_PY)
	@python3 $(TOPDIR)/tools/upy_transform.py --src $(TOPDIR)/third_party/seedsigner/src \
		--out $(FROZEN_PY) $(SS_MODULES)
	@# urtypes: insertion-ordered dicts so its CBOR output matches CPython's
	@python3 $(TOPDIR)/tools/upy_transform.py --ordered-dicts --no-new-rewrite \
		--src $(TOPDIR)/third_party/urtypes/src --out $(FROZEN_PY) \
		$$(cd $(TOPDIR)/third_party/urtypes/src && find urtypes -name '*.py' | sort)
	@# the overlay's helpers/ur2/__init__.py assumes upstream's is empty
	@test ! -s $(TOPDIR)/third_party/seedsigner/src/seedsigner/helpers/ur2/__init__.py || \
		{ echo "upstream helpers/ur2/__init__.py is no longer empty: merge it into the overlay"; exit 1; }
	@# SeedSigner's translations whose characters the UI fonts have
	@python3 $(TOPDIR)/tools/po_to_py.py $(L10N) $(FROZEN_PY) $(TOPDIR)/l10n | grep -v "^ok" || true
	@cp -R overlay/seedsigner $(FROZEN_PY)/
	@rm -f $(FROZEN_PY)/seedsigner/README.md
	@python3 $(TOPDIR)/tools/gen_gui_api.py $(TOPDIR)/third_party/seedsigner/src \
		$(FROZEN_PY)/seedsigner/gui/_upstream.py \
		$$(git -C $(TOPDIR)/third_party/seedsigner rev-parse --short HEAD 2>/dev/null)
	@python3 $(TOPDIR)/tools/freeze_vectors.py $(TOPDIR)/tests/vectors $(FROZEN_PY)/test_vectors.py
	@touch $@

$(EMBED)/.stamp: mpconfigport.h micropython_embed.mk manifest.py $(wildcard frozen/*.py frozen/*/*.py frozen/*/*/*.py) \
		$(USERMOD_C) $(FROZEN_PY)/.stamp
	@echo generating MicroPython embed package
	@rm -rf build-embed/frozen_content.c build-embed/frozen_mpy
	@NDS_AUTOTEST=$(AUTOTEST) NDS_DEVBUILD=$(DEVBUILD) NDS_AUTOPILOT=$(AUTOPILOT) $(MAKE) --no-print-directory -f micropython_embed.mk PACKAGE_DIR=$(EMBED) \
		CC=gcc CROSS_COMPILE= nds-embed-package >/dev/null
	@touch $@

$(LIB): $(EMBED)/.stamp $(wildcard *.c)
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
