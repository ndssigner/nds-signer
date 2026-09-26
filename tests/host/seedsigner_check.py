# Runs SeedSigner models (PSBTParser) and embit signing over the PSBT test
# vectors and compares with the CPython references in tests/vectors.
# Runs under CPython (upstream sources) and under MicroPython (the frozen,
# transformed sources): both must print only "ok" lines.
import sys

from embit import bip32
from embit.networks import NETWORKS
from embit.psbt import PSBT

import psbt_parser_summary

VECTORS = sys.argv[1] if len(sys.argv) > 1 else "../vectors"
failures = 0


def read(name):
    try:
        import test_vectors  # frozen into the spike ROM (no filesystem on the DSi)
        return test_vectors.DATA[name].strip()
    except ImportError:
        with open(VECTORS + "/" + name) as f:
            return f.read().strip()


for prefix in ("psbt_base64_singlesig", "psbt_base64_10in"):
    psbt_b64 = read(prefix + ".txt")
    mnemonic = read(prefix + ".mnemonic.txt")

    summary = psbt_parser_summary.summary(psbt_b64, mnemonic)
    ok = summary == read(prefix + ".summary.txt")
    print("ok  " if ok else "FAIL", prefix, "PSBTParser summary")
    failures += not ok

    from seedsigner.models.seed import Seed
    seed = Seed(mnemonic.split())
    root = bip32.HDKey.from_seed(seed.seed_bytes, version=NETWORKS["test"]["xprv"])
    psbt = PSBT.from_string(psbt_b64)
    psbt.sign_with(root)
    ok = psbt.to_string() == read(prefix + ".signed.txt")
    print("ok  " if ok else "FAIL", prefix, "signature")
    failures += not ok

print("PASSED" if not failures else "FAILED")
if __name__ == "__main__":
    sys.exit(1 if failures else 0)
