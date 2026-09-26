# NDS-Signer - AUTOTEST builds only: drives the UI with a script of taps.
#
# Wraps the native `nds` module: output goes to the real screens and is also
# kept in a text shadow, so a "tap by label" can find the button on screen.
# A tap waits until its label is visible (e.g. while the camera is scanning).
# Never included in release builds (see mpy/manifest.py).
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

    def bottom_clear(self):
        self._n.bottom_clear()
        self._shadow = [" " * COLS for _ in range(ROWS)]

    def _find(self, label):
        for row, line in enumerate(self._shadow):
            col = line.find(label)
            if col >= 0:
                return col * 8 + len(label) * 4, row * 8 + 4
        return None

    def frame(self):
        self._n.frame()
        self._keys = 0
        if self._release:
            self._release = False
            self._touch = None
            return
        if not self._events:
            return
        kind, arg = self._events[0]
        if kind == "tap_label":
            xy = self._find(arg)
            if xy is None:
                return  # wait for it to appear
            print("autopilot: tap", arg)
            self._touch = xy
            self._keys = self._n.KEY_TOUCH
            self._release = True
        elif kind == "key":
            self._keys = arg
        elif kind == "log":
            print("autopilot:", arg)
        elif kind == "exec":  # test setup that a user would do by hand
            exec(arg, {})
        self._events.pop(0)

    def keys_down(self):
        return self._keys | self._n.keys_down()

    def touch(self):
        return self._touch if self._touch is not None else self._n.touch()
