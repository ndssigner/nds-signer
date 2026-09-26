#!/usr/bin/env python3
"""Reference for the end-to-end flow test: what SeedSigner's PSBTFinalizeView
outputs (sign with embit, then PSBTParser.trim), computed on CPython with the
pinned upstream sources:
    PYTHONPATH=third_party/seedsigner/src:mpy/frozen/hwstubs \\
        tools/make_trimmed_ref.py tests/vectors/psbt_base64_singlesig
writes <prefix>.signed_trimmed.txt
"""
import sys

from embit import bip32
from embit.networks import NETWORKS
from embit.psbt import PSBT
from seedsigner.models.psbt_parser import PSBTParser
from seedsigner.models.seed import Seed

prefix = sys.argv[1]
mnemonic = open(prefix + ".mnemonic.txt").read().split()
psbt = PSBT.from_string(open(prefix + ".txt").read().strip())
root = bip32.HDKey.from_seed(Seed(mnemonic).seed_bytes, version=NETWORKS["test"]["xprv"])
psbt.sign_with(root)
open(prefix + ".signed_trimmed.txt", "w").write(PSBTParser.trim(psbt).to_string())
