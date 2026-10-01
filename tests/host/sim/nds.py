# NDS-Signer - host simulator of the native `nds` module
# (mpy/usermods/nds/modnds.c). Same API, so the Python app and SeedSigner's
# views can be driven headlessly on the host (MicroPython unix port or
# CPython) with scripted input and a fake camera.
#
#   import nds
#   nds.sim_script([("tap_label", "Scan"), ("camera", b"cHNidP8..."), ...])
#   nds.sim_dump()   # prints both text screens
import builtins

# A DS has no /proc (SeedSigner reads the Pi's serial number from
# /proc/cpuinfo and must cope with its absence): hide the host's.
_host_open = builtins.open


def _open(path, *args, **kwargs):
    if isinstance(path, str) and path.startswith("/proc/"):
        raise OSError(2, "no /proc on a DS")
    return _host_open(path, *args, **kwargs)


builtins.open = _open

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
# Touch readings for the coming frames. Like a real DSi (not like melonDS),
# the first frame of a touch reads (0, 0): the position is not stable yet.
_touch_queue = []
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


# Display lists: what each screen shows since its last clear, as drawing
# operations; sim_snapshot() saves them for tools/dev/render_gallery.py.
_dl = [[], []]
snapshot_dir = None


def top_print(row, col, text):
    _dl[0].append(("console", row, col, str(text)))
    _print(0, row, col, text)


def bottom_print(row, col, text):
    _dl[1].append(("console", row, col, str(text)))
    _print(1, row, col, text)


def top_clear():
    _screens[0] = [" " * COLS for _ in range(ROWS)]
    _dl[0] = []


def bottom_clear():
    _screens[1] = [" " * COLS for _ in range(ROWS)]
    _dl[1] = []


def sim_snapshot(name):
    """Saves both screens' display lists as <snapshot_dir>/<name>.json."""
    if snapshot_dir is None:
        return
    import json
    with open("%s/%s.json" % (snapshot_dir, name), "w") as f:
        f.write(json.dumps({"top": _dl[0], "bottom": _dl[1]}))


def _find_label(label):
    for row, line in enumerate(_screens[1]):
        col = line.find(label)
        if col >= 0:
            return col * 8 + len(label) * 4, row * 8 + 4
    raise AssertionError("label %r not on the bottom screen:\n%s" % (label, sim_text(1)))


def _start_touch(x, y):
    global _touch_xy, _keys_down
    _touch_queue[:] = [(x, y), (x, y)]
    _touch_xy = (0, 0)
    _keys_down = KEY_TOUCH


def frame():
    global _keys_down, _touch_xy, _ticks, _idle_frames
    _ticks += 16
    _keys_down = 0
    if _touch_queue:  # stylus still down: next reading
        _touch_xy = _touch_queue.pop(0)
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
        _start_touch(ev[1], ev[2])
    elif kind == "tap_key":  # a letter of the touch keyboard
        from seedsigner.gui.nds_keyboard import key_center
        _start_touch(*key_center(ev[1]))
    elif kind == "tap_label":
        _start_touch(*_find_label(ev[1]))
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
    return KEY_TOUCH if _touch_xy is not None else 0


def touch():
    return _touch_xy


def ticks_ms():
    return _ticks


def camera_init():
    return True


camera_front = False  # camera of the last camera_start(), for tests
_camera_decode = True


def camera_start(front=False):
    global _camera_on, camera_front, _camera_decode
    _camera_on, camera_front, _camera_decode = True, bool(front), True
    _dl[0].append(("camera",))
    return True


CAMERA_FRAME_BYTES = 640 * 480 * 2
camera_grabbed = [0]  # frames handed out by camera_grab, for tests
sim_flat_frames = 0   # the next n frames grabbed are flat (all pixels identical)


def camera_grab(buf):
    """A new frame on every call while the camera is on: a different
    pattern each time, like a real sensor's noise."""
    global sim_flat_frames
    if not _camera_on:
        return 0
    camera_grabbed[0] += 1
    n = camera_grabbed[0]
    if sim_flat_frames:
        sim_flat_frames -= 1
        for i in range(0, len(buf), 4096):
            buf[i:i + 4096] = bytes(min(4096, len(buf) - i))
        return 2
    for i in range(0, len(buf), 4096):
        buf[i] = (n * 131 + i) & 255
    buf[1] = n & 255
    buf[2] = (n >> 8) & 255
    return 1


def camera_running():
    return _camera_on


def frame_show(screen, frame):
    _dl[screen].append(("camera",))


def camera_decode(on):
    global _camera_decode
    _camera_decode = bool(on)


def camera_poll():
    global _camera_frames
    if not _camera_on or not _camera_decode or not _camera_queue:
        return None
    _camera_frames += 1
    return _camera_queue.pop(0)


def camera_stop():
    global _camera_on
    _camera_on = False


def camera_stats():
    return (_camera_frames, 0, _camera_frames, _camera_frames, 0, 0, 0, _ticks, 0, 0)


def scan_benchmark(text, pixels):
    return None


qr_shown = []  # texts passed to qr_show, for tests


def qr_show(text, border=2, background=255):
    qr_shown.append(text)
    _dl[0] = [op for op in _dl[0] if op[0] != "qr"] + [("qr", text, border, background)]
    return 1


qr_transcribed = []  # (data, zone_modules, zone_x, zone_y) per qr_transcribe call

