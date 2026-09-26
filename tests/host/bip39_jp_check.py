# Official Japanese BIP-39 vectors (tests/vectors/bip39_japanese.json):
# NFKD-normalized mnemonic + passphrase -> seed, with embit. Runs on the host
# MicroPython and, frozen with the vectors, on the DSi.
import json
import unicodedata
from binascii import hexlify

from embit import bip39

try:
    import test_vectors  # frozen into the spike ROM (no filesystem on the DSi)
    vectors = json.loads(test_vectors.DATA["bip39_japanese.json"])
except ImportError:
    vectors = json.load(open("../vectors/bip39_japanese.json"))

matches = 0
for v in vectors:
    seed = bip39.mnemonic_to_seed(unicodedata.normalize("NFKD", v["mnemonic"]),
                                  unicodedata.normalize("NFKD", v["passphrase"]), wordlist=None)
    matches += hexlify(seed).decode() == v["seed"]
print("ok  " if matches == len(vectors) else "FAIL",
      "BIP-39 Japanese vectors (NFKD): %d/%d" % (matches, len(vectors)))
