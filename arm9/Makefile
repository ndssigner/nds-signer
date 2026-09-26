#---------------------------------------------------------------------------------
# NDS-Signer - ARM9 core: application, UI and (later) PSBT / crypto logic.
# Built from the top-level Makefile; see ../Makefile.
#---------------------------------------------------------------------------------
.SUFFIXES:
#---------------------------------------------------------------------------------

ifeq ($(strip $(DEVKITARM)),)
$(error "Please set DEVKITARM in your environment. export DEVKITARM=<path to>devkitARM")
endif

include $(DEVKITARM)/ds_rules

#---------------------------------------------------------------------------------
# BUILD    : directory for object files & intermediates
# SOURCES  : directories containing source code
# INCLUDES : directories containing extra header files
# DATA     : directories containing binary files embedded with bin2o
#---------------------------------------------------------------------------------
BUILD    := build
SOURCES  := src ../lib/quirc ../lib/qrcodegen ../build/generated
INCLUDES := include ../shared/include ../lib/quirc ../lib/qrcodegen
DATA     := data

#---------------------------------------------------------------------------------
# Code generation options
#---------------------------------------------------------------------------------
ARCH := -march=armv5te -mtune=arm946e-s

# -ffile-prefix-map keeps absolute host paths out of the binary (reproducibility)
CFLAGS   := -std=gnu99 -g -Wall -Wextra -O2 -ffunction-sections -fdata-sections \
            -ffile-prefix-map=$(TOPDIR)=. \
            $(ARCH) $(INCLUDE) -DARM9 \
            -DQUIRC_FLOAT_TYPE=float -DQUIRC_USE_TGMATH \
            -I$(TOPDIR)/mpy -I$(TOPDIR)/build/micropython_embed
# Development only: `make AUTOTEST=1` boots straight into the scanner so the
# emulator can be driven without input. Never use for release builds.
ifneq ($(strip $(AUTOTEST)),)
CFLAGS   += -DNDS_SIGNER_AUTOTEST
endif
# SPIKE: `make MPY_SPIKE=1` boots into the MicroPython benchmark screen
ifneq ($(strip $(MPY_SPIKE)),)
CFLAGS   += -DNDS_SIGNER_MPY_SPIKE
endif
# SPIKE: `make MPY_APP=1` runs the Python app (SeedSigner Controller)
ifneq ($(strip $(MPY_APP)),)
CFLAGS   += -DNDS_SIGNER_MPY_APP
endif
CXXFLAGS := $(CFLAGS) -fno-rtti -fno-exceptions
ASFLAGS  := -g $(ARCH)
LDFLAGS   = -specs=ds_arm9.specs -g $(ARCH) -Wl,--gc-sections -Wl,-Map,$(notdir $*).map \
            -L$(TOPDIR)/build

# NOTE: dswifi / libfat are deliberately NOT linked. The signer is air-gapped
# and stateless: it must never touch the network or the SD card.
LIBS := -lmicropython -lnds9 -lm

LIBDIRS := $(LIBNDS) $(PORTLIBS)

#---------------------------------------------------------------------------------
# No real need to edit anything past this point
#---------------------------------------------------------------------------------
ifneq ($(BUILD),$(notdir $(CURDIR)))
#---------------------------------------------------------------------------------

export ARM9ELF := $(CURDIR)/$(TARGET).elf
export DEPSDIR := $(CURDIR)/$(BUILD)

export VPATH := $(foreach dir,$(SOURCES),$(CURDIR)/$(dir)) \
                $(foreach dir,$(DATA),$(CURDIR)/$(dir))

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

.PHONY: $(BUILD) clean

#---------------------------------------------------------------------------------
$(BUILD):
	@mkdir -p $@
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

#---------------------------------------------------------------------------------
clean:
	@echo clean ...
	@rm -fr $(BUILD) $(TARGET).elf

#---------------------------------------------------------------------------------
else
#---------------------------------------------------------------------------------

$(ARM9ELF): $(OFILES)

# source files depend on generated headers
$(OFILES_SOURCES): $(HFILES)

# Vendored third-party code is kept unmodified: silence -Wextra noise there only
decode.o identify.o quirc.o version_db.o qrcodegen.o: \
	CFLAGS += -Wno-unused-parameter -Wno-sign-compare -Wno-type-limits

#---------------------------------------------------------------------------------
%.bin.o %_bin.h: %.bin
#---------------------------------------------------------------------------------
	@echo $(notdir $<)
	@$(bin2o)

-include $(DEPSDIR)/*.d

#---------------------------------------------------------------------------------
endif
#---------------------------------------------------------------------------------