qr_drawn = []  # the last texts drawn by qr_draw, for tests


def qr_draw(screen, text, x, y, px):
    qr_drawn[:] = qr_drawn[-9:] + [text]  # bounded: the crawler draws thousands
    _dl[screen].append(("qrdraw", text, x, y, px))
    return 21 if len(text) <= 25 else 29 if len(text) <= 77 else 33


def qr_transcribe_map(screen, x, y, scale, zone_modules, zone_x, zone_y):
    if qr_transcribed:
        data = qr_transcribed[-1][0]
        shown = data if isinstance(data, str) else "hex:" + "".join("%02x" % b for b in data)
        _dl[screen].append(("qrmap", shown, x, y, scale, zone_modules, zone_x, zone_y))


# QR capacities at ECC level L, versions 1-4 (SeedQRs are 21x21 to 29x29)
_CAPACITY_L = {"numeric": (41, 77, 127, 187), "byte": (17, 32, 53, 78)}


def qr_transcribe(data, zone_modules=0, zone_x=0, zone_y=0):
    qr_transcribed.append((data, zone_modules, zone_x, zone_y))
    shown = data if isinstance(data, str) else "hex:" + "".join("%02x" % b for b in data)
    _dl[0].append(("transcribe", shown, zone_modules, zone_x, zone_y))
    if isinstance(data, str) and data.isdigit():
        caps, n = _CAPACITY_L["numeric"], len(data)
    else:
        caps, n = _CAPACITY_L["byte"], len(data)
    for version, cap in enumerate(caps, 1):
        if n <= cap:
            return 17 + 4 * version
    return 0


# ---- graphical UI (arm9/include/gfx.h) ----
# Font ids, (ascent, line height) and an average advance per character, in
# the order of build/generated/gfx_fonts.h (tools/ttf_to_ndsfont.py FONTS);
# tests/host/gfx_sim_check.py compares the metrics with the generated file.
(FONT_BODY, FONT_BODY_BOLD, FONT_BUTTON, FONT_TITLE, FONT_LARGE, FONT_MONO, FONT_MONO_SMALL,
 FONT_MONO_BOLD, FONT_ICON, FONT_ICON_LARGE, FONT_SSICON, FONT_SSICON_LARGE,
 FONT_SSICON_HUGE) = range(13)
FONT_METRICS = [(14, 18), (14, 18), (17, 22), (19, 24), (26, 34), (13, 16), (11, 14), (14, 18),
                (14, 16), (23, 27), (15, 16), (25, 27), (42, 45)]
_FONT_ADVANCE = [7, 7, 8, 9, 13, 7, 6, 8, 16, 26, 16, 26, 44]
_ICON_FONTS = (FONT_ICON, FONT_ICON_LARGE, FONT_SSICON, FONT_SSICON_LARGE, FONT_SSICON_HUGE)


def gfx_clear(screen, rgb):
    if screen == 0:
        top_clear()
    else:
        bottom_clear()
    _dl[screen].append(("clear", rgb))


def gfx_rect(screen, x, y, w, h, rgb, radius=0):
    _dl[screen].append(("rect", x, y, w, h, rgb, radius))


def gfx_frame(screen, x, y, w, h, rgb, radius=0, thickness=1):
    _dl[screen].append(("frame", x, y, w, h, rgb, radius, thickness))


def gfx_text(screen, x, y, text, font, rgb, max_width=0):
    """Text also goes to the text grid (cell of its first pixel), so tests
    can find labels and tap them as on the text UI."""
    _dl[screen].append(("text", x, y, str(text), font, rgb, max_width))
    width = gfx_text_width(text, font)
    if max_width and width > max_width:
        text = text[:max(0, max_width // _FONT_ADVANCE[font])]
        width = gfx_text_width(text, font)
    if font not in _ICON_FONTS:
        line_height = FONT_METRICS[font][1]
        _print(screen, (y + line_height // 2) // 8, x // 8, text)
    return width


def gfx_text_width(text, font):
    return len(text) * _FONT_ADVANCE[font]


def gfx_font_metrics(font):
    return FONT_METRICS[font]


def gfx_present(screen):
    pass


SFX_CLICK, SFX_KEY, SFX_BACK, SFX_SUCCESS, SFX_WARNING, SFX_ERROR, SFX_SCAN = range(7)
sounds = []  # effects played, for tests


def sound(effect):
    sounds.append(effect)


system_language_value = 1  # English; tests may change it


def system_language():
    return system_language_value


def info():
    return (True, True, 0, _ticks // 1000)


def version():
    return "sim"


# ---- simulator controls (not part of the native API) ----

def sim_script(events):
    _events.extend(events)


def sim_camera(payloads):
    _camera_queue.extend(payloads)


# box-drawing glyphs of the NDS font (see nds_ui.BOX_*) shown as ASCII
_BOX_ASCII = {"\x10": "-", "\x11": "|", "\x12": "+", "\x13": "+", "\x14": "+", "\x15": "+",
              "\x16": "=", "\x17": "#", "\x18": "#", "\x19": "#", "\x1a": "#", "\x1c": "#"}


def sim_text(screen):
    border = "+" + "-" * COLS + "+"
    lines = ["".join(_BOX_ASCII.get(c, c) for c in line) for line in _screens[screen]]
    return "\n".join([border] + ["|" + line + "|" for line in lines] + [border])


def sim_dump():
    print(sim_text(0))
    print(sim_text(1))
