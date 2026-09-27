# NDS-Signer - text UI primitives for the dual-screen DSi.
#
# Top screen: information (title, status, body text, live camera, QR codes).
# Bottom screen: touch buttons; the D-pad + A also work, B goes back.
# Everything is drawn with the `nds` module (native) or its host simulator.
from seedsigner.gui.hw import nds

try:
    import nds_dev  # developer build only
except ImportError:
    nds_dev = None

COLS = nds.COLS
ROWS = nds.ROWS
GFX_W, GFX_H = 256, 192
TOP, BOTTOM = 0, 1

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


# ---- graphical style (UI style A: SeedSigner's colours, dark) ----
def _rgb(hex_color):
    return int(hex_color[1:], 16)


def _theme():
    from seedsigner.gui.components import GUIConstants as GC
    return {
        "bg": _rgb(GC.BACKGROUND_COLOR), "accent": _rgb(GC.ACCENT_COLOR),
        "button": _rgb(GC.BUTTON_BACKGROUND_COLOR), "button_fg": _rgb(GC.BUTTON_FONT_COLOR),
        "body": _rgb(GC.BODY_FONT_COLOR), "label": _rgb(GC.LABEL_FONT_COLOR),
        "inactive": _rgb(GC.INACTIVE_COLOR),
    }


_THEME = []


def theme():
    if not _THEME:
        _THEME.append(_theme())
    return _THEME[0]


MARGIN = 8
TITLE_Y = 4
BODY_Y = 32          # first body line on the top screen
BUTTON_H = 28        # touch buttons on the bottom screen
BUTTON_GAP = 5
BUTTON_RADIUS = 8
FIRST_BUTTON_Y = 4
BUTTONS_PER_PAGE = 5
NAV_Y = GFX_H - 26   # "< Back" and paging
NAV_H = 24


