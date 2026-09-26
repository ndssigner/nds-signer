# Host-side tests (run on the development machine or CI).
#   make -C tests/host            C unit tests (qr_type)
#   make -C tests/host re-compat  MicroPython `re` compat vs CPython (Docker)
#   make -C tests/host seedsigner SeedSigner/embit on MicroPython vs CPython refs,
#                                 incl. the full Scan -> review -> sign UI flow
CC     ?= cc
# CPython with embit==0.8.0 and urtypes (tests/requirements.txt) for references
PYTHON ?= python3
CFLAGS := -std=gnu99 -Wall -Wextra -Werror -g -fsanitize=address,undefined \
          -I../../arm9/include

TOPDIR := $(abspath ../..)
DOCKER_MPY = docker run --rm -v "$(TOPDIR)":/source -w /source/tests/host \
             -e MICROPYPATH=/source/mpy/frozen/compat:/source/tests/host \
             nds-signer-builder /source/build/mpy-unix/micropython

# Same module search path as the frozen ROM contents (see mpy/manifest.py)
MPY_LIB = /source/third_party/micropython/lib/micropython-lib/python-stdlib
MPY_ROM_PATH = /source/tests/host/sim:/source/mpy/frozen/compat:/source/mpy/frozen/hwstubs:/source/mpy/frozen:/source/build/frozen_py:/source/third_party/embit/src:/source/third_party/urtypes/src:$(MPY_LIB)/logging:$(MPY_LIB)/base64:$(MPY_LIB)/zlib:$(MPY_LIB)/datetime:/source/tests/vectors:/source/tests/host
DOCKER_MPY_ROM = docker run --rm -v "$(TOPDIR)":/source -w /source/tests/host \
             -e MICROPYPATH=$(MPY_ROM_PATH) nds-signer-builder /source/build/mpy-unix/micropython

.PHONY: all clean re-compat seedsigner qrdecode
all: test_qr_type
	./test_qr_type

test_qr_type: test_qr_type.c ../../arm9/src/qr_type.c ../../arm9/include/qr_type.h
	$(CC) $(CFLAGS) -o $@ test_qr_type.c ../../arm9/src/qr_type.c

# Requires the MicroPython unix port: make -C ../.. mpy-unix
re-compat:
	@for t in re_compat_run re_compat_fuzz; do \
		python3 $$t.py > $(TOPDIR)/build/$$t.cpython.txt; \
		$(DOCKER_MPY) $$t.py > $(TOPDIR)/build/$$t.mpy.txt; \
		diff -q $(TOPDIR)/build/$$t.cpython.txt $(TOPDIR)/build/$$t.mpy.txt >/dev/null \
			&& echo "ok   $$t ($$(wc -l < $(TOPDIR)/build/$$t.cpython.txt | tr -d ' ') lines identical)" \
			|| { echo "FAIL $$t"; diff $(TOPDIR)/build/$$t.cpython.txt $(TOPDIR)/build/$$t.mpy.txt | head -20; exit 1; }; \
	done

# Requires `make mpy-unix` and a ROM build (for build/frozen_py) in Docker
seedsigner:
	$(DOCKER_MPY_ROM) seedsigner_check.py /source/tests/vectors
	@PYTHONPATH=$(TOPDIR)/third_party/seedsigner/src:$(TOPDIR)/mpy/frozen/hwstubs $(PYTHON) decode_qr_check.py $(TOPDIR)/tests/vectors \
		> $(TOPDIR)/build/decode_qr.cpython.txt
	@$(DOCKER_MPY_ROM) decode_qr_check.py /source/tests/vectors > $(TOPDIR)/build/decode_qr.mpy.txt
	@diff $(TOPDIR)/build/decode_qr.cpython.txt $(TOPDIR)/build/decode_qr.mpy.txt \
		&& echo "ok   DecodeQR ($$(wc -l < $(TOPDIR)/build/decode_qr.cpython.txt | tr -d ' ') payloads identical)"
	@$(DOCKER_MPY_ROM) flow_check.py /source/tests/vectors 2>/dev/null | grep -E "^(ok|FAIL)|PASSED|FAILED"

# Host QR decoder (same quirc as the ROM) for emulator screenshots:
#   tools/png_to_pgm.py shot.png | ../../build/qrdecode
qrdecode: ../../build/qrdecode
../../build/qrdecode: qrdecode.c
	$(CC) -O2 -I../../lib/quirc -o $@ qrdecode.c ../../lib/quirc/*.c -lm

clean:
	rm -rf test_qr_type test_qr_type.dSYM
