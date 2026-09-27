#!/usr/bin/env python3
"""Reference for the xpub export flow test: the animated UR (crypto-account)
parts SeedSigner's own UrXpubQrEncoder produces on CPython for a test seed,
single sig native segwit, testnet, default QR density. One part per line.
    PYTHONPATH=third_party/seedsigner/src tools/make_xpub_ref.py \\
        tests/vectors/psbt_base64_singlesig | grep "^UR:" > tests/vectors/psbt_base64_singlesig.xpub_ur.txt
Needs (host only): embit==0.8.0, urtypes, qrcode, pillow.
"""
import sys

from seedsigner.models.encode_qr import UrXpubQrEncoder
from seedsigner.models.seed import Seed
from seedsigner.models.settings import Settings, SettingsConstants

prefix = sys.argv[1]
seed = Seed(open(prefix + ".mnemonic.txt").read().split())
encoder = UrXpubQrEncoder(
    seed=seed,
    derivation="m/84'/1'/0'",
    network=SettingsConstants.TESTNET,
    qr_density=Settings.get_instance().get_value(SettingsConstants.SETTING__QR_DENSITY),
    sig_type=SettingsConstants.SINGLE_SIG,
)
for _ in range(encoder.seq_len()):
    print(encoder.next_part())
