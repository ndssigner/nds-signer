# NDS-Signer - generates the MicroPython embed package (C sources) from the
# pinned submodule. Invoked from the top-level Makefile, inside Docker.
MICROPYTHON_TOP = ../third_party/micropython
include $(MICROPYTHON_TOP)/ports/embed/embed.mk
