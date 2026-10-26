# Coverage-guided fuzzing of the ROM's C QR path (quirc + QR type detection)
# with libFuzzer, ASan and UBSan, in a container (any host with Docker):
#   make -C tests/fuzz run              each harness for FUZZ_TIME seconds
#   make -C tests/fuzz run FUZZ_TIME=3600 HARNESS=fuzz_image
# Crashes are written to tests/fuzz/build/<harness>-crash-*; the corpora grow
# in tests/fuzz/build/corpus/ (seeded from tests/vectors by make_corpus.py).
TOPDIR := $(abspath ../..)
FUZZ_TIME ?= 600
HARNESSES := fuzz_qr_type fuzz_decode fuzz_image
HARNESS ?= $(HARNESSES)
IMAGE := nds-signer-fuzz
PYTHON ?= $(TOPDIR)/build/venv/bin/python
DOCKER = docker run --rm -v $(TOPDIR):/source -w /source/tests/fuzz $(IMAGE)

QUIRC := ../../lib/quirc/decode.c ../../lib/quirc/identify.c ../../lib/quirc/quirc.c ../../lib/quirc/version_db.c
# as arm9/Makefile builds them for the ROM (QUIRC_DIV_ROUND: the portable
# division instead of the DS's hardware divider); float-cast-overflow is not
# checked, as in tests/host (upstream quirc casts NaN to int on degenerate grids)
CFLAGS := -std=gnu99 -O1 -g -fsanitize=fuzzer,address,undefined -fno-sanitize-recover=all \
          -fno-sanitize=float-cast-overflow \
          -DQUIRC_FIXED_POINT_GRID -DQUIRC_LAZY_JIGGLE \
          -I../../lib/quirc -I../../arm9/include

.PHONY: image build corpus run clean
image:
	docker build -q -t $(IMAGE) .

build: image
	$(DOCKER) make --no-print-directory $(addprefix build/,$(HARNESSES))

build/fuzz_qr_type: fuzz_qr_type.c ../../arm9/src/qr_type.c
	@mkdir -p build
	clang $(CFLAGS) -o $@ $^
build/fuzz_decode: fuzz_decode.c ../../arm9/src/qr_type.c $(QUIRC)
	@mkdir -p build
	clang $(CFLAGS) -o $@ $^ -lm
build/fuzz_image: fuzz_image.c ../../arm9/src/qr_type.c $(QUIRC)
	@mkdir -p build
	clang $(CFLAGS) -o $@ $^ -lm

corpus:
	$(PYTHON) make_corpus.py ../vectors build/corpus

run: build corpus
	@for h in $(HARNESS); do \
		echo "== $$h ($(FUZZ_TIME) s)"; \
		$(DOCKER) build/$$h -max_total_time=$(FUZZ_TIME) -print_final_stats=1 \
			-artifact_prefix=build/$$h- build/corpus/$$h || exit 1; \
	done

clean:
	rm -rf build
