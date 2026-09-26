# Generates the expected results for the unicodedata differential test with
# CPython (run in the builder image: CPython 3.11, Unicode 14.0).
# Output: JSON list of [codepoints, NFC, NFD, NFKC, NFKD] (codepoint lists, so
# no encoding is involved).
import json
import sys
import unicodedata

FORMS = ("NFC", "NFD", "NFKC", "NFKD")


class Lcg:
    def __init__(self, seed):
        self.s = seed

    def next(self, n):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s % n


def cps(s):
    return [ord(c) for c in s]


strings = []
# every assigned code point (Unicode 14) except surrogates and private use
for cp in range(0x110000):
    cat = unicodedata.category(chr(cp))
    if cat not in ("Cn", "Cs", "Co"):
        strings.append(chr(cp))

# sequences that exercise canonical reordering and composition
marks = [chr(c) for c in range(0x300, 0x370)] + ["ཱ", "ི", "ְ", "़", "゙", "゚"]
bases = list("aeiouAEIOUnNcCsSzZ") + ["Α", "а", "か", "ハ", "ᄀ", "가"]
rng = Lcg(14)
for _ in range(20000):
    s = "".join(bases[rng.next(len(bases))] + "".join(marks[rng.next(len(marks))]
                                                   for _ in range(rng.next(4)))
                for _ in range(1 + rng.next(4)))
    strings.append(s)
# Hangul jamo sequences (L V T) and passphrase-like mixed text
for l in range(0x1100, 0x1113, 3):
    for v in range(0x1161, 0x1176, 4):
        strings.append(chr(l) + chr(v))
        strings.append(chr(l) + chr(v) + chr(0x11A8 + (l + v) % 27))
strings += ["Contraseña café ﬁn Ⅷ ＡＢ ㍱", "Ångström Å"]

json.dump([[cps(s)] + [cps(unicodedata.normalize(f, s)) for f in FORMS] for s in strings],
          sys.stdout, separators=(",", ":"))
