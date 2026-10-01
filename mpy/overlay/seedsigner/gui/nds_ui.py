# NDS-Signer - text UI primitives for the dual-screen DSi.
#
# Top screen: information (title, status, body text, live camera, QR codes).
# Bottom screen: touch buttons; the D-pad + A also work, B goes back.
# Everything is drawn with the `nds` module (native) or its host simulator.
from gettext import gettext as _

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


def sound(kind):
    """A UI feedback sound (click, key, back, success, warning, error,
    scan) unless the "Sound effects" setting is disabled."""
    from seedsigner.gui import SETTING__NDS_SOUND
    from seedsigner.models.settings import Settings, SettingsConstants
    try:
        enabled = Settings.get_instance().get_value(SETTING__NDS_SOUND) == SettingsConstants.OPTION__ENABLED
    except Exception:
        enabled = True
    if enabled:
        nds.sound(getattr(nds, "SFX_" + kind.upper()))


def theme_color(name):
    """0xRRGGBB of an upstream GUIConstants colour, e.g. "WARNING_COLOR"."""
    from seedsigner.gui.components import GUIConstants
    return _rgb(getattr(GUIConstants, name))


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
#   ("mono_small", text)         smaller fixed-width, left-aligned, wrapped
#   ("large", text[, color])     large text, centred (amounts, words)
#   ("amount", sats)             bitcoin amount: network-coloured icon, digits, unit
#   ("kv", label, value[, color]) label on the left, value on the right
#   ("rule",)                    thin horizontal line
#   ("address", text)            fixed-width address, ends highlighted
#   ("status", kind, text)       small icon + text; kind: success/warning/error
#   ("space", pixels)
def _text_rows(rows, text, font, color, centred, width):
    line_h = nds.gfx_font_metrics(font)[1]
    fits = "\n" not in text and nds.gfx_text_width(text, font) <= width
    for line in [text] if fits else wrap_px(text, font, width):
        def draw(y, line=line):
            if centred:
                text_centered(TOP, y, line, font, color, MARGIN, width)
            else:
                nds.gfx_text(TOP, MARGIN, y, line, font, color, width)
        rows.append((line_h, draw))