def text_centered(screen, y, text, font, color, x=0, width=GFX_W):
    w = nds.gfx_text_width(text, font)
    return nds.gfx_text(screen, x + max(0, (width - w) // 2), y, text, font, color, width)


def button(screen, x, y, w, h, label, selected=False, enabled=True, font=None, checked=False):
    """A rounded touch button with its label centred (and a check mark on
    the left for the chosen option of a selection list)."""
    t = theme()
    font = nds.FONT_BUTTON if font is None else font
    fill = t["accent"] if selected else (t["button"] if enabled else t["bg"])
    nds.gfx_rect(screen, x, y, w, h, fill, BUTTON_RADIUS if h > 20 else 5)
    if not enabled:
        nds.gfx_frame(screen, x, y, w, h, t["inactive"], BUTTON_RADIUS if h > 20 else 5, 1)
    color = t["bg"] if selected else (t["button_fg"] if enabled else t["inactive"])
    line = nds.gfx_font_metrics(font)[1]
    text_centered(screen, y + (h - line) // 2, label, font, color, x + 4, w - 8)
    if checked:
        from seedsigner.gui.components import SeedSignerIconConstants as Icons
        icon_h = nds.gfx_font_metrics(nds.FONT_SSICON)[1]
        nds.gfx_text(screen, x + 10, y + (h - icon_h) // 2, Icons.CHECK, nds.FONT_SSICON, color)


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


def wrap_px(text, font, width):
    """Word-wraps text to `width` pixels in `font` (keeps explicit newlines;
    words longer than a line are split)."""
    lines = []
    space = nds.gfx_text_width(" ", font)
    for paragraph in str(text).split("\n"):
        line, line_w = "", 0
        for word in paragraph.split(" "):
            w = nds.gfx_text_width(word, font)
            while w > width:  # hard-split (addresses, xpubs)
                cut = len(word)
                while cut > 1 and nds.gfx_text_width(word[:cut], font) > width:
                    cut -= 1
                if line:
                    lines.append(line)
                    line, line_w = "", 0
                lines.append(word[:cut])
                word = word[cut:]
                w = nds.gfx_text_width(word, font)
            if not line:
                line, line_w = word, w
            elif line_w + space + w <= width:
                line, line_w = line + " " + word, line_w + space + w
            else:
                lines.append(line)
                line, line_w = word, w
        lines.append(line)
    return lines


def icon_font(glyph, size="huge"):
    """Font for an icon code point: SeedSigner's icons or Font Awesome."""
    seedsigner = glyph and 0xE900 <= ord(glyph[0]) <= 0xE9FF
    if size == "huge":
        return nds.FONT_SSICON_HUGE if seedsigner else nds.FONT_ICON_LARGE
    if size == "large":
        return nds.FONT_SSICON_LARGE if seedsigner else nds.FONT_ICON_LARGE
    return nds.FONT_SSICON if seedsigner else nds.FONT_ICON


def color_value(color, default):
    """0xRRGGBB from upstream's "#RRGGBB" (or an int), else `default`."""
    if isinstance(color, int):
        return color
    if isinstance(color, str) and color.startswith("#") and len(color) == 7:
        return _rgb(color)
    return default


# Top screen content as blocks, laid out with proportional text:
#   ("icon", glyph[, color])     large icon, centred
#   ("headline", text[, color])  title font, centred
#   ("text", text)               body text, centred paragraph
#   ("text_left", text)          body text, left-aligned paragraph
#   ("label", text)              body text in the label colour, centred
#   ("value", text[, color])     fixed-width bold, centred (fingerprints...)
#   ("mono", text)               fixed-width, left-aligned, wrapped
#   ("large", text[, color])     large text, centred (amounts, words)
#   ("space", pixels)
def _layout(blocks, width):
    t = theme()
    rows = []  # (font, text, color, centred, height) or ("space", h)
    for block in blocks:
        kind = block[0]
        if kind == "space":
            rows.append((None, "", 0, False, block[1]))
            continue
        text = block[1]
        if text is None or text == "":
            continue
        color = block[2] if len(block) > 2 else None
        if kind == "icon":
            font = icon_font(text)
            rows.append((font, text, color_value(color, t["accent"]), True,
                         nds.gfx_font_metrics(font)[1] + 4))
            continue
        font, centred, default = {
            "headline": (nds.FONT_TITLE, True, t["body"]),
            "text": (nds.FONT_BODY, True, t["body"]),
            "text_left": (nds.FONT_BODY, False, t["body"]),
            "label": (nds.FONT_BODY, True, t["label"]),
            "value": (nds.FONT_MONO_BOLD, True, t["body"]),
            "mono": (nds.FONT_MONO, False, t["body"]),
            "mono_small": (nds.FONT_MONO_SMALL, False, t["body"]),
            "large": (nds.FONT_LARGE, True, t["body"]),
        }[kind]
        line_h = nds.gfx_font_metrics(font)[1]
        fits = "\n" not in text and nds.gfx_text_width(text, font) <= width
        for line in [text] if fits else wrap_px(text, font, width):
            rows.append((font, line, color_value(color, default), centred, line_h))
    return rows


def top_blocks(title, blocks):
    """Title, then `blocks` (see above) centred vertically below it."""
    t = theme()
    nds.top_clear()
    nds.gfx_clear(TOP, t["bg"])
    if title:
        text_centered(TOP, TITLE_Y, title, nds.FONT_TITLE, t["body"])
    width = GFX_W - 2 * MARGIN
    rows = _layout(blocks, width)
    total = sum(r[4] for r in rows)
    y = BODY_Y + max(0, (GFX_H - BODY_Y - total) // 2 - 6)
    for font, text, color, centred, height in rows:
        if font is not None:
            if centred:
                text_centered(TOP, y, text, font, color, MARGIN, width)
            else:
                nds.gfx_text(TOP, MARGIN, y, text, font, color, width)
        y += height
    nds.gfx_present(TOP)


def top_note(y, text, color=None, font=None):
    """Replaces one centred line of text on the top screen (e.g. progress)."""
    t = theme()
    font = nds.FONT_BODY if font is None else font
    line_h = nds.gfx_font_metrics(font)[1]
    nds.gfx_rect(TOP, 0, y, GFX_W, line_h, t["bg"])
    text_centered(TOP, y, text, font, t["body"] if color is None else color)
    nds.gfx_present(TOP)


def bottom_note(y, text, color=None, font=None):
    """A line of text on the bottom screen (erases its area first); for
    status lines drawn over a button panel, e.g. scan progress."""
    t = theme()
    font = nds.FONT_BODY if font is None else font
    line_h = nds.gfx_font_metrics(font)[1]
    nds.gfx_rect(BOTTOM, 0, y, GFX_W, line_h, t["bg"])
    text_centered(BOTTOM, y, text, font, t["label"] if color is None else color)
    nds.gfx_present(BOTTOM)


def top_page(title, lines):
    """Title on the top screen, then the given lines (clipped). The lines are
    laid out for 32 text columns (spaces align them), so they are drawn in a
    fixed-width font: the larger one when they fit, else the smaller one,
    else the console font."""
    t = theme()
    nds.top_clear()
    nds.gfx_clear(TOP, t["bg"])
    if title:
        text_centered(TOP, TITLE_Y, title, nds.FONT_TITLE, t["body"])
    lines = list(lines)
    for font in (nds.FONT_MONO, nds.FONT_MONO_SMALL):
        line_h = nds.gfx_font_metrics(font)[1]
        if len(lines) * line_h <= GFX_H - BODY_Y:
            for i, line in enumerate(lines):
                if line:
                    nds.gfx_text(TOP, MARGIN, BODY_Y + i * line_h, line, font, t["body"])
            nds.gfx_present(TOP)
            return
    nds.gfx_present(TOP)
    for i, line in enumerate(lines[:ROWS - 4]):
        nds.top_print(4 + i, 0, line)


class TapTracker:
    """Turns stylus contact into taps, like a regular touch UI: a tap is
    reported when the stylus is lifted, at the last valid position read while
    it was down. On a real DSi the position read on the first frame of a touch
    is not reliable yet (often 0,0), so acting on the touch-down frame misses
    buttons (the emulator reports it exactly, which hid the problem)."""

    def __init__(self):
        self.last = None

    def update(self):
        """Call once per frame. Returns (x, y) when a tap ends, else None."""
        xy = nds.touch()
        if xy is not None:
            if xy[0] or xy[1]:  # (0, 0) = no valid reading yet
                self.last = xy
            return None
        tap, self.last = self.last, None
        return tap


class ButtonPanel:
    """A pageable list of full-width touch buttons on the bottom screen."""

    def __init__(self, labels, show_back=True, selected=0, header=None, redraw=None, checked=(),
                 on_page=None):
        self.redraw = redraw  # redraws the top screen after the dev overlay
        self.taps = TapTracker()
        self.labels = list(labels)
        self.show_back = show_back
        self.selected = selected if 0 <= selected < len(self.labels) else 0
        self.header = header
        self.checked = set(checked)
        self.on_page = on_page  # called after the page changes (top screen follows)
        self.per_page = BUTTONS_PER_PAGE - 1 if header else BUTTONS_PER_PAGE
        self.hits = []  # (x0, y0, x1, y1, action) in pixels

    def page(self):
        return self.selected // self.per_page

    def pages(self):
        return max(1, (len(self.labels) + self.per_page - 1) // self.per_page)

    def draw(self):
        t = theme()
        nds.bottom_clear()
        nds.gfx_clear(BOTTOM, t["bg"])
        self.hits = []
        y = FIRST_BUTTON_Y
        if self.header:
            text_centered(BOTTOM, y, self.header, nds.FONT_BODY_BOLD, t["label"])
            y += BUTTON_H
        start = self.page() * self.per_page
        for i, label in enumerate(self.labels[start:start + self.per_page]):
            button(BOTTOM, MARGIN, y, GFX_W - 2 * MARGIN, BUTTON_H, label, start + i == self.selected,
                   checked=start + i in self.checked)
            self.hits.append((MARGIN, y, GFX_W - MARGIN, y + BUTTON_H, start + i))
            y += BUTTON_H + BUTTON_GAP
        if self.show_back:
            button(BOTTOM, MARGIN, NAV_Y, 80, NAV_H, _BACK_LABEL, font=nds.FONT_BODY_BOLD)
            self.hits.append((MARGIN, NAV_Y, MARGIN + 80, NAV_Y + NAV_H, BACK))
        if self.pages() > 1:
            text_centered(BOTTOM, NAV_Y + 3, "%d/%d" % (self.page() + 1, self.pages()),
                          nds.FONT_BODY, t["label"], 96, 40)
            if self.page() > 0:
                button(BOTTOM, 140, NAV_Y, 52, NAV_H, _PREV_LABEL, font=nds.FONT_BODY_BOLD)
                self.hits.append((140, NAV_Y, 192, NAV_Y + NAV_H, "prev"))
            if self.page() < self.pages() - 1:
                button(BOTTOM, 196, NAV_Y, 52, NAV_H, _NEXT_LABEL, font=nds.FONT_BODY_BOLD)
                self.hits.append((196, NAV_Y, 248, NAV_Y + NAV_H, "next"))
        nds.gfx_present(BOTTOM)

    def _hit(self, x, y):
        for x0, y0, x1, y1, action in self.hits:
            if x0 <= x < x1 and y0 <= y < y1:
                return action
        return None

    def handle_frame(self):
        """Processes one frame of input. Returns an index, BACK or None."""
        tap = self.taps.update()
        if tap is not None:
            action = self._hit(tap[0], tap[1])
            if action == "prev":
                self.selected = (self.page() - 1) * self.per_page
                self.draw()
                if self.on_page is not None:
                    self.on_page()
                return None
            if action == "next":
                self.selected = (self.page() + 1) * self.per_page
                self.draw()
                if self.on_page is not None:
                    self.on_page()
                return None
            return action
        down = nds.keys_down()
        if not down:
            return None
        if down & nds.KEY_A and self.labels:
            return self.selected
        if down & nds.KEY_B and self.show_back:
            return BACK
        if down & (nds.KEY_UP | nds.KEY_DOWN) and self.labels:
            step = -1 if down & nds.KEY_UP else 1
            page = self.page()
            self.selected = (self.selected + step) % len(self.labels)
            self.draw()
            if self.page() != page and self.on_page is not None:
                self.on_page()
        return None

    def run(self):
        self.draw()
        while True:
            nds.frame()
            if nds_dev is not None and nds.keys_down() & nds.KEY_SELECT:
                nds_dev.diagnostics()
                if self.redraw is not None:
                    self.redraw()
                self.draw()
                continue
            result = self.handle_frame()
            if result is not None:
                return result
