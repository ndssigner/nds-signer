# NDS-Signer - text UI primitives for the dual-screen DSi.
#
# Top screen: information (title, status, body text, live camera, QR codes).
# Bottom screen: touch buttons; the D-pad + A also work, B goes back.
# Everything is drawn with the `nds` module (native) or its host simulator.
from seedsigner.gui.hw import nds

COLS = nds.COLS
ROWS = nds.ROWS
BUTTON_ROWS = 3           # each button is a 3-row box
FIRST_BUTTON_ROW = 1
BUTTONS_PER_PAGE = 5      # rows 1..15
NAV_ROW = 20              # "< Back" and paging, rows 20..22

# Box-drawing glyphs of NDS-Signer's console font (tools/bdf_to_ndsfont.py):
# (horizontal, vertical, top-left, top-right, bottom-left, bottom-right)
BOX_SINGLE = ("\x10", "\x11", "\x12", "\x13", "\x14", "\x15")
BOX_DOUBLE = ("\x16", "\x17", "\x18", "\x19", "\x1a", "\x1c")


def box_rows(width, label, highlighted=False):
    """The three text rows of a box of `width` cells around `label`."""
    h, v, tl, tr, bl, br = BOX_DOUBLE if highlighted else BOX_SINGLE
    inner = width - 2
    text = label[:inner]
    left = (inner - len(text)) // 2
    body = " " * left + text + " " * (inner - len(text) - left)
    return (tl + h * inner + tr, v + body + v, bl + h * inner + br)


BACK = "back"
_BACK_LABEL = "< Back"
_PREV_LABEL = "Prev"
_NEXT_LABEL = "Next"


def pad(text, width=COLS):
    """str.ljust (not available in MicroPython)."""
    return text + " " * (width - len(text)) if len(text) < width else text


def center(text, width=COLS):
    """str.center (optional in MicroPython), without trailing spaces."""
    return " " * ((width - len(text)) // 2) + text if len(text) < width else text


def wrap(text, width=COLS):
    """Word-wraps text (keeps explicit newlines)."""
    lines = []
    for paragraph in str(text).split("\n"):
        line = ""
        for word in paragraph.split(" "):
            while len(word) > width:  # hard-split very long words (addresses)
                if line:
                    lines.append(line)
                    line = ""
                lines.append(word[:width])
                word = word[width:]
            if not line:
                line = word
            elif len(line) + 1 + len(word) <= width:
                line += " " + word
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def top_page(title, lines):
    """Title bar on the top screen, then the given lines (clipped)."""
    nds.top_clear()
    nds.top_print(0, -1, title or "")
    nds.top_print(1, 0, BOX_SINGLE[0] * COLS)
    for i, line in enumerate(lines[:ROWS - 3]):
        nds.top_print(3 + i, 0, line)


def _box(row, col, width, label, selected):
    for i, text in enumerate(box_rows(width, label, selected)):
        nds.bottom_print(row + i, col, text)


class ButtonPanel:
    """A pageable list of full-width touch buttons on the bottom screen."""

    def __init__(self, labels, show_back=True, selected=0, header=None):
        self.labels = list(labels)
        self.show_back = show_back
        self.selected = selected if 0 <= selected < len(self.labels) else 0
        self.header = header
        self.hits = []  # (row0, row1, col0, col1, action)

    def page(self):
        return self.selected // BUTTONS_PER_PAGE

    def pages(self):
        return max(1, (len(self.labels) + BUTTONS_PER_PAGE - 1) // BUTTONS_PER_PAGE)

    def draw(self):
        nds.bottom_clear()
        self.hits = []
        if self.header:
            nds.bottom_print(0, -1, self.header)
        start = self.page() * BUTTONS_PER_PAGE
        for i, label in enumerate(self.labels[start:start + BUTTONS_PER_PAGE]):
            row = FIRST_BUTTON_ROW + i * BUTTON_ROWS
            _box(row, 1, COLS - 2, label, start + i == self.selected)
            self.hits.append((row, row + BUTTON_ROWS, 1, COLS - 1, start + i))
        if self.show_back:
            _box(NAV_ROW, 1, 10, _BACK_LABEL, False)
            self.hits.append((NAV_ROW, NAV_ROW + BUTTON_ROWS, 1, 11, BACK))
        if self.pages() > 1:
            nds.bottom_print(NAV_ROW - 1, -1, "page %d/%d" % (self.page() + 1, self.pages()))
            if self.page() > 0:
                _box(NAV_ROW, 12, 9, _PREV_LABEL, False)
                self.hits.append((NAV_ROW, NAV_ROW + BUTTON_ROWS, 12, 21, "prev"))
            if self.page() < self.pages() - 1:
                _box(NAV_ROW, 22, 9, _NEXT_LABEL, False)
                self.hits.append((NAV_ROW, NAV_ROW + BUTTON_ROWS, 22, 31, "next"))

    def _hit(self, x, y):
        row, col = y // 8, x // 8
        for r0, r1, c0, c1, action in self.hits:
            if r0 <= row < r1 and c0 <= col < c1:
                return action
        return None

    def handle_frame(self):
        """Processes one frame of input. Returns an index, BACK or None."""
        down = nds.keys_down()
        if not down:
            return None
        if down & nds.KEY_TOUCH:
            xy = nds.touch()
            action = self._hit(xy[0], xy[1]) if xy else None
            if action == "prev":
                self.selected = (self.page() - 1) * BUTTONS_PER_PAGE
                self.draw()
                return None
            if action == "next":
                self.selected = (self.page() + 1) * BUTTONS_PER_PAGE
                self.draw()
                return None
            return action
        if down & nds.KEY_A and self.labels:
            return self.selected
        if down & nds.KEY_B and self.show_back:
            return BACK
        if down & (nds.KEY_UP | nds.KEY_DOWN) and self.labels:
            step = -1 if down & nds.KEY_UP else 1
            self.selected = (self.selected + step) % len(self.labels)
            self.draw()
        return None

    def run(self):
        self.draw()
        while True:
            nds.frame()
            result = self.handle_frame()
            if result is not None:
                return result