def _amount_row(rows, sats):
    t = theme()
    text, unit, color = format_btc(sats)
    icon = _icons().BITCOIN_ALT
    icon_font, digits_font, unit_font = nds.FONT_SSICON_LARGE, nds.FONT_LARGE, nds.FONT_BODY_BOLD
    height = nds.gfx_font_metrics(digits_font)[1]

    def draw(y):
        widths = [nds.gfx_text_width(icon, icon_font) + 6, nds.gfx_text_width(text, digits_font) + 5,
                  nds.gfx_text_width(unit, unit_font)]
        x = (GFX_W - sum(widths)) // 2
        icon_h = nds.gfx_font_metrics(icon_font)[1]
        nds.gfx_text(TOP, x, y + (height - icon_h) // 2 + 1, icon, icon_font, color)
        x += widths[0]
        nds.gfx_text(TOP, x, y, text, digits_font, t["body"])
        x += widths[1]
        a_digits = nds.gfx_font_metrics(digits_font)[0]
        a_unit = nds.gfx_font_metrics(unit_font)[0]
        nds.gfx_text(TOP, x, y + a_digits - a_unit, unit, unit_font, t["label"])
    rows.append((height + 2, draw))


def _kv_row(rows, label, value, color, width):
    t = theme()
    font = nds.FONT_BODY
    height = nds.gfx_font_metrics(font)[1] + 2

    def draw(y):
        nds.gfx_text(TOP, MARGIN + 8, y, label, font, t["label"], width // 2)
        w = nds.gfx_text_width(value, nds.FONT_BODY_BOLD)
        nds.gfx_text(TOP, GFX_W - MARGIN - 8 - w, y, value, nds.FONT_BODY_BOLD, color_value(color, t["body"]))
    rows.append((height, draw))


def _address_rows(rows, address, width):
    """Fixed-width address, its first and last 7 characters in the accent
    colour (like upstream's FormattedAddress), centred."""
    t = theme()
    font = nds.FONT_MONO_BOLD
    char_w = nds.gfx_text_width("0", font)
    per_line = width // char_w
    # balanced lines (e.g. 21 + 21, not 30 + 12): easier to compare in chunks
    count = max(1, (len(address) + per_line - 1) // per_line)
    per_line = (len(address) + count - 1) // count or 1
    lines = [address[i:i + per_line] for i in range(0, len(address), per_line)] or [""]
    line_h = nds.gfx_font_metrics(font)[1]
    for n, line in enumerate(lines):
        start = n * per_line

        def draw(y, line=line, start=start):
            x = (GFX_W - len(line) * char_w) // 2
            for i, ch in enumerate(line):
                pos = start + i
                accent = pos < 7 or pos >= len(address) - 7
                nds.gfx_text(TOP, x + i * char_w, y, ch, font, t["accent"] if accent else t["body"])
        rows.append((line_h, draw))


def _status_row(rows, kind, text, width):
    from seedsigner.gui.components import GUIConstants as GC
    icons = _icons()
    icon, color = {"success": (icons.SUCCESS, GC.SUCCESS_COLOR),
                   "warning": (icons.WARNING, GC.WARNING_COLOR),
                   "error": (icons.ERROR, GC.ERROR_COLOR)}[kind]
    color = _rgb(color)
    font = nds.FONT_BODY_BOLD
    height = nds.gfx_font_metrics(font)[1] + 2

    def draw(y):
        w = nds.gfx_text_width(icon, nds.FONT_SSICON) + 6 + nds.gfx_text_width(text, font)
        x = (GFX_W - w) // 2
        nds.gfx_text(TOP, x, y + 1, icon, nds.FONT_SSICON, color)
        nds.gfx_text(TOP, x + nds.gfx_text_width(icon, nds.FONT_SSICON) + 6, y, text, font, color)
    rows.append((height, draw))


def _icons():
    from seedsigner.gui.components import SeedSignerIconConstants
    return SeedSignerIconConstants


def _layout(blocks, width):
    """(height, draw(y)) rows for the blocks (see above)."""
    t = theme()
    rows = []
    for block in blocks:
        kind = block[0]
        if kind == "space":
            rows.append((block[1], None))
        elif kind == "rule":
            rows.append((7, lambda y: nds.gfx_rect(TOP, MARGIN + 8, y + 3, GFX_W - 2 * MARGIN - 16, 1,
                                                   t["inactive"])))
        elif kind == "amount":
            _amount_row(rows, block[1])
        elif kind == "kv":
            _kv_row(rows, block[1], block[2], block[3] if len(block) > 3 else None, width)
        elif kind == "address":
            if block[1]:
                _address_rows(rows, block[1], width)
        elif kind == "status":
            _status_row(rows, block[1], block[2], width)
        elif kind == "bar":  # ("bar", label, fraction 0..1[, colour]): a progress bar
            def draw(y, label=block[1], frac=block[2], color=block[3] if len(block) > 3 else None):
                nds.gfx_text(TOP, MARGIN + 8, y, label, nds.FONT_BODY, t["label"], 96)
                x0, w = MARGIN + 110, GFX_W - 2 * MARGIN - 118
                nds.gfx_rect(TOP, x0, y + 6, w, 6, t["inactive"], 3)
                fill = int(w * min(max(frac, 0), 1))
                if fill:
                    nds.gfx_rect(TOP, x0, y + 6, max(fill, 6), 6, color_value(color, t["accent"]), 3)
            rows.append((nds.gfx_font_metrics(nds.FONT_BODY)[1] + 4, draw))
        elif kind == "qr":  # ("qr", text, px[, caption]): a QR code in a px x px square
            def draw(y, text=block[1], px=block[2], caption=block[3] if len(block) > 3 else ""):
                x = (GFX_W - px) // 2
                nds.qr_draw(TOP, text, x, y, px)
                if caption:  # e.g. an address index, left of the code
                    line_h = nds.gfx_font_metrics(nds.FONT_LARGE)[1]
                    text_centered(TOP, y + (px - line_h) // 2, caption, nds.FONT_LARGE,
                                  t["accent"], 0, x)
            rows.append((block[2], draw))
        elif kind == "icon":
            if block[1]:
                font = icon_font(block[1])
                color = color_value(block[2] if len(block) > 2 else None, t["accent"])

                def draw(y, glyph=block[1], font=font, color=color):
                    text_centered(TOP, y, glyph, font, color)
                rows.append((nds.gfx_font_metrics(font)[1] + 4, draw))
        else:
            text = block[1]
            if text is None or text == "":
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
            color = color_value(block[2] if len(block) > 2 else None, default)
            _text_rows(rows, text, font, color, centred, width)
    return rows


def network_badge(always=False, draw=True):
    """Which network the signer is set to, on the top screen: on testnet and
    regtest always (a thin band along the top edge in the network's colour
    and its name in the top-right corner, beside the title); on mainnet only
    when `always` (transaction screens: signing moves real money). Returns
    the badge's width (0 if none), so the title can make room for it."""
    from seedsigner.gui.components import GUIConstants as GC
    from seedsigner.models.settings import Settings, SettingsConstants as SC
    network = Settings.get_instance().get_value(SC.SETTING__NETWORK)
    if network == SC.MAINNET:
        if not always:
            return 0
        name, color = "Mainnet", _rgb(GC.ACCENT_COLOR)
    elif network == SC.TESTNET:
        name, color = "Testnet", _rgb(GC.TESTNET_COLOR)
    else:
        name, color = "Regtest", _rgb(GC.REGTEST_COLOR)
    font = nds.FONT_BODY_BOLD
    w = nds.gfx_text_width(name, font) + 12
    if not draw:
        return w
    if network != SC.MAINNET:
        nds.gfx_rect(TOP, 0, 0, GFX_W, 2, color)
    h = nds.gfx_font_metrics(font)[1]
    nds.gfx_rect(TOP, GFX_W - w - 4, 6, w, h, color, 6)
    nds.gfx_text(TOP, GFX_W - w + 2, 6, name, font, theme()["bg"])
    return w


LOW_BATTERY_LEVEL = 3  # DSi levels 0-15; DS mode reports only 3 (low) or 15


def battery_low():
    """True when the battery is low and the console is not charging."""
    level, charging = nds.battery()
    return level <= LOW_BATTERY_LEVEL and not charging


def low_battery_blocks():
    """A warning line for screens before signing or showing secrets."""
    if not battery_low():
        return []
    return [("space", 6), ("status", "error", _("Low battery: plug in the charger"))]


def battery_badge(draw=True):
    """A red battery in the top-left corner while the battery is low.
    Returns its width (0 if not shown), so the title can make room."""
    if not battery_low():
        return 0
    if draw:
        from seedsigner.gui.components import GUIConstants as GC
        red = _rgb(GC.ERROR_COLOR)
        nds.gfx_frame(TOP, 6, 9, 20, 11, red, 2, 1)       # body
        nds.gfx_rect(TOP, 26, 12, 2, 5, red)               # terminal
        nds.gfx_rect(TOP, 8, 11, 4, 7, red)                # what is left
    return 28


def _title(title, network_always=False):
    """The title, centred, or between the low battery icon and the network
    badge when they are shown."""
    t = theme()
    badge = network_badge(network_always, draw=False)
    left = battery_badge(draw=False)
    if title:
        room = GFX_W - (badge + 12 if badge else 0)
        w = nds.gfx_text_width(title, nds.FONT_TITLE)
        x = max((GFX_W - w) // 2, left + 4 if left else 0)
        if badge and x + w > room:
            x = max(left + 4 if left else 4, room - w)
        nds.gfx_text(TOP, x, TITLE_Y, title, nds.FONT_TITLE, t["body"], room - x)
    network_badge(network_always)
    battery_badge()


def top_blocks(title, blocks, network_always=False):
    """Title, then `blocks` (see above) centred vertically below it."""
    t = theme()
    nds.top_clear()
    nds.gfx_clear(TOP, t["bg"])
    _title(title, network_always)
    rows = _layout(blocks, GFX_W - 2 * MARGIN)
    total = sum(r[0] for r in rows)
    y = BODY_Y + max(0, (GFX_H - BODY_Y - total) // 2 - 6)
    for height, draw in rows:
        if draw is not None:
            draw(y)
        y += height
    nds.gfx_present(TOP)


def group_thousands(n):
    s = str(int(n))
    out = ""
    while len(s) > 3:
        out = "," + s[-3:] + out
        s = s[:-3]
    return s + out


def format_btc(total_sats):
    """(digits, unit, icon colour) like upstream's BtcAmount: the Settings'
    denomination (sats, btc, threshold at 0.01 btc, btc|sats hybrid) and
    the network (testnet/regtest units and colours)."""
    from seedsigner.gui.components import GUIConstants as GC
    from seedsigner.models.settings import Settings, SettingsConstants as SC
    settings = Settings.get_instance()
    denomination = settings.get_value(SC.SETTING__BTC_DENOMINATION)
    network = settings.get_value(SC.SETTING__NETWORK)
    btc_unit, sats_unit = _("tBtc"), _("tSats")
    color = GC.TESTNET_COLOR if network == SC.TESTNET else GC.REGTEST_COLOR
    if network == SC.MAINNET:
        btc_unit, sats_unit, color = _("btc"), _("sats"), GC.ACCENT_COLOR
    total = int(total_sats)
    as_btc = (denomination == SC.BTC_DENOMINATION__BTC
              or (denomination == SC.BTC_DENOMINATION__THRESHOLD and total >= 10 ** 6)
              or (denomination == SC.BTC_DENOMINATION__BTCSATSHYBRID and total >= 10 ** 6
                  and total % 10 ** 6 == 0)
              or total > 10 ** 10)
    if as_btc:
        whole, frac = divmod(total, 10 ** 8)
        frac = "%08d" % frac
        if total % 10 ** 8 == 0:
            frac = frac[:1]
        elif total % 10 ** 6 == 0:
            frac = frac[:2]
        text = group_thousands(whole) + "." + frac
        if len(text) >= 12:
            text = text.split(".")[0] + "." + frac[:2] + "..."
        return text, btc_unit, _rgb(color)
    if denomination == SC.BTC_DENOMINATION__BTCSATSHYBRID:
        return "%d.%02d | %s" % (total // 10 ** 8, total % 10 ** 8 // 10 ** 6,
                                  group_thousands(total % 10 ** 6)), sats_unit, _rgb(color)
    return group_thousands(total), sats_unit, _rgb(color)


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
    _title(title)
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
                 on_page=None, on_select=None, tap_selects=False, content=None):
        self.redraw = redraw  # redraws the top screen after the dev overlay
        self.taps = TapTracker()
        self.labels = list(labels)
        self.show_back = show_back
        self.selected = selected if 0 <= selected < len(self.labels) else 0
        self.header = header
        self.checked = set(checked)
        self.on_page = on_page  # called after the page changes (top screen follows)
        # called after the selection changes (top screen shows the selected item)
        self.on_select = on_select
        # a tap on another button selects it; a tap on the selected one chooses it
        self.tap_selects = tap_selects
        # content(index, x, y, w, h, selected) draws a button's label itself
        self.content = content
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
            selected = start + i == self.selected
            button(BOTTOM, MARGIN, y, GFX_W - 2 * MARGIN, BUTTON_H,
                   "" if self.content else label, selected, checked=start + i in self.checked)
            if self.content:
                self.content(start + i, MARGIN, y, GFX_W - 2 * MARGIN, BUTTON_H, selected)
            self.hits.append((MARGIN, y, GFX_W - MARGIN, y + BUTTON_H, start + i))
            y += BUTTON_H + BUTTON_GAP
        if self.show_back:
            button(BOTTOM, MARGIN, NAV_Y, 80, NAV_H, _(_BACK_LABEL), font=nds.FONT_BODY_BOLD)
            self.hits.append((MARGIN, NAV_Y, MARGIN + 80, NAV_Y + NAV_H, BACK))
        if self.pages() > 1:
            text_centered(BOTTOM, NAV_Y + 3, "%d/%d" % (self.page() + 1, self.pages()),
                          nds.FONT_BODY, t["label"], 96, 40)
            from seedsigner.gui.components import SeedSignerIconConstants as Icons
            if self.page() > 0:  # chevrons: the same in every language
                button(BOTTOM, 140, NAV_Y, 52, NAV_H, Icons.CHEVRON_LEFT, font=nds.FONT_SSICON)
                self.hits.append((140, NAV_Y, 192, NAV_Y + NAV_H, "prev"))
            if self.page() < self.pages() - 1:
                button(BOTTOM, 196, NAV_Y, 52, NAV_H, Icons.CHEVRON_RIGHT, font=nds.FONT_SSICON)
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
            if action is not None:
                sound("back" if action == BACK else ("key" if action in ("prev", "next") else "click"))
            if action == "prev":
                self.selected = (self.page() - 1) * self.per_page
                self.draw()
                self._moved(True)
                return None
            if action == "next":
                self.selected = (self.page() + 1) * self.per_page
                self.draw()
                self._moved(True)
                return None
            if self.tap_selects and isinstance(action, int) and action != self.selected:
                self.selected = action
                self.draw()
                self._moved(False)
                return None
            return action
        down = nds.keys_down()
        if not down:
            return None
        if down & nds.KEY_A and self.labels:
            sound("click")
            return self.selected
        if down & nds.KEY_B and self.show_back:
            sound("back")
            return BACK
        if down & (nds.KEY_UP | nds.KEY_DOWN) and self.labels:
            sound("key")
            step = -1 if down & nds.KEY_UP else 1
            page = self.page()
            self.selected = (self.selected + step) % len(self.labels)
            self.draw()
            self._moved(self.page() != page)
        return None

    def _moved(self, new_page):
        if self.on_select is not None:
            self.on_select()
        elif new_page and self.on_page is not None:
            self.on_page()

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
