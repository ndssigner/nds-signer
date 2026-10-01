# Drives SeedSigner's unmodified Controller and views headlessly through
# NDS-Signer's native screens (host simulator of the `nds` module):
# Home -> Scan (fake camera: PSBT QR) -> select seed -> review -> sign.
# The signed PSBT shown at the end must match the CPython reference.
import sys

import nds
from seedsigner.controller import Controller, StopFlowBasedTest, FlowBasedTestException

VECTORS = sys.argv[1] if len(sys.argv) > 1 else "../vectors"
VERBOSE = "-v" in sys.argv


def read(name):
    try:
        import test_vectors
        return test_vectors.DATA[name].strip()
    except ImportError:
        with open(VECTORS + "/" + name) as f:
            return f.read().strip()


RESULT = {}


def check_signed(prefix):
    """Decodes the QR parts shown by QRDisplayScreen and compares the signed
    PSBT with the CPython reference."""
    from seedsigner.models.decode_qr import DecodeQR

    parts = list(nds.qr_shown)
    if not parts:
        raise FlowBasedTestException("no QR was displayed")
    decoder = DecodeQR()
    for part in parts:
        decoder.add_data(part)
    ok = decoder.is_complete and decoder.get_psbt().to_string() == read(prefix + ".signed_trimmed.txt")
    RESULT[prefix] = ok
    print("ok  " if ok else "FAIL", prefix, "flow: signed PSBT QR (%d frames shown)" % len(parts))


def stop():
    raise StopFlowBasedTest()


# --gallery=DIR: snapshot of the screen at every dump() point, named after the
# screen class shown last (tools/dev/render_gallery.py)
GALLERY = ([a[10:] for a in sys.argv if a.startswith("--gallery=")] or [None])[0]
_last_screen = ["?"]
_snaps = [0]
if GALLERY:
    nds.snapshot_dir = GALLERY
    from seedsigner.gui.screens import screen as _screen_mod

    _orig_display = _screen_mod.BaseScreen.display

    def _display(self):
        _last_screen[0] = type(self).__name__
        return _orig_display(self)

    _screen_mod.BaseScreen.display = _display


def dump():
    if VERBOSE:
        nds.sim_dump()
    if GALLERY:
        _snaps[0] += 1
        nds.sim_snapshot("flow-%s_%02d_%s" % (MODE, _snaps[0], _last_screen[0]))


def type_mnemonic(words):
    """Taps for SeedSigner's word-by-word entry: 4 letters identify any
    BIP-39 word, then its candidate button."""
    events = []
    for word in words:
        for letter in word[:4]:
            events += [("tap_key", letter), ("key", 0)]
        events += [("tap_label", word), ("key", 0)]
    return events


def run_typed_seed_flow(prefix):
    """Home -> Seeds -> Load -> type 12 words -> Done -> Scan transaction ->
    review -> sign: the seed is entered through the touch keyboard."""
    from seedsigner.models.settings import Settings, SettingsConstants
    from seedsigner.views.view import Destination, MainMenuView

    controller = Controller.get_instance()
    Settings.get_instance().set_value(SettingsConstants.SETTING__NETWORK, SettingsConstants.TESTNET)

    def taps(*labels):
        out = []
        for label in labels:
            out += [("call", dump), ("tap_label", label), ("key", 0)]
        return out

    # with no seed loaded, SeedsMenuView goes straight to "Load a Seed"
    events = taps("Seeds", "Enter 12-word seed")
    events += type_mnemonic(read(prefix + ".mnemonic.txt").split())
    events += taps("Done", "Scan transaction")
    events.append(("camera", read(prefix + ".txt").encode()))
    events += taps("Review details", "Continue", "Review recipients", "Next recipient", "Next",
                   "Approve transaction")
    events += [("wait", 200), ("call", dump), ("call", lambda: check_signed(prefix)), ("call", stop)]
    nds.sim_script(events)
    controller.start(initial_destination=Destination(MainMenuView))


