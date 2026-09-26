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
export TOPDIR := $(CURDIR)

# Banner text shown by TWiLight Menu++ / the DSi menu
GAME_TITLE     := NDS-Signer
GAME_SUBTITLE1 := Air-gapped Bitcoin PSBT signer
GAME_SUBTITLE2 := github.com/nds-signer
GAME_ICON      :=

include $(DEVKITARM)/ds_rules

.PHONY: checkarm7 checkarm9 checkmpy clean

#---------------------------------------------------------------------------------
all: checkarm7 checkmpy checkarm9 $(TARGET).nds

# MicroPython static library (SPIKE, see docs/architecture.md)
checkmpy:
	$(MAKE) -C mpy TOPDIR=$(TOPDIR)

checkarm7:
	$(MAKE) -C arm7

checkarm9: checkmpy
	$(MAKE) -C arm9

$(TARGET).nds: arm7/$(TARGET).elf arm9/$(TARGET).elf
	ndstool -c $(TARGET).nds -7 arm7/$(TARGET).elf -9 arm9/$(TARGET).elf \
	-b $(GAME_ICON) "$(GAME_TITLE);$(GAME_SUBTITLE1);$(GAME_SUBTITLE2)"
	@echo built ... $(notdir $@)

arm7/$(TARGET).elf:
	$(MAKE) -C arm7

arm9/$(TARGET).elf:
	$(MAKE) -C arm9

#---------------------------------------------------------------------------------
clean:
	$(MAKE) -C arm9 clean
	$(MAKE) -C arm7 clean
	$(MAKE) -C mpy clean TOPDIR=$(TOPDIR)
	rm -f $(TARGET).nds
