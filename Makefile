#---------------------------------------------------------------------------------
# NDS-Signer - top-level Makefile (custom ARM7 + ARM9)
# Based on the devkitPro combined template ($(DEVKITPRO)/examples/nds/templates/combined)
#
# A custom ARM7 core is used so that the Wi-Fi, SD/NAND and sound drivers are
# never even linked into the binary, and to drive the DSi cameras over I2C.
#
# Build inside the pinned Docker image for reproducible output:
#   docker build -t nds-signer-builder .
#   docker run --rm -v "$(pwd)":/source nds-signer-builder make
#---------------------------------------------------------------------------------
.SUFFIXES:
#---------------------------------------------------------------------------------

ifeq ($(strip $(DEVKITARM)),)
$(error "Please set DEVKITARM in your environment. export DEVKITARM=<path to>devkitARM")
endif

export TARGET := nds-signer
# Version string for screens and reports, the same in any clone (full,
# shallow, with or without tags), so the build stays reproducible: a release
# tag (v*) when building exactly that tag, else dev-<12 hex of the commit>;
# -dirty with uncommitted changes. (git inside the builder container sees a
# repo owned by another user, hence safe.directory.)
GIT := git -c safe.directory='*'
export NDS_VERSION := $(shell $(GIT) describe --tags --exact-match --match 'v*' 2>/dev/null || \
	echo dev-$$($(GIT) rev-parse HEAD 2>/dev/null | cut -c1-12))$(shell $(GIT) diff --quiet HEAD -- 2>/dev/null || echo -dirty)
export TOPDIR := $(CURDIR)

# Banner text shown by TWiLight Menu++ / the DSi menu: just the name (the
# console's menu need not say what the app is for). The other two lines are
# a space: left empty, ndstool would fill in its own text.
GAME_TITLE     := NDS-Signer
GAME_ICON      := build/generated/icon.bmp

include $(DEVKITARM)/ds_rules

.PHONY: checkarm7 checkarm9 checkmpy clean mpy-unix fonts

#---------------------------------------------------------------------------------
all: checkarm7 checkmpy checkarm9 $(TARGET).nds

# MicroPython static library (SPIKE, see docs/architecture.md); the nds
# module needs the generated font ids (gfx_fonts.h)
checkmpy: fonts
	$(MAKE) -C mpy TOPDIR=$(TOPDIR)

checkarm7:
	$(MAKE) -C arm7

checkarm9: checkmpy fonts
	$(MAKE) -C arm9

# Console font generated from the vendored BDF (lib/fonts)
fonts: build/generated/nds_font.c build/generated/gfx_fonts.c
build/generated/nds_font.c: lib/fonts/spleen-5x8.bdf tools/bdf_to_ndsfont.py
	@mkdir -p build/generated
	python3 tools/bdf_to_ndsfont.py $< $@

# Graphical UI fonts: SeedSigner's own, rasterized (Pillow pinned in the image)
build/generated/gfx_fonts.c: tools/ttf_to_ndsfont.py \
		$(wildcard third_party/seedsigner/src/seedsigner/resources/fonts/*) \
		third_party/seedsigner/src/seedsigner/gui/components.py
	@mkdir -p build/generated
	python3 tools/ttf_to_ndsfont.py third_party/seedsigner/src $@ build/generated/gfx_fonts.h
	@# (also writes build/generated/gfx_advances.json for the host simulator)

# Menu icon: SeedSigner's "sign" icon on an orange tile (tools/make_icon.py)
$(GAME_ICON): tools/make_icon.py third_party/seedsigner/src/seedsigner/resources/fonts/seedsigner-icons.otf
	@mkdir -p build/generated
	python3 tools/make_icon.py third_party/seedsigner/src $@

$(TARGET).nds: arm7/$(TARGET).elf arm9/$(TARGET).elf $(GAME_ICON)
	ndstool -c $(TARGET).nds -7 arm7/$(TARGET).elf -9 arm9/$(TARGET).elf \
	-b $(GAME_ICON) "$(GAME_TITLE); ; "
	@echo built ... $(notdir $@)

arm7/$(TARGET).elf:
	$(MAKE) -C arm7

arm9/$(TARGET).elf:
	$(MAKE) -C arm9

#---------------------------------------------------------------------------------
# MicroPython unix port with the same `re` options as the ROM, used by the
# host tests (make -C tests/host re-compat). Run inside the builder image.
# It includes the same native modules (lib/mpy-usermods) as the ROM.
mpy-unix:
	$(MAKE) -C third_party/micropython/mpy-cross
	$(MAKE) -C third_party/micropython/ports/unix BUILD=$(TOPDIR)/build/mpy-unix PROG=micropython \
		MICROPY_PY_FFI=0 MICROPY_PY_BTREE=0 MICROPY_PY_SSL=0 MICROPY_USE_READLINE=0 \
		USER_C_MODULES=$(TOPDIR)/lib/mpy-usermods \
		CFLAGS_EXTRA="-DMICROPY_PY_RE_MATCH_GROUPS=1 -DMICROPY_PY_RE_MATCH_SPAN_START_END=1 \
		              -DMODULE_HASHLIB_ENABLED=1 -DMODULE_SECP256K1_ENABLED=1"

#---------------------------------------------------------------------------------
clean:
	$(MAKE) -C arm9 clean
	$(MAKE) -C arm7 clean
	$(MAKE) -C mpy clean TOPDIR=$(TOPDIR)
	rm -f $(TARGET).nds
