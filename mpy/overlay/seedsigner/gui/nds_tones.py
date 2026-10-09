# NDS-Signer - listening to ur-tones (experimental): PSBTs, seeds and other
# URs sent as telephone tones, by cable or through the air
# (github.com/ndssigner/ur-tones). The audio and the frames are C
# (third_party/ur-tones/c, arm9/src/tones_audio.c); what is heard goes to
# SeedSigner's DecodeQR exactly as a scanned QR code: UR text as it is, and a
# seed as the digits of a Standard SeedQR, its PIN undone first.
from gettext import gettext as _

from seedsigner.gui.hw import nds
from seedsigner.gui import nds_keyboard, nds_ui

REPO = "github.com/ndssigner/ur-tones"
GAINS = ("20", "40", "80", "160")
KEYS = "0123456789ABCD*#"
# A made-up PIN (SPEC §4): 12 characters without 0/O, 1/I (60 bits), shown
# in groups of four; shorter PINs are accepted, with a warning
PIN_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
PIN_LENGTH = 12
_state = {"gain": 1}  # this session only
UT_PARITY = 32  # Reed-Solomon parity bytes per frame
_last = {"parts": 0}  # the multi-part UR's length, from the last frame


def seedqr_digits(entropy):
    """A Standard SeedQR's payload: each word's index in four digits."""
    from embit import bip39
    words = bip39.mnemonic_from_bytes(entropy).split()
    return "".join("%04d" % bip39.WORDLIST.index(w) for w in words)


def feed(decoder, group, pin):
    """Hands a group of tones heard to the decoder. Returns its status, or
    (None, bytes repaired or a negative error) when the group is not a frame
    or a seed that reads."""
    if group.startswith("*"):                       # keypad mode: a seed
        entropy, err = nds.tones_seed(group, pin or None)
        if entropy is None:
            return None, err
        return decoder.add_data(seedqr_digits(entropy).encode()), 0
    ur, fixed = nds.tones_frame_to_ur(group)
    if ur is None:
        return None, fixed
    seq = ur.split("/")
    if len(seq) == 3 and "-" in seq[1]:              # ur:<type>/<n>-<parts>/<body>
        try:
            _last["parts"] = int(seq[1].split("-")[1])
        except ValueError:
            pass
    if ur.startswith("ur:crypto-seed/") or ur.startswith("ur:seed/"):
        entropy, err = nds.tones_seed(ur, pin or None)
        if entropy is None:
            return None, err
        return decoder.add_data(seedqr_digits(entropy).encode()), fixed
    return decoder.add_data(ur.encode()), fixed


def frame_length(tones):
    """A frame's length in tones after its sync, from its first 12 tones
    (SPEC §2.1-2.2: the header gives the body's length); None until then, or
    if they do not read."""
    if len(tones) < 12:
        return None
    prev, value = KEYS.index("D"), 0
    for k in tones[:12]:
        if k not in KEYS:
            return None
        i = KEYS.index(k)
        d = (i - prev - 1) % 16
        if d == 15:                                  # a tone twice: an echo
            return None
        prev, value = i, value * 15 + d
    # 3 groups of 4 digits: 3 x 15 bits, the first 5 bytes and 5 bits more
    chunks = []
    for g in range(3):
        chunks.append(value % 50625)
        value //= 50625
    if any(c > 32767 for c in chunks):
        return None
    bits = (chunks[2] << 30) | (chunks[1] << 15) | chunks[0]
    header = [(bits >> (37 - 8 * b)) & 0xFF for b in range(5)]
    if header[0] >> 4:                               # version 0 only
        return None
    n = 3 + header[2] + UT_PARITY
    if header[1] == 0:                               # a named type
        n += 1 + header[3]
    groups = (8 * n + 14) // 15
    if 15 * groups - 8 * n >= 8:                     # the padding byte
        groups = (8 * (n + 1) + 14) // 15
    return 4 * groups


def make_pin():
    """A PIN made up from the microphone's noise (about a second of it,
    hashed with SHA-256: no pseudo-random generator). None if the microphone
    is not available."""
    import hashlib
    import struct
    if not nds.mic_start():
        return None
    h = hashlib.sha256(b"NDS-Signer ur-tones PIN v1")
    buf = bytearray(nds.MIC_BUFFER_BYTES)
    buffers = 0
    try:
        while buffers < 4:
            nds.frame()
            n, peak = nds.mic_take(buf)
            if n:
                h.update(buf)
                h.update(struct.pack("<I", nds.ticks_ms()))
                buffers += 1
    finally:
        nds.mic_stop()
    digest = h.digest()
    return "".join(PIN_ALPHABET[b % len(PIN_ALPHABET)] for b in digest[:PIN_LENGTH])


