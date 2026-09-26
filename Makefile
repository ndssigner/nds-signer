#---------------------------------------------------------------------------------
# NDS-Signer - libnds (calico) ARM9 project Makefile
# Based on the devkitPro arm9 template ($(DEVKITPRO)/examples/nds/templates/arm9)
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

# Banner text shown by TWiLight Menu++ / the DSi menu
GAME_TITLE     := NDS-Signer
GAME_SUBTITLE1 := Air-gapped Bitcoin PSBT signer
GAME_SUBTITLE2 := github.com/nds-signer

include $(DEVKITARM)/ds_rules

#---------------------------------------------------------------------------------
# TARGET   : name of the output (.elf / .nds)
# BUILD    : directory for object files & intermediates
# SOURCES  : directories containing source code
# INCLUDES : directories containing extra header files
# DATA     : directories containing binary files embedded with bin2o
#---------------------------------------------------------------------------------
TARGET   := nds-signer
BUILD    := build
SOURCES  := src
INCLUDES := include
DATA     := data
ICON     :=

#---------------------------------------------------------------------------------
# Code generation options
#---------------------------------------------------------------------------------
ARCH := -march=armv5te -mtune=arm946e-s

# -ffile-prefix-map keeps absolute host paths out of the binary (reproducibility)
CFLAGS   := -std=gnu99 -g -Wall -Wextra -O2 -ffunction-sections -fdata-sections \
            -ffile-prefix-map=$(CURDIR)=. \
            $(ARCH) $(INCLUDE) -DARM9
CXXFLAGS := $(CFLAGS) -fno-rtti -fno-exceptions
ASFLAGS  := -g $(ARCH)
LDFLAGS   = -specs=ds_arm9.specs -g $(ARCH) -Wl,--gc-sections -Wl,-Map,$(notdir $*.map)

#---------------------------------------------------------------------------------
# Libraries to link with (order is important).
# NOTE: dswifi is deliberately NOT linked. The signer must stay air-gapped.
#---------------------------------------------------------------------------------
LIBS := -lnds9

LIBDIRS := $(LIBNDS) $(PORTLIBS)

#---------------------------------------------------------------------------------
# No real need to edit anything past this point
#---------------------------------------------------------------------------------
ifneq ($(BUILD),$(notdir $(CURDIR)))
#---------------------------------------------------------------------------------

export OUTPUT := $(CURDIR)/$(TARGET)

export VPATH := $(foreach dir,$(SOURCES),$(CURDIR)/$(dir)) \
                $(foreach dir,$(DATA),$(CURDIR)/$(dir))

export DEPSDIR := $(CURDIR)/$(BUILD)

CFILES   := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))
CPPFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.cpp)))
SFILES   := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.s)))
BINFILES := $(foreach dir,$(DATA),$(notdir $(wildcard $(dir)/*.bin)))

ifeq ($(strip $(CPPFILES)),)
  export LD := $(CC)
else
  export LD := $(CXX)
endif

export OFILES_BIN     := $(addsuffix .o,$(BINFILES))
export OFILES_SOURCES := $(CPPFILES:.cpp=.o) $(CFILES:.c=.o) $(SFILES:.s=.o)
export OFILES         := $(OFILES_BIN) $(OFILES_SOURCES)
export HFILES         := $(addsuffix .h,$(subst .,_,$(BINFILES)))

export INCLUDE  := $(foreach dir,$(INCLUDES),-iquote $(CURDIR)/$(dir)) \
                   $(foreach dir,$(LIBDIRS),-I$(dir)/include) \
                   -I$(CURDIR)/$(BUILD)
export LIBPATHS := $(foreach dir,$(LIBDIRS),-L$(dir)/lib)

ifneq ($(strip $(ICON)),)
  export GAME_ICON := $(CURDIR)/$(ICON)
else ifneq (,$(wildcard icon.bmp))
  export GAME_ICON := $(CURDIR)/icon.bmp
endif

.PHONY: $(BUILD) clean

#---------------------------------------------------------------------------------
$(BUILD):
	@mkdir -p $@
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

#---------------------------------------------------------------------------------
clean:
	@echo clean ...
	@rm -fr $(BUILD) $(TARGET).elf $(TARGET).nds

#---------------------------------------------------------------------------------
else
#---------------------------------------------------------------------------------

$(OUTPUT).nds: $(OUTPUT).elf $(GAME_ICON)
$(OUTPUT).elf: $(OFILES)

# source files depend on generated headers
$(OFILES_SOURCES): $(HFILES)

#---------------------------------------------------------------------------------
%.bin.o %_bin.h: %.bin
#---------------------------------------------------------------------------------
	@echo $(notdir $<)
	@$(bin2o)

-include $(DEPSDIR)/*.d

#---------------------------------------------------------------------------------
endif
#---------------------------------------------------------------------------------
