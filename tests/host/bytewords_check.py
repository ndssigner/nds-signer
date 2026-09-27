# NDS-Signer: the native Bytewords decoding installed by the overlay
# (seedsigner/helpers/ur2/__init__.py, lib/mpy-usermods/bytewords) must behave
# exactly like SeedSigner's Python decode(): same bytes for valid input, and
# ValueError('Invalid Bytewords.') for invalid input. Run on MicroPython.
import seedsigner.helpers.ur2  # installs the native version
from seedsigner.helpers.ur2 import bytewords as bw
from seedsigner.helpers.ur2.bytewords import Bytewords, Bytewords_Style_minimal
from test_vectors import DATA

native, upstream = bw.decode, seedsigner.helpers.ur2._upstream_decode
assert native is not upstream, "native Bytewords decoding not installed"


def outcome(fn, s):
    try:
        return ("ok", bytes(fn(s, 0, 2)))
    except ValueError as e:
        return ("ValueError", str(e))


seed = 7  # tiny LCG: same inputs on every run


def rand(n):
    global seed
    seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
    return seed % n


cases = []
for name in ("psbt_base64_10in.ur.txt", "psbt_base64_singlesig.ur.txt",
             "psbt_base64_singlesig.xpub_ur.txt"):
    for part in DATA[name].split():
        body = part.split("/")[-1]
        cases += [body, body.lower()]
for _ in range(400):  # random valid bodies (with a correct checksum)
    data = bytes(rand(256) for _ in range(rand(40)))
    cases.append(Bytewords.encode(Bytewords_Style_minimal, data))
mutants = []
alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/ é"
for s in cases[:300]:
    if not s:
        continue
    i = rand(len(s))
    mutants.append(s[:i] + alphabet[rand(len(alphabet))] + s[i + 1:])  # replace
    mutants.append(s[:i] + s[i + 1:])                                    # delete
    c = s[i]
    mutants.append(s[:i] + (c.lower() if c.isupper() else c.upper()) + s[i + 1:])  # case
cases += mutants + ["", "a", "ab", "abcd", "lpad", "LPAD", "zmzmzmzmzm", "éé", "aé"]
# every 2-letter word, both cases, in a valid position
for a in range(26):
    for b in range(26):
        w = chr(97 + a) + chr(97 + b)
        cases += [w * 5, (w * 5).upper()]

mismatch = 0
kinds = {"ok": 0, "ValueError": 0}
for s in cases:
    n, u = outcome(native, s), outcome(upstream, s)
    kinds[u[0]] += 1
    if n != u:
        mismatch += 1
        if mismatch <= 5:
            print("MISMATCH", repr(s), n, u)
print("%s native Bytewords decode: %d inputs (%d valid, %d invalid), %d mismatches" % (
    "ok  " if mismatch == 0 else "FAIL", len(cases), kinds["ok"], kinds["ValueError"], mismatch))