class PinScreen:
    """A PIN on the touch keyboard: letters and digits (SPEC §4), typed, or
    made up here for the other device. Returns it, or None for Back."""
    ROWS = ("1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM")

    def __init__(self, pin=""):
        self.pin = pin
        self.made_up = False
        self.keys = []
        for r, row in enumerate(self.ROWS):
            col = (nds_ui.COLS - len(row) * 3) // 2
            for i, ch in enumerate(row):
                self.keys.append(nds_keyboard.Key(ch, 3 + r * 3, col + i * 3))
        self.make_key = nds_keyboard.Key(_("Make one up"), 15, 1, width=16, action="make")
        self.del_key = nds_keyboard.Key(_("Del"), 15, 19, width=6, action="del")
        self.back_key = nds_keyboard.Key(_("< Back"), 20, 1, width=10, action="back")
        self.save_key = nds_keyboard.Key(_("Save"), 20, 21, width=10, action="save")

    def _all(self):
        return self.keys + [self.make_key, self.del_key, self.back_key, self.save_key]

    def _top(self):
        if self.made_up:
            notes = [("label", _("Made up from the microphone's noise.")),
                     ("text", _("Type it on the other device, without the spaces, then Save."))]
        elif self.pin and len(self.pin) < PIN_LENGTH:
            notes = [("text", _("A short PIN: fine by cable; for a backup or through the air, 12 characters or more.")),
                     ("label", _("Or make one up here, and type it there."))]
        else:
            notes = [("label", _("The same PIN as the other device. Letters and digits.")),
                     ("label", _("Or make one up here, and type it there.")),
                     ("label", _("A wrong PIN gives a different seed, without an error."))]
        shown = " ".join(self.pin[i:i + 4] for i in range(0, len(self.pin), 4))  # groups of four
        nds_ui.top_blocks(_("PIN"), [("large", shown or " "), ("space", 6)] + notes)

    def _draw(self):
        self._top()
        nds.bottom_clear()
        for key in self._all():
            nds_keyboard.draw_key(key)
        nds_keyboard.set_active(self._all())

    def run(self):
        self._draw()
        taps = nds_keyboard.KeyTracker()
        while True:
            nds.frame()
            tap = taps.update()
            if nds.keys_down() & nds.KEY_B:
                return None
            if tap is None:
                continue
            key = nds_keyboard.key_at(nds_keyboard.ACTIVE_KEYS, tap[0], tap[1])
            if key is None:
                continue
            if key.action == "back":
                return None
            if key.action == "save":
                return self.pin
            if key.action == "make":
                nds_ui.top_blocks(_("PIN"), [("text", _("Listening to the room's noise..."))])
                pin = make_pin()
                if pin is None:
                    nds_ui.sound("error")
                else:
                    self.pin, self.made_up = pin, True
                    nds_ui.sound("success")
            elif key.action == "del":
                self.pin = self.pin[:-1]
                self.made_up = False
            elif len(self.pin) < 32:
                self.pin += key.action
                self.made_up = False
            self._draw()


def intro():
    """What tones are, their risks and where they come from; then the PIN and
    the microphone's gain. Returns (pin, gain), or None for Back."""
    pin = ""
    while True:
        nds_ui.top_blocks(_("Tones (experimental)"), [
            ("text", _("Listen to a transaction, a seed or an xpub sent as telephone tones.")),
            ("space", 4),
            ("label", _("Through the air, any microphone nearby can record a seed: send it by cable, or with a PIN.")),
            ("label", _("Experimental: try it with test seeds first.")),
            ("space", 4),
            ("label", REPO)])
        labels = [_("Start listening"),
                  "%s: %s" % (_("PIN"), pin if pin else _("none")),
                  "%s: %s" % (_("Microphone gain"), GAINS[_state["gain"]])]
        choice = nds_ui.ButtonPanel(labels).run()
        if choice == nds_ui.BACK:
            return None
        if choice == 0:
            return pin, _state["gain"]
        if choice == 1:
            new = PinScreen(pin).run()
            if new is not None:
                pin = new
        if choice == 2:
            _state["gain"] = (_state["gain"] + 1) % len(GAINS)


