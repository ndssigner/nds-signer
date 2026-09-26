#!/usr/bin/env python3
"""Encode a base64 PSBT as animated UR (crypto-psbt) QR parts, exactly like
SeedSigner's UrPsbtQrEncoder (models/encode_qr.py), one part per line.

Uses SeedSigner's own ur2 encoder and urtypes from the pinned submodules:
    PYTHONPATH=third_party/seedsigner/src tools/make_ur_parts.py \\
        tests/vectors/psbt_base64_10in.txt 30 > tests/vectors/psbt_base64_10in.ur.txt
The second argument is max_fragment_len (SeedSigner: 30 for medium density).
Emits seq_len + 5 parts, so decoding also exercises fountain (mixed) parts.
"""
import sys
from binascii import a2b_base64

from seedsigner.helpers.ur2.ur import UR
from seedsigner.helpers.ur2.ur_encoder import UREncoder
from urtypes.crypto import PSBT as UR_PSBT

psbt_bytes = a2b_base64(open(sys.argv[1]).read().strip())
encoder = UREncoder(ur=UR("crypto-psbt", UR_PSBT(psbt_bytes).to_cbor()),
                    max_fragment_len=int(sys.argv[2]))
for _ in range(encoder.fountain_encoder.seq_len() + 5):
    print(encoder.next_part().upper())
