# NDS-Signer - a NON-cryptographic random generator for UI choices only.
#
# NDS-Signer's `random` module refuses to work, so that no PRNG can ever feed
# key material. SeedSigner's backup test (views/seed_views.py) still needs to
# pick which seed word to ask and to shuffle three decoy words; that view
# alone imports this module instead (tools/upy_transform.py,
# IMPORT_REPLACEMENTS). Predictability does not matter there: the user
# already knows the words being tested.
#
# xorshift32, seeded from the frame counter the first time it is used.
from seedsigner.gui.hw import nds

_state = [0]


def seed(a=None):
    value = nds.ticks_ms() if a is None else int(a)
    _state[0] = (value * 2654435761 + 1) & 0xFFFFFFFF or 1


def _next():
    if not _state[0]:
        seed()
    x = _state[0]
    x ^= (x << 13) & 0xFFFFFFFF
    x ^= x >> 17
    x ^= (x << 5) & 0xFFFFFFFF
    _state[0] = x
    return x


def random():
    return _next() / 4294967296.0


def randrange(start, stop=None):
    if stop is None:
        start, stop = 0, start
    return start + _next() % (stop - start)


def uniform(a, b):
    return a + (b - a) * random()


def shuffle(items):
    for i in range(len(items) - 1, 0, -1):
        j = _next() % (i + 1)
        items[i], items[j] = items[j], items[i]
