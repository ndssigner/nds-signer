# NDS-Signer - host simulator of the native `nds` module
# (mpy/usermods/nds/modnds.c). Same API, so the Python app and SeedSigner's
# views can be driven headlessly on the host (MicroPython unix port or
# CPython) with scripted input and a fake camera.
#
#   import nds
#   nds.sim_script([("tap_label", "Scan"), ("camera", b"cHNidP8..."), ...])
#   nds.sim_dump()   # prints both text screens
COLS = 32
ROWS = 24

KEY_A = 1 << 0
KEY_B = 1 << 1
KEY_SELECT = 1 << 2
KEY_START = 1 << 3
KEY_RIGHT = 1 << 4
KEY_LEFT = 1 << 5
KEY_UP = 1 << 6
KEY_DOWN = 1 << 7
KEY_R = 1 << 8
KEY_L = 1 << 9
KEY_X = 1 << 10
KEY_Y = 1 << 11
KEY_TOUCH = 1 << 12

_screens = [[" " * COLS for _ in range(ROWS)], [" " * COLS for _ in range(ROWS)]]
_events = []
_camera_queue = []
_keys_down = 0
_touch_xy = None
_ticks = 0
_idle_frames = 0
_camera_on = False
_camera_frames = 0
MAX_IDLE_FRAMES = 20000  # a stuck test fails instead of hanging
trace = []  # screens seen, for assertions


def _print(screen, row, col, text):
    text = str(text)
    if row < 0 or row >= ROWS:
        return
    text = text[:COLS]
    if col < 0:
        col = (COLS - len(text)) // 2
    if col >= COLS:
        return
    text = text[:COLS - col]
    line = _screens[screen][row]
    _screens[screen][row] = line[:col] + text + line[col + len(text):]


def top_print(row, col, text):
    _print(0, row, col, text)


def bottom_print(row, col, text):
    _print(1, row, col, text)


def top_clear():
    _screens[0] = [" " * COLS for _ in range(ROWS)]


def bottom_clear():
    _screens[1] = [" " * COLS for _ in range(ROWS)]


def _find_label(label):
    for row, line in enumerate(_screens[1]):
        col = line.find(label)
        if col >= 0:
            return col * 8 + len(label) * 4, row * 8 + 4
    raise AssertionError("label %r not on the bottom screen:\n%s" % (label, sim_text(1)))


def frame():
    global _keys_down, _touch_xy, _ticks, _idle_frames
    _ticks += 16
    _keys_down = 0
    if _touch_xy is not None and _touch_xy[2] == "down":
        _touch_xy = (_touch_xy[0], _touch_xy[1], "up")  # release next frame
        return
    _touch_xy = None
    if not _events:
        _idle_frames += 1
        if _idle_frames > MAX_IDLE_FRAMES:
            raise RuntimeError("sim: input script exhausted\n" + sim_text(0) + "\n" + sim_text(1))
        return
    _idle_frames = 0
    ev = _events.pop(0)
    kind = ev[0]
    if kind == "key":
        _keys_down = ev[1]
    elif kind == "tap":
        _touch_xy = (ev[1], ev[2], "down")
        _keys_down = KEY_TOUCH
    elif kind == "tap_key":  # a letter of the touch keyboard
        from seedsigner.gui.nds_keyboard import key_center
        x, y = key_center(ev[1])
        _touch_xy = (x, y, "down")
        _keys_down = KEY_TOUCH
    elif kind == "tap_label":
        x, y = _find_label(ev[1])
        _touch_xy = (x, y, "down")
        _keys_down = KEY_TOUCH
    elif kind == "wait":  # let n frames pass
        if ev[1] > 1:
            _events.insert(0, ("wait", ev[1] - 1))
    elif kind == "camera":
        _camera_queue.append(ev[1])
    elif kind == "expect_top":
        if ev[1] not in sim_text(0):
            raise AssertionError("expected %r on the top screen:\n%s" % (ev[1], sim_text(0)))
    elif kind == "call":
        ev[1]()


def keys_down():
    return _keys_down


def keys_held():
    return KEY_TOUCH if _touch_xy is not None and _touch_xy[2] == "down" else 0


def touch():
    if _touch_xy is not None and _touch_xy[2] == "down":
        return (_touch_xy[0], _touch_xy[1])
    return None


def ticks_ms():
    return _ticks


def camera_init():
    return True


def camera_start():
    global _camera_on
    _camera_on = True
    return True


def camera_poll():
    global _camera_frames
    if not _camera_on or not _camera_queue:
        return None
    _camera_frames += 1
    return _camera_queue.pop(0)


def camera_stop():
    global _camera_on
    _camera_on = False


def camera_stats():
    return (_camera_frames, 0)


qr_shown = []  # texts passed to qr_show, for tests


def qr_show(text, border=2, background=255):
    qr_shown.append(text)
    return 1


# ---- simulator controls (not part of the native API) ----

def sim_script(events):
    _events.extend(events)


def sim_camera(payloads):
    _camera_queue.extend(payloads)


def sim_text(screen):
    border = "+" + "-" * COLS + "+"
    return "\n".join([border] + ["|" + line + "|" for line in _screens[screen]] + [border])


def sim_dump():
    print(sim_text(0))
    print(sim_text(1))
