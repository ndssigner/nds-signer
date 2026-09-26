#!/usr/bin/env python3
"""Generate a synthetic testnet PSBT with N P2WPKH inputs owned by the public
BIP-39 test seed "abandon ... about", plus the signature expected from embit.

Test data only: the prevouts are made up and the seed is public.
Requires embit (the version SeedSigner pins) on the host:
    tools/make_test_psbt.py 10 tests/vectors/psbt_base64_10in
writes <prefix>.txt, <prefix>.mnemonic.txt and <prefix>.signed.txt
"""
import hashlib
import sys

from embit import bip32, bip39, script
from embit.networks import NETWORKS
from embit.psbt import PSBT, DerivationPath
from embit.transaction import Transaction, TransactionInput, TransactionOutput

MNEMONIC = "abandon " * 11 + "about"


def main():
    n, prefix = int(sys.argv[1]), sys.argv[2]
    net = NETWORKS["test"]
    root = bip32.HDKey.from_seed(bip39.mnemonic_to_seed(MNEMONIC), version=net["xprv"])
    fp = root.my_fingerprint

    vin, keys = [], []
    for i in range(n):
        path = "m/84h/1h/0h/0/%d" % i
        key = root.derive(path)
        txid = hashlib.sha256(b"nds-signer test prevout %d" % i).digest()
        vin.append(TransactionInput(txid, i % 3))
        keys.append((path, key.get_public_key()))

    dest = script.p2wpkh(root.derive("m/84h/1h/0h/0/100").get_public_key())
    change = script.p2wpkh(root.derive("m/84h/1h/0h/1/0").get_public_key())
    total = 10_000 * n
    fee = 150 * n + 200
    tx = Transaction(vin=vin, vout=[
        TransactionOutput(total // 2, dest),
        TransactionOutput(total - total // 2 - fee, change),
    ])
    psbt = PSBT(tx)
    for inp, (path, key) in zip(psbt.inputs, keys):
        inp.witness_utxo = TransactionOutput(10_000, script.p2wpkh(key))
        inp.bip32_derivations[key] = DerivationPath(fp, bip32.parse_path(path))
    psbt.outputs[1].bip32_derivations[root.derive("m/84h/1h/0h/1/0").get_public_key()] = DerivationPath(
        fp, bip32.parse_path("m/84h/1h/0h/1/0"))

    unsigned = psbt.to_string()
    signed_psbt = PSBT.from_string(unsigned)
    assert signed_psbt.sign_with(root) == n
    open(prefix + ".txt", "w").write(unsigned)
    open(prefix + ".mnemonic.txt", "w").write(MNEMONIC)
    open(prefix + ".signed.txt", "w").write(signed_psbt.to_string())
    print("%s: %d inputs, %d chars" % (prefix, n, len(unsigned)))


if __name__ == "__main__":
    main()
