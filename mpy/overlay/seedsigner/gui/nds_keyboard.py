# NDS-Signer - touch keyboard for the bottom screen.
#
# Keys are laid out on the 8x8-pixel cell grid (3 cells high) and drawn as
# rounded buttons. Disabled keys are dimmed and ignore taps, which lets the
# mnemonic entry offer only letters that continue a valid BIP-39 word (as
# SeedSigner does).
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
    """A rounded key over its 3-row cell area (drawn to the back buffer;
    set_active() shows the keyboard)."""
    _pending[id(key)] = (key, enabled, highlighted)
    _draw(key, enabled, highlighted)


def _draw(key, enabled, highlighted):
    font = nds.FONT_BUTTON if len(key.label) <= 2 else nds.FONT_BODY_BOLD
    nds_ui.button(nds_ui.BOTTOM, key.col * CELL + 1, key.row * CELL + 1, key.width * CELL - 2,
                  3 * CELL - 2, key.label, selected=highlighted, enabled=enabled, font=font)


# Keys currently on screen, set by the screen that drew them last; lets tests
# and the emulator autopilot tap a key by its label.
ACTIVE_KEYS = []
# id(key) -> (key, enabled, highlighted) of the keys drawn on screen now
_pending = {}
_drawn = {}


def set_active(keys):
    """Keys now on screen; also shows the keys drawn since the last clear."""
    global ACTIVE_KEYS, _pending, _drawn
    ACTIVE_KEYS = list(keys)
    _drawn, _pending = _pending, {}
    nds.gfx_present(nds_ui.BOTTOM)


class KeyTracker(nds_ui.TapTracker):
    """TapTracker for keyboards, with visual feedback: the key under the
    stylus is shown pressed (inverted colours) until the stylus moves off it
    or is lifted."""

    def __init__(self):
        super().__init__()
        self.pressed = None

    def update(self):
        xy = nds.touch()
        if xy is None:
            self._show(None)
        elif xy[0] or xy[1]:  # (0, 0) = no valid reading yet
            row, col = xy[1] // CELL, xy[0] // CELL
            self._show(next((k for k, enabled, _h in _drawn.values()
                             if enabled and k.contains(row, col)), None))
        return super().update()

    def _show(self, key):
        if key is self.pressed:
            return
        old, self.pressed = self.pressed, key
        if old is not None and id(old) in _drawn:
            _draw(*_drawn[id(old)])
        if key is not None:
            _k, enabled, highlighted = _drawn[id(key)]
            _draw(key, enabled, not highlighted)
        nds.gfx_present(nds_ui.BOTTOM)


def key_at(keys, x, y):
    """The key tapped at (x, y), if any (with its click sound)."""
    row, col = y // CELL, x // CELL
    for key in keys:
        if key.contains(row, col):
            nds_ui.sound("back" if key.action == "back" else "key")
            return key
    return None


def key_center(label):
    """Screen position of a key on screen by its label (tests, autopilot)."""
    for key in ACTIVE_KEYS:
        if key.label == label:
            return key.center()
    raise KeyError("key %r not on screen" % label)
