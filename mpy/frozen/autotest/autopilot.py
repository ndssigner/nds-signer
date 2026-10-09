# NDS-Signer - AUTOTEST builds only: drives the UI with a script of taps.
#
# Wraps the native `nds` module: output goes to the real screens and is also
# kept in a text shadow, so a "tap by label" can find the button on screen.
# A tap waits until its label is visible (e.g. while the camera is scanning).
# Never included in release builds (see mpy/manifest.py).
try:
    import autopilot_dev as autopilot_script
except ImportError:
    try:
        import autopilot_tones as autopilot_script
    except ImportError:
        import autopilot_script

COLS, ROWS = 32, 24


class Autopilot:
    def __init__(self, native):
        self._n = native
        self._shadow = [" " * COLS for _ in range(ROWS)]
        self._events = list(autopilot_script.EVENTS)
        self._keys = 0
        self._touch = None
        self._release = False

    def __getattr__(self, name):
        return getattr(self._n, name)

    def bottom_print(self, row, col, text):
        self._n.bottom_print(row, col, text)
        text = str(text)[:COLS]
        if 0 <= row < ROWS:
            if col < 0:
                col = (COLS - len(text)) // 2
            line = self._shadow[row]
            self._shadow[row] = (line[:col] + text + line[col + len(text):])[:COLS]

    def gfx_text(self, screen, x, y, text, font, rgb, max_width=0):
        # graphical labels go to the shadow too (cell of their first pixel,
        # like the host simulator), so taps by label keep working
        width = self._n.gfx_text(screen, x, y, text, font, rgb, max_width)
        if screen == 1 and font not in (self._n.FONT_ICON, self._n.FONT_ICON_LARGE,
                                        self._n.FONT_SSICON, self._n.FONT_SSICON_LARGE,
                                        self._n.FONT_SSICON_HUGE):
            line_height = self._n.gfx_font_metrics(font)[1]
            self._shadow_put((y + line_height // 2) // 8, x // 8, str(text))
        return width

    def _shadow_put(self, row, col, text):
        text = text[:COLS]
        if 0 <= row < ROWS and 0 <= col < COLS:
            line = self._shadow[row]
            self._shadow[row] = (line[:col] + text + line[col + len(text):])[:COLS]

    def bottom_clear(self):
        self._n.bottom_clear()
        self._shadow = [" " * COLS for _ in range(ROWS)]

    def _find(self, label):
        for row, line in enumerate(self._shadow):
            col = line.find(label)
            if col >= 0:
                return col * 8 + len(label) * 4, row * 8 + 4
        return None

    def _status(self, text):
        # visible progress on the top screen's last row (AUTOTEST builds only)
        self._n.top_print(23, 0, (text + " " * 32)[:32])

    def frame(self):
        self._n.frame()
        self._frames = getattr(self, "_frames", 0) + 1
        self._keys = 0
        if self._release:
            self._release = False
            self._touch = None
            return
        if not self._events:
            return
        kind, arg = self._events[0]
        self._status("AP %d left f%d %s %s" % (len(self._events), self._frames, kind, str(arg)[:10]))
        if kind == "tap_label":
            xy = self._find(arg)
            if xy is None:
                return  # wait for it to appear
            print("autopilot: tap", arg)
            self._touch = xy
            self._keys = self._n.KEY_TOUCH
            self._release = True
        elif kind == "tap_key":
            from seedsigner.gui.nds_keyboard import key_center
            self._touch = key_center(arg)
            self._keys = self._n.KEY_TOUCH
            self._release = True
        elif kind == "key":
            self._keys = arg
        elif kind == "wait":  # hold for n frames (e.g. for screenshots)
            if arg > 1:
                self._events[0] = ("wait", arg - 1)
                return
        elif kind == "log":
            print("autopilot:", arg)
        elif kind == "exec":  # test setup that a user would do by hand
            exec(arg, {})
        self._events.pop(0)

    def keys_down(self):
        return self._keys | self._n.keys_down()

    def touch(self):
        return self._touch if self._touch is not None else self._n.touch()
