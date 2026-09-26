# Host-side tests (run on the development machine or CI).
#   make -C tests/host            C unit tests (qr_type)
#   make -C tests/host re-compat  MicroPython `re` compat vs CPython (Docker)
CC     ?= cc
CFLAGS := -std=gnu99 -Wall -Wextra -Werror -g -fsanitize=address,undefined \
          -I../../arm9/include

TOPDIR := $(abspath ../..)
DOCKER_MPY = docker run --rm -v "$(TOPDIR)":/source -w /source/tests/host \
             -e MICROPYPATH=/source/mpy/frozen/compat:/source/tests/host \
             nds-signer-builder /source/build/mpy-unix/micropython

.PHONY: all clean re-compat
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

clean:
	rm -rf test_qr_type test_qr_type.dSYM
