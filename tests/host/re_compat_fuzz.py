# Randomized differential test for mpy/frozen/compat/re.py: prints one line
# per (pattern, input); CPython and MicroPython outputs must be identical.
# Uses its own LCG so both interpreters generate the same inputs.
import re
from re_compat_cases import CASES

SEEDS = [text for _, _, text in CASES]
ALPHABET = "0123456789abcdefmnpqtuxzABCDEFMNPQTUXZ:/$ -{}\"+=,."


class Lcg:
    def __init__(self, seed):
        self.s = seed

    def next(self, n):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s % n


def inputs(rng, count):
    for _ in range(count):
        kind = rng.next(3)
        if kind == 0:  # random string
            yield "".join(ALPHABET[rng.next(len(ALPHABET))] for _ in range(rng.next(110)))
        else:  # mutate a known interesting input: flip, insert, delete, repeat
            s = SEEDS[rng.next(len(SEEDS))]
            for _ in range(1 + rng.next(4)):
                op = rng.next(4)
                pos = rng.next(len(s) + 1)
                ch = ALPHABET[rng.next(len(ALPHABET))]
                if op == 0 and s:
                    pos = min(pos, len(s) - 1)
                    s = s[:pos] + ch + s[pos + 1:]
                elif op == 1:
                    s = s[:pos] + ch + s[pos:]
                elif op == 2 and s:
                    pos = min(pos, len(s) - 1)
                    s = s[:pos] + s[pos + 1:]
                else:
                    s = s[:pos] + s[pos:pos + 1] * rng.next(40) + s[pos:]
            yield s


patterns = []
for p, f, _ in CASES:
    if (p, f) not in patterns and p != r'[^,\s]+':
        patterns.append((p, f))

rng = Lcg(2026)
total = 0
for pattern, flags in patterns:
    for text in inputs(rng, 400):
        m = re.search(pattern, text, flags)
        print(repr(pattern)[:24], flags, repr(text)[:40], None if m is None else (m.group(0), m.groups()))
        total += 1
print("total", total)
