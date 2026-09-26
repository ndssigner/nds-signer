# NDS-Signer - touch keyboard for the bottom screen.
#
# Keys are 3x3-cell boxes ("+-+", "|q|", "+-+"). Disabled keys are drawn as
# "." and ignore taps, which lets the mnemonic entry offer only letters that
# continue a valid BIP-39 word (as SeedSigner does).
from seedsigner.gui.hw import nds
from seedsigner.gui import nds_ui

CELL = 8
QWERTY = ("qwertyuiop", "asdfghjkl", "zxcvbnm")


class Key:
    def __init__(self, label, row, col, width=3, action=None):
        self.label = label
        self.row = row
        self.col = col
        self.width = width
        self.action = action if action is not None else label

    def contains(self, cell_row, cell_col):
        return self.row <= cell_row < self.row + 3 and self.col <= cell_col < self.col + self.width

    def center(self):
        return ((self.col * 2 + self.width) * CELL // 2, self.row * CELL + CELL * 3 // 2)


def qwerty_keys(first_row):
    """Letter keys; rows are centred (10, 9 and 7 keys of 3 cells)."""
    keys = []
    for r, letters in enumerate(QWERTY):
        col = (nds_ui.COLS - len(letters) * 3) // 2
        for i, ch in enumerate(letters):
            keys.append(Key(ch, first_row + r * 3, col + i * 3))
    return keys


def draw_key(key, enabled=True, highlighted=False):
    label = key.label if enabled else "."
    for i, text in enumerate(nds_ui.box_rows(key.width, label, highlighted)):
        nds.bottom_print(key.row + i, key.col, text)


# Keys currently on screen, set by the screen that drew them last; lets tests
# and the emulator autopilot tap a key by its label.
ACTIVE_KEYS = []


def set_active(keys):
    global ACTIVE_KEYS
    ACTIVE_KEYS = list(keys)


def key_at(keys, x, y):
    row, col = y // CELL, x // CELL
    for key in keys:
        if key.contains(row, col):
            return key
    return None


def key_center(label):
    """Screen position of a key on screen by its label (tests, autopilot)."""
    for key in ACTIVE_KEYS:
        if key.label == label:
            return key.center()
    raise KeyError("key %r not on screen" % label)