class ListenView:
    """The top screen while listening: frames heard, the message's progress,
    the frame being heard (its share and its tones as they come) and the
    sound's level. The bottom screen is left for the controls."""
    DB_MIN = -60          # the level bar's range, dBFS
    SILENCE_FRAMES = 30   # half a second without tones ends a frame

    def __init__(self, pin):
        from seedsigner.gui.components import GUIConstants as GC
        self.t = nds_ui.theme()
        self.ok = nds_ui._rgb(GC.SUCCESS_COLOR)
        self.warn = nds_ui._rgb(GC.WARNING_COLOR)
        self.bad = nds_ui._rgb(GC.ERROR_COLOR)
        self.pin = pin
        self.heard = ""         # the latest keys, for the scrolling line
        self.mode = None        # None between frames, "frame" or "keypad"
        self.current = ""       # this frame's tones after the sync
        self.total = None       # and how many it will have
        self.quiet = 0
        self.frames = self.bad_frames = 0
        self.history = []       # True / False per frame heard, the latest last
        self.last = ""
        self.percent = 0
        self.level = -990
        self.dirty = True
        self.urgent = False     # a frame starts: shown at once

    def keys(self, live):
        """Follows the keys heard, as they come (a rough view: the frame
        itself comes later, whole, from the receiver)."""
        if not live:
            self.quiet += 1
            if self.quiet == self.SILENCE_FRAMES and self.mode:
                self.mode, self.current, self.total = None, "", None
                self.dirty = True
            return
        self.quiet = 0
        self.dirty = True
        self.heard = (self.heard + live)[-40:]
        for k in live:
            if self.mode == "frame":
                if self.current and self.current[-1] == k:
                    continue                         # an echo: tones never repeat
                self.current += k
                if self.total is None:
                    self.total = frame_length(self.current)
            elif self.mode == "keypad":
                self.current += k
                if k == "#":
                    self.mode = None
            elif k == "*":
                self.mode, self.current, self.total = "keypad", "", None
                self.urgent = True
            else:
                self.current = (self.current + k)[-2:]
                if self.current == "AD":
                    self.mode, self.current, self.total = "frame", "", None
                    self.urgent = True

    def frame_done(self, ok, text):
        if ok:
            self.frames += 1
        else:
            self.bad_frames += 1
        self.history = (self.history + [ok])[-16:]
        self.last = text
        self.mode, self.current, self.total = None, "", None
        self.dirty = True

    def _bar(self, y, fraction, color, h=8):
        x, w = nds_ui.MARGIN, nds_ui.GFX_W - 2 * nds_ui.MARGIN
        nds.gfx_rect(nds_ui.TOP, x, y, w, h, self.t["inactive"], 3)
        fill = max(0, min(w, int(w * fraction)))
        if fill >= 6:
            nds.gfx_rect(nds_ui.TOP, x, y, fill, h, color, 3)

    def _row(self, y, left, right, font=None, color=None):
        font = nds.FONT_BODY if font is None else font
        color = self.t["body"] if color is None else color
        nds.gfx_text(nds_ui.TOP, nds_ui.MARGIN, y, left, font, color)
        if right:
            w = nds.gfx_text_width(right, font)
            nds.gfx_text(nds_ui.TOP, nds_ui.GFX_W - nds_ui.MARGIN - w, y, right, font, color)

    def draw(self):
        t, top = self.t, nds_ui.TOP
        nds.top_clear()
        nds.gfx_clear(top, t["bg"])
        nds_ui._title(_("Listening"))
        # frames heard, and a light per frame (green: read, red: discarded)
        parts = _last["parts"]
        right = (_("{} parts").format(parts) if parts > 1 else "") + ("  PIN" if self.pin else "")
        self._row(32, _("Frames: {}").format(self.frames), right)
        x = nds_ui.MARGIN + nds.gfx_text_width(_("Frames: {}").format(self.frames), nds.FONT_BODY) + 8
        for ok in self.history:
            if x > 170:
                break
            nds.gfx_rect(top, x, 37, 7, 7, self.ok if ok else self.bad, 2)
            x += 10
        # the message
        self._row(52, _("Message"), "%d%%" % self.percent, nds.FONT_BODY_BOLD)
        self._bar(70, self.percent / 100, t["accent"])
        # the frame being heard
        n = len(self.current)
        if self.mode == "keypad":
            total = 48 if n <= 49 else 96             # 12 or 24 words, 4 digits each
            label, share = _("Seed (keypad)"), min(n, total) / total
            detail = "%d/%d" % (min(n, total), total)
        elif self.mode == "frame":
            total = self.total
            label = _("This frame")
            share = min(n / total, 0.99) if total else 0
            detail = "%d%%  %d/%s" % (int(share * 100), n, total if total else "?")
        else:
            label, share, detail = _("Waiting for a frame..."), 0, ""
        self._row(84, label, detail)
        self._bar(102, share, self.ok)
        # the tones as they come
        nds.gfx_frame(top, nds_ui.MARGIN, 116, nds_ui.GFX_W - 2 * nds_ui.MARGIN, 24, t["inactive"], 4, 1)
        nds_ui.text_centered(top, 119, self.heard[-26:] or "...", nds.FONT_MONO_BOLD, t["accent"])
        # the level
        db = self.level // 10
        if self.level <= -900:
            text, share, color = _("Level: -"), 0, t["inactive"]
        else:
            share = (db - self.DB_MIN) / -self.DB_MIN
            color = self.bad if db > -3 else self.warn if db < -45 else self.ok
            text = "%s %d dB" % (_("Level:"), db)
        nds.gfx_text(top, nds_ui.MARGIN, 148, text, nds.FONT_BODY, t["body"])
        x0 = nds_ui.MARGIN + 92
        w = nds_ui.GFX_W - nds_ui.MARGIN - x0
        for i in range(20):                          # 3 dB per segment
            on = i < int(share * 20 + 0.5)            # lit in the level's colour: quiet, good, too loud
            nds.gfx_rect(top, x0 + i * w // 20, 152, w // 20 - 2, 10, color if on else t["inactive"], 1)
        # the last frame's outcome
        if self.last:
            nds_ui.text_centered(top, 170, self.last, nds.FONT_BODY, t["label"])
        nds.gfx_present(top)
        self.dirty = self.urgent = False


def listen(decoder, pin, gain):
    """Listens until the decoder is complete (True), or Cancel (False). The
    top screen shows the progress (ListenView); the bottom one, Cancel and the
    microphone's gain, which can be changed while listening."""
    from seedsigner.models.decode_qr import DecodeQRStatus

    def panel_for(g):
        p = nds_ui.ButtonPanel([_("Cancel"), "%s: %s" % (_("Microphone gain"), GAINS[g])],
                               show_back=False)
        p.draw()
        return p

    _last["parts"] = 0
    view = ListenView(pin)
    view.draw()
    panel = panel_for(gain)
    if not nds.tones_listen(True, gain):
        return False
    tick = 0
    try:
        while True:
            nds.frame()
            choice = panel.handle_frame()
            if choice == 0 or nds.keys_down() & nds.KEY_B:
                return False
            if choice == 1:                          # restarts the microphone
                gain = _state["gain"] = (gain + 1) % len(GAINS)
                nds.tones_listen(False)
                if not nds.tones_listen(True, gain):
                    return False
                panel = panel_for(gain)
                view.mode, view.current, view.total = None, "", None
            group, live, level, buffers, dropped = nds.tones_poll()
            view.keys(live)
            if level != view.level and tick % 15 == 0:  # twice a second: enough to set the volume
                view.level, view.dirty = level, True
            tick += 1
            if group is not None:
                status, fixed = feed(decoder, group, pin)
                if status is None:
                    nds_ui.sound("error")
                    view.frame_done(False, _("Discarded: too many errors"))
                elif status in (DecodeQRStatus.COMPLETE, DecodeQRStatus.INVALID):
                    view.percent = 100 if status == DecodeQRStatus.COMPLETE else view.percent
                    view.frame_done(True, "")
                    view.draw()
                    nds_ui.sound("success" if status == DecodeQRStatus.COMPLETE else "error")
                    return True
                else:
                    nds_ui.sound("scan")
                    view.percent = decoder.get_percent_complete() or view.percent
                    view.frame_done(True, _("Read, {} bytes repaired").format(fixed) if fixed
                                    else _("Frame read"))
            if nds_ui.nds_dev is not None and tick % 30 == 0:
                view.last = "b%d d%d" % (buffers, dropped)
                view.dirty = True
            if view.urgent or view.dirty and tick % 6 == 0:  # 10 times a second at most
                view.draw()
    finally:
        nds.tones_listen(False)
