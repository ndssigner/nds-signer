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
_state = {"gain": 1}  # this session only


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
    if ur.startswith("ur:crypto-seed/") or ur.startswith("ur:seed/"):
        entropy, err = nds.tones_seed(ur, pin or None)
        if entropy is None:
            return None, err
        return decoder.add_data(seedqr_digits(entropy).encode()), fixed
    return decoder.add_data(ur.encode()), fixed


class PinScreen:
    """A PIN on the touch keyboard: letters and digits (SPEC §4). Returns it,
    or None for Back."""
    ROWS = ("1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM")

    def __init__(self, pin=""):
        self.pin = pin
        self.keys = []
        for r, row in enumerate(self.ROWS):
            col = (nds_ui.COLS - len(row) * 3) // 2
            for i, ch in enumerate(row):
                self.keys.append(nds_keyboard.Key(ch, 3 + r * 3, col + i * 3))
        self.del_key = nds_keyboard.Key(_("Del"), 15, 19, width=6, action="del")
        self.back_key = nds_keyboard.Key(_("< Back"), 20, 1, width=10, action="back")
        self.save_key = nds_keyboard.Key(_("Save"), 20, 21, width=10, action="save")

    def _draw(self):
        nds_ui.top_blocks(_("PIN"), [
            ("large", self.pin or " "), ("space", 6),
            ("label", _("The same PIN the sender used. Letters and digits.")),
            ("label", _("A wrong PIN gives a different seed, without an error."))])
        nds.bottom_clear()
        for key in self.keys + [self.del_key, self.back_key, self.save_key]:
            nds_keyboard.draw_key(key)
        nds_keyboard.set_active(self.keys + [self.del_key, self.back_key, self.save_key])

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
            if key.action == "del":
                self.pin = self.pin[:-1]
            elif len(self.pin) < 32:
                self.pin += key.action
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
                  "%s: %s" % (_("PIN"), _("set") if pin else _("none")),
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


def listen(decoder, pin, gain, progress):
    """Listens until the decoder is complete (True), or Cancel (False).
    progress(text) shows a line below the Cancel button."""
    from seedsigner.models.decode_qr import DecodeQRStatus

    panel = nds_ui.ButtonPanel([_("Cancel")], show_back=False)
    panel.draw()
    if not nds.tones_listen(True, gain):
        return False
    heard, frames, bad, shown, tick = "", 0, 0, None, 0
    try:
        while True:
            nds.frame()
            if panel.handle_frame() is not None or nds.keys_down() & nds.KEY_B:
                return False
            group, live, level, buffers, dropped = nds.tones_poll()
            if live:
                heard = (heard + live)[-28:]
            tick += 1
            if live or tick % 15 == 0:  # the level twice a second: enough to set the volume
                line = "%s  %s %s" % (heard[-14:] or "...", "%d dB" % (level // 10) if level > -900 else "-",
                                       _("{} frames").format(frames) if frames else "")
                if nds_ui.nds_dev is not None:
                    line += " b%d d%d" % (buffers, dropped)
                if line != shown:
                    progress(line)
                    shown = line
            if group is None:
                continue
            status, fixed = feed(decoder, group, pin)
            if status is None:
                bad += 1
                nds_ui.sound("error")
                continue
            frames += 1
            if status == DecodeQRStatus.COMPLETE:
                nds_ui.sound("success")
                return True
            if status == DecodeQRStatus.INVALID:
                nds_ui.sound("error")
                return True
            nds_ui.sound("scan")
            percent = decoder.get_percent_complete()
            if percent:
                progress("%s %d%%" % (_("Progress:"), percent))
                shown = None
    finally:
        nds.tones_listen(False)
