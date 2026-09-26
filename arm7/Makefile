#---------------------------------------------------------------------------------
# NDS-Signer - ARM7 core: keypad, touch, power management and DSi camera (I2C) only.
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
SOURCES  := src
INCLUDES := include ../shared/include
DATA     := 

#---------------------------------------------------------------------------------
# Code generation options
#---------------------------------------------------------------------------------
ARCH := -march=armv4t -mtune=arm7tdmi -mthumb

# -ffile-prefix-map keeps absolute host paths out of the binary (reproducibility)
CFLAGS   := -std=gnu99 -g -Wall -Wextra -Os -ffunction-sections -fdata-sections \
            -ffile-prefix-map=$(TOPDIR)=. \
            $(ARCH) $(INCLUDE) -DARM7
CXXFLAGS := $(CFLAGS) -fno-rtti -fno-exceptions
ASFLAGS  := -g $(ARCH)
LDFLAGS   = -specs=ds_arm7.specs -g $(ARCH) -Wl,--gc-sections -Wl,-Map,$(notdir $*).map

# Only libnds + calico: no dswifi, no maxmod, no filesystem.
LIBS := -lnds7

LIBDIRS := $(LIBNDS)

#---------------------------------------------------------------------------------
# No real need to edit anything past this point
#---------------------------------------------------------------------------------
ifneq ($(BUILD),$(notdir $(CURDIR)))
#---------------------------------------------------------------------------------

export ARM7ELF := $(CURDIR)/$(TARGET).elf
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

$(ARM7ELF): $(OFILES)

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
