# Differential test of NDS-Signer's native unicodedata.normalize (utf8proc)
# against CPython's (tests/host/unicode_gen.py output), plus the official
# Japanese BIP-39 vectors (NFKD mnemonic + passphrase -> seed) with embit.
import json
import sys
import unicodedata
from binascii import hexlify

FORMS = ("NFC", "NFD", "NFKC", "NFKD")


def text_of(cps):
    """Code points -> str via UTF-8 bytes. (chr() would intern every
    character as a qstr in MicroPython; ~140k of them corrupt the table.)"""
    out = bytearray()
    for c in cps:
        if c < 0x80:
            out.append(c)
        elif c < 0x800:
            out += bytes((0xC0 | c >> 6, 0x80 | c & 0x3F))
        elif c < 0x10000:
            out += bytes((0xE0 | c >> 12, 0x80 | c >> 6 & 0x3F, 0x80 | c & 0x3F))
        else:
            out += bytes((0xF0 | c >> 18, 0x80 | c >> 12 & 0x3F, 0x80 | c >> 6 & 0x3F, 0x80 | c & 0x3F))
    return bytes(out).decode()

cases = json.load(open(sys.argv[1]))
failures = 0
for case in cases:
    text = text_of(case[0])
    for i, form in enumerate(FORMS):
        expected = text_of(case[i + 1])
        if unicodedata.normalize(form, text) != expected:
            failures += 1
            if failures <= 5:
                print("FAIL", form, case[0][:8])
print("ok  " if not failures else "FAIL", "unicodedata: %d strings x 4 forms vs CPython, %d mismatches"
      % (len(cases), failures))

from embit import bip39  # noqa: E402

vectors = json.load(open(sys.argv[2]))
bad = 0
for v in vectors:
    mnemonic = unicodedata.normalize("NFKD", v["mnemonic"])
    passphrase = unicodedata.normalize("NFKD", v["passphrase"])
    seed = bip39.mnemonic_to_seed(mnemonic, passphrase, wordlist=None)
    if hexlify(seed).decode() != v["seed"]:
        bad += 1
print("ok  " if not bad else "FAIL", "BIP-39 Japanese vectors (NFKD): %d/%d seeds match"
      % (len(vectors) - bad, len(vectors)))
sys.exit(1 if failures or bad else 0)