PASSPHRASE_MODES = (("abc", "abcdefghijklmnopqrstuvwxyz"), ("ABC", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                    ("123", "0123456789"), ("!@#", """!@#$%&();:,.-+='"?"""),
                    ("*[]", """^*[]{}_\\|<>/`~"""))


def type_passphrase(text):
    """Taps on the passphrase keyboard, switching layouts as needed."""
    events, mode = [], "abc"
    for ch in text:
        wanted = next(name for name, chars in PASSPHRASE_MODES if ch in chars)
        if wanted != mode:
            events += [("tap_key", wanted), ("key", 0)]
            mode = wanted
        events += [("tap_key", ch), ("key", 0)]
    return events


def run_passphrase_flow(prefix):
    """Typed seed + BIP-39 passphrase: the fingerprint shown must match
    SeedSigner on CPython for that seed and passphrase."""
    from seedsigner.views.view import Destination, MainMenuView

    def check_fingerprint():
        expected = read("passphrase.fingerprint.txt")
        ok = expected in nds.sim_text(0)
        RESULT["passphrase"] = ok
        print("ok  " if ok else "FAIL", "passphrase flow: fingerprint", expected, "shown")

    events = [("tap_label", "Seeds"), ("key", 0), ("tap_label", "Enter 12-word seed"), ("key", 0)]
    events += type_mnemonic(read(prefix + ".mnemonic.txt").split())
    events += [("call", dump), ("tap_label", "BIP-39 Passphrase"), ("key", 0)]
    events += type_passphrase(read("passphrase.txt"))
    events += [("call", dump), ("tap_key", "Save"), ("key", 0), ("wait", 5), ("call", dump),
               ("call", check_fingerprint), ("tap_label", "Done"), ("key", 0), ("call", dump),
               ("call", check_fingerprint), ("call", stop)]
    nds.sim_script(events)
    Controller.get_instance().start(initial_destination=Destination(MainMenuView))


def run_settings_flow():
    """Settings -> Advanced -> Bitcoin network -> Testnet, through the UI."""
    from seedsigner.models.settings import Settings, SettingsConstants
    from seedsigner.views.view import Destination, MainMenuView

    def check_network():
        value = Settings.get_instance().get_value(SettingsConstants.SETTING__NETWORK)
        ok = value == SettingsConstants.TESTNET
        RESULT["settings"] = ok
        print("ok  " if ok else "FAIL", "settings flow: network =", value)

    events = []
    for label in ("Settings", "Advanced", "Bitcoin network", "Testnet"):
        events += [("call", dump), ("tap_label", label), ("key", 0)]
    events += [("call", dump), ("call", check_network), ("call", stop)]
    nds.sim_script(events)
    Controller.get_instance().start(initial_destination=Destination(MainMenuView))


def run_xpub_flow(prefix):
    """Seeds -> seed -> Export xpub -> single sig native segwit -> animated
    QR: the parts shown must be exactly those SeedSigner's UrXpubQrEncoder
    produces on CPython (tests/vectors/<prefix>.xpub_ur.txt)."""
    from seedsigner.views.view import Destination, MainMenuView
    from seedsigner.models.seed import Seed

    def check_xpub():
        expected = read(prefix + ".xpub_ur.txt").split("\n")
        shown = list(nds.qr_shown)[:len(expected)]
        ok = shown == expected
        if not ok and VERBOSE:
            for a, b in zip(shown, expected):
                print("shown   ", a[:70]); print("expected", b[:70])
            print("shown count", len(nds.qr_shown))
        RESULT["xpub"] = ok
        print("ok  " if ok else "FAIL", "xpub flow: %d animated UR parts identical to SeedSigner on CPython"
              % len(expected))

    from seedsigner.models.settings import Settings, SettingsConstants

    controller = Controller.get_instance()
    Settings.get_instance().set_value(SettingsConstants.SETTING__NETWORK, SettingsConstants.TESTNET)
    controller.storage.set_pending_seed(Seed(read(prefix + ".mnemonic.txt").split()))
    controller.storage.finalize_pending_seed()
    events = []
    for label in ("Seeds", "8b218e81", "Export xpub", "Single Sig", "Native Segwit",
                  "Animated (default)", "I understand"):
        events += [("call", dump), ("tap_label", label), ("key", 0)]
    events += [("call", dump), ("tap_label", "Export xpub"), ("key", 0), ("wait", 300),
               ("call", dump), ("call", check_xpub), ("call", stop)]
    nds.sim_script(events)
    controller.start(initial_destination=Destination(MainMenuView))


def run_seedqr_flow():
    """Home -> Seeds -> Scan a SeedQR (camera) -> Finalize: the fingerprint
    shown must be the one SeedSigner computes on CPython."""
    from seedsigner.views.view import Destination, MainMenuView

    def check_fingerprint():
        expected = read("seedqr_12words.fingerprint.txt")
        ok = expected in nds.sim_text(0)
        RESULT["seedqr"] = ok
        print("ok  " if ok else "FAIL", "seedqr flow: fingerprint", expected, "shown")

    events = [("call", dump), ("tap_label", "Seeds"), ("key", 0),
              ("call", dump), ("tap_label", "Scan a SeedQR"), ("key", 0),
              ("camera", read("seedqr_12words.txt").encode()),
              ("wait", 10), ("call", dump), ("call", check_fingerprint), ("call", stop)]
    nds.sim_script(events)
    Controller.get_instance().start(initial_destination=Destination(MainMenuView))


def run_address_flow(prefix, own):
    """Home -> Scan an address -> pick the seed. Own address (the seed's
    first receive address): the search must end on "index 0". Foreign
    address: the search runs until Cancel, then Home (it used to hang: the
    brute-force thread ran synchronously, forever)."""
    from seedsigner.models.seed import Seed
    from seedsigner.models.settings import Settings, SettingsConstants
    from seedsigner.views.view import Destination, MainMenuView

    controller = Controller.get_instance()
    Settings.get_instance().set_value(SettingsConstants.SETTING__NETWORK, SettingsConstants.TESTNET)
    controller.storage.set_pending_seed(Seed(read(prefix + ".mnemonic.txt").split()))
    controller.storage.finalize_pending_seed()
    address = read("address_testnet.txt") if not own else "tb1qw2as76rh4jhykn9zvevdt5tawmqx7hhy7ydvvu"
    name = "address flow (%s)" % ("own address" if own else "foreign address, cancelled")

    def check():
        top, bottom = nds.sim_text(0), nds.sim_text(1)
        if own:
            ok = "receive address" in top and "index 0" in top
        else:
            ok = "Scan" in bottom and "Seeds" in bottom  # back Home
        RESULT["address"] = ok
        print("ok  " if ok else "FAIL", name)

    events = [("call", dump), ("tap_label", "Scan"), ("key", 0),
              ("camera", ("bitcoin:" + address).encode()), ("wait", 10),
              ("call", dump), ("tap_label", "8b218e81"), ("key", 0), ("wait", 30), ("call", dump)]
    if not own:
        events += [("tap_label", "Cancel"), ("key", 0), ("wait", 10), ("call", dump)]
    events += [("call", check), ("call", stop)]
    nds.sim_script(events)
    controller.start(initial_destination=Destination(MainMenuView))


def run_backup_flow(prefix):
    """Seeds -> Backup seed -> View seed words: the pages must show the
    mnemonic, in order; then the backup test (Verify), answering each
    "Verify Word #N" with the right word, must end on "Backup Verified"."""
    from seedsigner.models.seed import Seed
    from seedsigner.views.view import Destination, MainMenuView

    controller = Controller.get_instance()
    words = read(prefix + ".mnemonic.txt").split()
    controller.storage.set_pending_seed(Seed(words))
    controller.storage.finalize_pending_seed()
    shown = []

    def collect_page():
        for line in nds.sim_text(0).split("\n"):
            parts = line.strip("|").split()
            if len(parts) == 2 and parts[0].endswith(".") and parts[0][:-1].isdigit():
                shown.append((int(parts[0][:-1]), parts[1]))

    def answer():
        top = nds.sim_text(0)
        if "Verify Word #" in top:
            n = int(top.split("Verify Word #")[1].split()[0].strip("|"))
            nds._events[0:0] = [("tap_label", words[n - 1]), ("key", 0), ("wait", 3),
                                 ("call", dump), ("call", answer)]

    def check():
        ok_words = shown == [(i + 1, w) for i, w in enumerate(words)]
        ok_test = "Backup Verified" in nds.sim_text(0)
        RESULT["backup"] = ok_words and ok_test
        print("ok  " if ok_words and ok_test else "FAIL",
              "backup flow: %d seed words shown in order%s, backup test %s" % (
                  len(shown), "" if ok_words else " (WRONG)", "verified" if ok_test else "FAILED"))

    events = []
    for label in ("Seeds", "8b218e81", "Backup seed", "View seed words", "I understand"):
        events += [("call", dump), ("tap_label", label), ("key", 0)]
    for page in range(3):
        events += [("wait", 2), ("call", dump), ("call", collect_page),
                   ("tap_label", "Next" if page < 2 else "Done"), ("key", 0)]
    events += [("wait", 2), ("call", dump), ("tap_label", "Verify"), ("key", 0), ("wait", 2),
               ("call", dump), ("call", answer), ("wait", 5), ("call", check), ("call", stop)]
    nds.sim_script(events)
    controller.start(initial_destination=Destination(MainMenuView))


def run_transcribe_flow(prefix, compact):
    """Backup seed -> Export as SeedQR: the whole QR (ECC L) must have the
    template's size, the zoomed zones must follow the D-pad, and scanning back
    exactly what was shown must confirm the SeedQR. A tap on the map's zone
    B-2 then D-pad right must show zone C-2."""
    from seedsigner.models.seed import Seed
    from seedsigner.views.view import Destination, MainMenuView

    controller = Controller.get_instance()
    controller.storage.set_pending_seed(Seed(read(prefix + ".mnemonic.txt").split()))
    controller.storage.finalize_pending_seed()
    size = 21 if compact else 25
    fmt = "Compact: 21x21" if compact else "Standard: 25x25"
    name = "transcribe flow (%s)" % fmt
    state = {}

    def check_whole():
        data, zone, _x, _y = nds.qr_transcribed[-1]
        state["data"] = data
        state["whole"] = zone == 0 and nds.qr_transcribe(data) == size and (
            len(data) == 16 if compact else data == read(prefix + ".seedqr.txt"))
        del nds.qr_transcribed[-1]

    def check_zone():
        _d, zone, x, y = nds.qr_transcribed[-1]
        state["zone"] = (zone, x, y) == ((7 if compact else 5), 2, 1)

    def scan_back():
        nds.sim_camera([state["data"] if compact else state["data"].encode()])

    def check():
        ok = state.get("whole") and state.get("zone") and "Success" in nds.sim_text(0)
        RESULT["transcribe"] = ok
        print("ok  " if ok else "FAIL", name, state.get("whole"), state.get("zone"))

    # the centre of zone B-2 on the bottom screen's map (5 px per module)
    side, cell = size * 5, (7 if compact else 5) * 5
    map_x = 80 + (176 - side) // 2 + cell + cell // 2
    map_y = 38 + (148 - side) // 2 + cell + cell // 2
    events = []
    for label in ("Seeds", "8b218e81", "Backup seed", "Export as SeedQR", fmt, "I understand"):
        events += [("call", dump), ("tap_label", label), ("key", 0)]
    events += [("wait", 2), ("call", check_whole), ("tap_label", "Begin %dx%d" % (size, size)),
               ("key", 0), ("wait", 2), ("tap", map_x, map_y), ("wait", 4), ("key", 0),
               ("wait", 2), ("key", nds.KEY_RIGHT), ("wait", 2), ("call", dump),
               ("call", check_zone), ("tap_label", "Done"), ("key", 0), ("wait", 2),
               ("call", dump), ("call", scan_back), ("tap_label", "Confirm SeedQR"), ("key", 0),
               ("wait", 10), ("call", dump), ("call", check), ("call", stop)]
    nds.sim_script(events)
    controller.start(initial_destination=Destination(MainMenuView))


def run_explorer_flow(prefix):
    """Seeds -> Address explorer -> Native Segwit -> Receive: the top screen
    shows the selected address in full with its QR code (bech32 in capitals);
    the first two are the test seed's (the same Sparrow showed on Signet,
    docs/guia-xpub-sparrow.md). D-pad down selects the second; a tap on the
    first selects it again, a second tap opens its QR view."""
    from seedsigner.models.seed import Seed
    from seedsigner.models.settings import Settings, SettingsConstants
    from seedsigner.views.view import Destination, MainMenuView

    controller = Controller.get_instance()
    Settings.get_instance().set_value(SettingsConstants.SETTING__NETWORK, SettingsConstants.TESTNET)
    controller.storage.set_pending_seed(Seed(read(prefix + ".mnemonic.txt").split()))
    controller.storage.finalize_pending_seed()
    expected = ["tb1qw2as76rh4jhykn9zvevdt5tawmqx7hhy7ydvvu", "tb1qdxl0syr9zqwxentq7mzvf7taglscyrmmnpfss6"]
    seen = []

    def shown(n):
        def check():
            # the drawn text itself (the simulator's text grid is only 32 columns)
            top = "".join(op[3] for op in nds._dl[0] if op[0] == "text").replace(" ", "")
            seen.append(expected[n] in top and nds.qr_drawn[-1:] == [expected[n].upper()])
        return check

    def opened():
        seen.append(any(op[0] == "qr" for op in nds._dl[0]))

    def check():
        ok = seen == [True] * 4
        RESULT["explorer"] = ok
        print("ok  " if ok else "FAIL", "address explorer flow: selected address and QR on top", seen)

    events = []
    for label in ("Seeds", "8b218e81", "Address explorer", "Native Segwit", "Receive"):
        events += [("call", dump), ("tap_label", label), ("key", 0)]
    events += [("wait", 5), ("call", dump), ("call", shown(0)), ("key", nds.KEY_DOWN), ("wait", 2),
               ("call", shown(1)), ("tap_label", expected[0][:6]), ("wait", 4), ("key", 0), ("wait", 2),
               ("call", shown(0)), ("tap_label", expected[0][:6]), ("wait", 4), ("key", 0), ("wait", 4),
               ("call", dump), ("call", opened), ("call", check), ("call", stop)]
    nds.sim_script(events)
    controller.start(initial_destination=Destination(MainMenuView))


def run_dice_flow():
    """Tools -> New seed -> Dice -> 12 words: the 50 rolls typed on the touch
    keyboard must give the mnemonic of SeedSigner's own test vector
    (tests/test_mnemonic_generation.py, same as iancoleman.io/bip39), shown
    word by word."""
    from seedsigner.views.view import Destination, MainMenuView

    rolls = "12345612345612345612345612345612345612345612345612"
    expected = "unveil nice picture region tragic fault cream strike tourist control recipe tourist".split()
    shown = []

    def collect_page():
        for line in nds.sim_text(0).split("\n"):
            parts = line.strip("|").split()
            if len(parts) == 2 and parts[0].endswith(".") and parts[0][:-1].isdigit():
                shown.append(parts[1])

    # every key tapped is shown pressed while the stylus is on it
    from seedsigner.gui import nds_keyboard
    pressed = []
    _orig_show = nds_keyboard.KeyTracker._show

    def _show(self, key):
        if key is not None and key is not self.pressed:
            pressed.append(key.label)
        _orig_show(self, key)
    nds_keyboard.KeyTracker._show = _show

    def check():
        ok = shown == expected and "".join(pressed) == rolls
        RESULT["dice"] = ok
        print("ok  " if ok else "FAIL", "dice flow: 50 rolls ->", " ".join(shown[:3]),
              "... (%d words), %d keys shown pressed" % (len(shown), len(pressed)))

    events = []
    for label in ("Tools", "New seed", "Dice", "12 words (50 rolls)"):
        events += [("call", dump), ("tap_label", label), ("key", 0)]
    for roll in rolls:
        events += [("tap_key", roll), ("key", 0)]
    events += [("wait", 5), ("call", dump), ("tap_label", "I understand"), ("key", 0)]
    for page in range(3):
        events += [("wait", 2), ("call", dump), ("call", collect_page),
                   ("tap_label", "Next"), ("key", 0)]
    events += [("call", check), ("call", stop)]
    nds.sim_script(events)
    Controller.get_instance().start(initial_destination=Destination(MainMenuView))


def run_final_word_flow(prefix):
    """Tools -> Calc 12th/24th word -> 12 words: the test seed's first 11
    words, then the 7 entropy bits of its real 12th word as coin flips, must
    give back that word ("enroll") and the seed's fingerprint."""
    from embit import bip39
    from seedsigner.views.view import Destination, MainMenuView

    words = read(prefix + ".mnemonic.txt").split()
    bits = "{:011b}".format(bip39.WORDLIST.index(words[-1]))[:7]
    name = "final word flow: 11 words + coin flips %s" % bits

    def check():
        top = nds.sim_text(0)
        ok = '"%s"' % words[-1] in top and "8b218e81" in top
        RESULT["final_word"] = ok
        print("ok  " if ok else "FAIL", name, "->", words[-1] if ok else "WRONG")

    events = []
    for label in ("Tools", "Calc 12th/24th word", "12 words"):
        events += [("call", dump), ("tap_label", label), ("key", 0)]
    events += type_mnemonic(words[:11])
    events += [("call", dump), ("tap_label", "Coin flip entropy"), ("key", 0)]
    for bit in bits:
        events += [("tap_key", bit), ("key", 0)]
    events += [("wait", 3), ("call", dump), ("tap_label", "Next"), ("key", 0), ("wait", 3),
               ("call", dump), ("call", check), ("call", stop)]
    nds.sim_script(events)
    Controller.get_instance().start(initial_destination=Destination(MainMenuView))


def run_sound_flow():
    """Settings > Sound effects: taps make sounds; once disabled, none."""
    from seedsigner.views.view import Destination, MainMenuView
    state = {}

    def mark():
        state["before"] = len(nds.sounds)

    def check():
        played_on = state["before"] > 0
        silent_after = len(nds.sounds) == state["after_off"]
        ok = played_on and silent_after
        RESULT["sound"] = ok
        print("ok  " if ok else "FAIL", "sound flow: %d sounds while enabled, %s after disabling" % (
            state["before"], "none" if silent_after else "SOME"))

    def after_off():
        state["after_off"] = len(nds.sounds)

    events = []
    for label in ("Settings", "Sound effects"):
        events += [("call", dump), ("tap_label", label), ("key", 0)]
    events += [("call", mark), ("call", dump), ("tap_label", "Disabled"), ("key", 0), ("wait", 2),
               ("call", after_off), ("call", dump), ("tap_label", "Disabled"), ("key", 0),
               ("wait", 2), ("key", nds.KEY_B), ("wait", 2), ("call", dump),
               ("call", check), ("call", stop)]
    nds.sim_script(events)
    Controller.get_instance().start(initial_destination=Destination(MainMenuView))


def run_scan_intro_flow(prefix):
    """Scan with "Scan preparation" enabled: the tips and the camera choice
    first (switched to the front camera), then Start; the code shown to the
    camera from the start is decoded only after the countdown, and the PSBT
    then reaches seed selection."""
    from seedsigner.models.seed import Seed
    from seedsigner.views.view import Destination, MainMenuView

    controller = Controller.get_instance()
    controller.storage.set_pending_seed(Seed(read(prefix + ".mnemonic.txt").split()))
    controller.storage.finalize_pending_seed()
    state = {}

    def top():
        return "".join(op[3] for op in nds._dl[0] if op[0] == "text")

    def intro():
        state["tips"] = "15-25 cm" in top()

    def show_code():
        nds.sim_camera([read(prefix + ".txt").encode()])

    def still_waiting():  # ~2 s in: the countdown is still running
        state["waited"] = len(nds._camera_queue) == 1

    def check():
        bottom = "".join(op[3] for op in nds._dl[1] if op[0] == "text")
        ok = state.get("tips") and nds.camera_front and state.get("waited") and "8b218e81" in bottom
        RESULT["scan_intro"] = ok
        print("ok  " if ok else "FAIL", "scan intro flow: tips %s, front camera %s, countdown %s, "
              "seed selection %s" % (state.get("tips"), nds.camera_front, state.get("waited"),
                                     "8b218e81" in bottom))

    events = [("call", dump), ("tap_label", "Scan"), ("key", 0), ("wait", 2), ("call", dump),
              ("call", intro), ("tap_label", "Camera: Rear camera"), ("key", 0), ("wait", 2),
              ("call", dump), ("tap_label", "Start scanning"), ("key", 0), ("call", show_code),
              ("wait", 120), ("call", still_waiting), ("wait", 200), ("call", dump),
              ("call", check), ("call", stop)]
    nds.sim_script(events)
    controller.start(initial_destination=Destination(MainMenuView))


def run_camera_seed_flow():
    """Tools -> New seed -> Camera: 50 distinct frames (two flat ones skipped),
    Take photo, Accept, 12 words: a valid new 12-word mnemonic is shown, and
    the camera is off again."""
    from seedsigner.views.view import Destination, MainMenuView
    state = {}

    def flat():  # a covered lens: these frames must not count
        nds.sim_flat_frames = 2

    def check_pool():
        state["pool"] = "50/50" in "".join(op[3] for op in nds._dl[1] if op[0] == "text")

    def check():
        from seedsigner.models.seed import Seed
        seed = Controller.get_instance().storage.pending_seed
        words = seed.mnemonic_list if seed else []
        try:
            valid = len(words) == 12 and bool(Seed(words))
        except Exception:
            valid = False
        ok = state.get("pool") and valid and not nds.camera_running() and nds.camera_grabbed[0] >= 52
        RESULT["camera_seed"] = ok
        print("ok  " if ok else "FAIL", "camera seed flow: pool %s, 12 valid words %s, %d frames, "
              "camera off %s" % (state.get("pool"), valid, nds.camera_grabbed[0],
                                 not nds.camera_running()))

    events = [("call", dump), ("tap_label", "Tools"), ("key", 0), ("call", dump),
              ("tap_label", "New seed"), ("key", 0), ("call", flat), ("tap_label", "Camera"),
              ("key", 0), ("wait", 80),
              ("call", check_pool), ("call", dump), ("tap_label", "Take photo"), ("key", 0),
              ("wait", 6), ("call", dump), ("tap_label", "Accept"), ("key", 0), ("wait", 2),
              ("call", dump), ("tap_label", "12 words"), ("key", 0), ("wait", 4), ("call", dump),
              ("call", check), ("call", stop)]
    nds.sim_script(events)
    Controller.get_instance().start(initial_destination=Destination(MainMenuView))


def run_scribble_mic_flow():
    """Tools -> New seed -> Scribble + microphone: Done stays disabled until there are
    256 distinct stylus points and 16 non-flat microphone buffers (three
    flat ones are skipped); then 12 words: a valid new mnemonic, and the
    microphone is off again."""
    from seedsigner.views.view import Destination, MainMenuView
    state = {}

    def silent():  # a dead microphone at first: those buffers must not count
        nds.sim_mic_silent = 3

    def too_early():  # Done before enough entropy: nothing happens
        state["early"] = nds.mic_on

    def check():
        from seedsigner.models.seed import Seed
        seed = Controller.get_instance().storage.pending_seed
        words = seed.mnemonic_list if seed else []
        try:
            valid = len(words) == 12 and bool(Seed(words))
        except Exception:
            valid = False
        ok = state.get("early") and valid and not nds.mic_on
        RESULT["scribble_mic"] = ok
        print("ok  " if ok else "FAIL", "scribble + mic flow: Done waits %s, 12 valid words %s, "
              "%d mic buffers, mic off %s" % (state.get("early"), valid, nds.mic_buffers[0],
                                             not nds.mic_on))

    scribble = []
    for i in range(260):  # distinct points over the canvas
        scribble += [("tap", 8 + (i * 37) % 240, 8 + (i * 11) % 150), ("wait", 1)]
    events = [("call", dump), ("tap_label", "Tools"), ("key", 0), ("call", silent),
              ("tap_label", "New seed"), ("key", 0), ("tap_label", "Scribble + microphone"), ("key", 0), ("wait", 2), ("call", dump),
              ("tap", 220, 178), ("wait", 4), ("key", 0), ("call", too_early)] + scribble + [
              ("wait", 30), ("call", dump), ("tap", 220, 178), ("wait", 4), ("key", 0),
              ("wait", 2), ("call", dump), ("tap_label", "12 words"), ("key", 0), ("wait", 4),
              ("call", dump), ("call", check), ("call", stop)]
    nds.sim_script(events)
    Controller.get_instance().start(initial_destination=Destination(MainMenuView))


def run_battery_flow(prefix):
    """Seeds -> Backup seed -> View seed words with a low battery: the red
    battery icon is in the title bar and the warning before the words says
    to plug in the charger; while charging, neither is shown."""
    from seedsigner.models.seed import Seed
    from seedsigner.views.view import Destination, MainMenuView

    controller = Controller.get_instance()
    controller.storage.set_pending_seed(Seed(read(prefix + ".mnemonic.txt").split()))
    controller.storage.finalize_pending_seed()
    seen = {}

    def look(name):
        def call():
            top = "".join(op[3] for op in nds._dl[0] if op[0] == "text")
            icon = any(op[0] == "frame" and op[1:3] == (6, 9) for op in nds._dl[0])
            seen[name] = ("Low battery" in top, icon)
        return call

    def charging():
        nds.battery_state = (3, True)

    def check():
        ok = seen.get("low") == (True, True) and seen.get("charging") == (False, False)
        RESULT["battery"] = ok
        print("ok  " if ok else "FAIL", "battery flow: low %s, charging %s" % (
            seen.get("low"), seen.get("charging")))

    nds.battery_state = (3, False)
    events = []
    for label in ("Seeds", "8b218e81", "Backup seed", "View seed words"):
        events += [("call", dump), ("tap_label", label), ("key", 0)]
    events += [("wait", 2), ("call", dump), ("call", look("low")), ("call", charging),
               ("key", nds.KEY_B), ("wait", 2), ("tap_label", "View seed words"), ("key", 0),
               ("wait", 2), ("call", dump), ("call", look("charging")), ("call", check),
               ("call", stop)]
    nds.sim_script(events)
    controller.start(initial_destination=Destination(MainMenuView))


def run_language_flow():
    """A console set to Spanish starts in Spanish (SeedSigner's translation);
    Settings > Language > English switches back."""
    from seedsigner.gui import apply_system_language
    from seedsigner.views.view import Destination, MainMenuView
    state = {}
    nds.system_language_value = 5  # Spanish in the DS user settings
    state["locale"] = apply_system_language()

    def bottom():
        return "".join(op[3] for op in nds._dl[1] if op[0] == "text")

    def check_spanish():
        state["es"] = "Semillas" in bottom() and "Ajustes" in bottom()

    def check():
        ok = state["locale"] == "es" and state.get("es") and "Seeds" in bottom()
        RESULT["language"] = ok
        print("ok  " if ok else "FAIL", "language flow: console in Spanish -> %s, Spanish home %s, "
              "back to English %s" % (state["locale"], state.get("es"), "Seeds" in bottom()))

    events = [("call", dump), ("call", check_spanish), ("tap_label", "Ajustes"), ("key", 0),
              ("call", dump), ("tap_label", "Idioma"), ("key", 0), ("call", dump),
              ("tap_label", "English"), ("key", 0), ("wait", 2), ("key", nds.KEY_B), ("wait", 2),
              ("call", dump), ("call", check), ("call", stop)]
    nds.sim_script(events)
    Controller.get_instance().start(initial_destination=Destination(MainMenuView))


def run_flow(prefix, taps):
    from seedsigner.models.seed import Seed
    from seedsigner.views.view import Destination, MainMenuView

    from seedsigner.models.settings import Settings, SettingsConstants

    controller = Controller.get_instance()
    # the vectors are testnet transactions (as a user would set in Settings)
    Settings.get_instance().set_value(SettingsConstants.SETTING__NETWORK, SettingsConstants.TESTNET)
    controller.storage.set_pending_seed(Seed(read(prefix + ".mnemonic.txt").split()))
    controller.storage.finalize_pending_seed()

    events = []
    for tap in taps:
        events += [("call", dump), ("tap_label", tap), ("key", 0)]
        if tap == "Scan":
            events.append(("camera", read(prefix + ".txt").encode()))
    # let the animated QR run through all its parts (~6 per second) first
    events += [("wait", 200), ("call", dump), ("call", lambda: check_signed(prefix)), ("call", stop)]
    nds.sim_script(events)
    controller.start(initial_destination=Destination(MainMenuView))


# The taps a user makes on the bottom screen, by button label.
SINGLESIG_TAPS = ["Scan", "8b218e81", "Review details", "Continue", "Review recipients",
                  "Next recipient", "Next", "Approve transaction"]

MODE = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "preloaded"
if MODE != "scan_intro":  # the flows below scan straight away
    from seedsigner.gui import SETTING__NDS_SCAN_INTRO
    from seedsigner.models.settings import Settings, SettingsConstants
    Settings.get_instance().set_value(SETTING__NDS_SCAN_INTRO, SettingsConstants.OPTION__DISABLED)
if MODE == "typed":
    run_typed_seed_flow("psbt_base64_singlesig")
elif MODE == "seedqr":
    run_seedqr_flow()
elif MODE == "xpub":
    run_xpub_flow("psbt_base64_singlesig")
elif MODE == "settings":
    run_settings_flow()
elif MODE == "passphrase":
    run_passphrase_flow("psbt_base64_singlesig")
elif MODE in ("transcribe", "transcribe_compact"):
    run_transcribe_flow("psbt_base64_singlesig", MODE == "transcribe_compact")
elif MODE == "language":
    run_language_flow()
elif MODE == "sound":
    run_sound_flow()
elif MODE == "battery":
    run_battery_flow("psbt_base64_singlesig")
elif MODE == "scribble_mic":
    run_scribble_mic_flow()
elif MODE == "camera_seed":
    run_camera_seed_flow()
elif MODE == "scan_intro":
    run_scan_intro_flow("psbt_base64_singlesig")
elif MODE == "final_word":
    run_final_word_flow("psbt_base64_singlesig")
elif MODE == "dice":
    run_dice_flow()
elif MODE == "explorer":
    run_explorer_flow("psbt_base64_singlesig")
elif MODE == "backup":
    run_backup_flow("psbt_base64_singlesig")
elif MODE in ("address", "address_foreign"):
    run_address_flow("psbt_base64_singlesig", MODE == "address")
else:
    run_flow("psbt_base64_singlesig", SINGLESIG_TAPS if MODE == "preloaded" else MODE.split(","))
print("PASSED" if RESULT and all(RESULT.values()) else "FAILED")
