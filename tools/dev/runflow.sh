#!/bin/sh
# dev helper: run a host MicroPython script (tests/host) with the ROM's module
# path, as tests/host/Makefile does (MPY_ROM_PATH), in the build container.
#   tools/dev/runflow.sh flow_check.py /source/tests/vectors <mode> [--gallery=DIR]
cd "$(dirname "$0")/../.."
MPY_LIB=/source/third_party/micropython/lib/micropython-lib/python-stdlib
P=/source/third_party/ur-tones/reference/python:/source/tests/host/sim:/source/mpy/frozen/compat:/source/mpy/frozen/hwstubs:/source/mpy/frozen:/source/build/frozen_py:/source/third_party/embit/src:/source/third_party/urtypes/src
for m in logging base64 zlib datetime; do P=$P:$MPY_LIB/$m; done
P=$P:/source/tests/vectors:/source/tests/host
exec docker run --rm -v "$(pwd)":/source -w /source/tests/host -e MICROPYPATH=$P nds-signer-builder \
	timeout 900 /source/build/mpy-unix/micropython "$@"
