# NDS-Signer - MicroPython frozen modules manifest (SPIKE)
#
# Upstream Python frozen unmodified into the ROM as bytecode (mpy-cross).
# See docs/architecture.md.

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

# CPython stdlib compatibility modules needed by SeedSigner (see each file)
for _name in ("dataclasses", "typing", "gettext", "platform", "os", "pathlib", "time", "unicodedata"):
    module(_name + ".py", base_path="$(PORT_DIR)/frozen/compat")

# From micropython-lib
require("logging")

# Upstream SeedSigner, transformed by tools/upy_transform.py (mpy/Makefile)
package("seedsigner", base_path="$(PORT_DIR)/../build/frozen_py")

# SPIKE: shared test helper, identical on CPython and on the DSi
module("psbt_parser_summary.py", base_path="$(PORT_DIR)/../tests/vectors")
