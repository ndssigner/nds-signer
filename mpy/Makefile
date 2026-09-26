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
$(EMBED)/.stamp: mpconfigport.h micropython_embed.mk
	@echo generating MicroPython embed package
	@$(MAKE) --no-print-directory -f micropython_embed.mk PACKAGE_DIR=$(EMBED) \
		CC=gcc CROSS_COMPILE= >/dev/null
	@touch $@

$(LIB): $(EMBED)/.stamp $(wildcard *.c)
	@mkdir -p $(OBJDIR)
	@echo compiling MicroPython
	@for f in $$(cd $(EMBED) && find py shared port -name '*.c'); do \
		o=$(OBJDIR)/$$(echo $$f | tr / _ | sed 's/\.c$$/.o/'); \
		$(CC) $(CFLAGS) -c $(EMBED)/$$f -o $$o || exit 1; \
	done
	@for f in *.c; do \
		$(CC) $(CFLAGS) -Wall -c $$f -o $(OBJDIR)/nds_$${f%.c}.o || exit 1; \
	done
	@rm -f $@
	@$(AR) rcs $@ $(OBJDIR)/*.o
	@echo built ... $(notdir $@)

clean:
	@rm -rf $(EMBED) $(OBJDIR) $(LIB) build-embed
