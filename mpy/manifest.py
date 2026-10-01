# NDS-Signer - MicroPython frozen modules manifest (SPIKE)
#
# Upstream Python frozen unmodified into the ROM as bytecode (mpy-cross).
# See docs/architecture.md.

# Reproducible builds: MicroPython's package()/require() walk directories with
# os.walk, whose order depends on the filesystem (macOS and Linux differ), and
# the frozen modules land in the ROM in that order. Walk in sorted order.
import os as _os

_os_walk = _os.walk


def _sorted_walk(top, *args, **kwargs):
    for root, dirs, files in _os_walk(top, *args, **kwargs):
        dirs.sort()
        files.sort()
        yield root, dirs, files


_os.walk = _sorted_walk

# embit (SeedSigner's pinned version), minus the Liquid sidechain support and
# the CPython-only ctypes backend.
package(
    "embit",
    files=[
        "__init__.py",
        "base.py",
        "base58.py",
        "bech32.py",
        "bip32.py",
        "bip39.py",
        "bip85.py",
        "compact.py",
        "descriptor/__init__.py",
        "descriptor/arguments.py",
        "descriptor/base.py",
        "descriptor/checksum.py",
        "descriptor/descriptor.py",
        "descriptor/errors.py",
        "descriptor/miniscript.py",
        "descriptor/taptree.py",
        "ec.py",
        "finalizer.py",
        "hashes.py",
        "misc.py",
        "networks.py",
        "psbt.py",
        "psbtview.py",
        "script.py",
        "slip39.py",
        "transaction.py",
        "util/__init__.py",
        "util/key.py",
        "util/py_ripemd160.py",
        "util/py_secp256k1.py",
        "util/secp256k1.py",
        "wordlists/__init__.py",
        "wordlists/base.py",
        "wordlists/bip39.py",
        "wordlists/slip39.py",
        "wordlists/ubip39.py",
        "wordlists/uslip39.py",
    ],
    base_path="$(PORT_DIR)/../third_party/embit/src",
)

# NDS-Signer shims
module("random.py", base_path="$(PORT_DIR)/frozen")
module("nds_ui_random.py", base_path="$(PORT_DIR)/frozen")  # backup test only

# CPython stdlib compatibility modules needed by SeedSigner (see each file)
for _name in ("dataclasses", "enum", "importlib", "threading", "traceback", "typing", "gettext",
              "platform", "os", "pathlib", "re",
              "_pyre", "time", "nds_strcompat"):
    module(_name + ".py", base_path="$(PORT_DIR)/frozen/compat")

# Stand-ins for Raspberry Pi hardware libraries (QR decoding is native here)
package("pyzbar", base_path="$(PORT_DIR)/frozen/hwstubs")
package("PIL", base_path="$(PORT_DIR)/frozen/hwstubs")

# From micropython-lib
require("logging")
# base64 / zlib without their manifest dependencies: require("base64") would
# also freeze micropython-lib's pure-Python binascii, which shadows the native
# one and rejects str input (embit passes str to a2b_base64).
module("base64.py", base_path="$(MPY_LIB_DIR)/python-stdlib/base64")
module("zlib.py", base_path="$(MPY_LIB_DIR)/python-stdlib/zlib")
module("datetime.py", base_path="$(MPY_LIB_DIR)/python-stdlib/datetime")

# urtypes (Krux project, the commit SeedSigner pins), transformed for
# insertion-ordered dicts (mpy/Makefile, tools/upy_transform.py)
package("urtypes", base_path="$(PORT_DIR)/../build/frozen_py")

# Upstream SeedSigner, transformed by tools/upy_transform.py (mpy/Makefile)
package("seedsigner", base_path="$(PORT_DIR)/../build/frozen_py")

# SPIKE: the host test scripts and vectors, run unchanged on the DSi
module("psbt_parser_summary.py", base_path="$(PORT_DIR)/../tests/vectors")
module("seedsigner_check.py", base_path="$(PORT_DIR)/../tests/host")
module("decode_qr_check.py", base_path="$(PORT_DIR)/../tests/host")
module("flow_check.py", base_path="$(PORT_DIR)/../tests/host")
module("bip39_jp_check.py", base_path="$(PORT_DIR)/../tests/host")
module("test_vectors.py", base_path="$(PORT_DIR)/../build/frozen_py")

# SeedSigner's translations (tools/po_to_py.py, generated with the rest of
# build/frozen_py by mpy/Makefile)
include("$(PORT_DIR)/../build/frozen_py/l10n_manifest.py")

# Python entry point
module("nds_main.py", base_path="$(PORT_DIR)/frozen")

import os as _os

# Developer build only (make DEVBUILD=1): diagnostics screen
if _os.environ.get("NDS_DEVBUILD"):
    module("nds_dev.py", base_path="$(PORT_DIR)/frozen/dev")

# AUTOTEST builds only (make AUTOTEST=1): scripted taps for unattended runs
if _os.environ.get("NDS_AUTOTEST"):
    module("autopilot.py", base_path="$(PORT_DIR)/frozen/autotest")
    if _os.environ.get("NDS_AUTOPILOT") == "dev":
        module("autopilot_dev.py", base_path="$(PORT_DIR)/../tests/host")
    else:
        module("autopilot_script.py", base_path="$(PORT_DIR)/../tests/host")
