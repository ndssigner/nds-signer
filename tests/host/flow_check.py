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


def dump():
    if VERBOSE:
        nds.sim_dump()


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
elif MODE == "backup":
    run_backup_flow("psbt_base64_singlesig")
elif MODE in ("address", "address_foreign"):
    run_address_flow("psbt_base64_singlesig", MODE == "address")
else:
    run_flow("psbt_base64_singlesig", SINGLESIG_TAPS if MODE == "preloaded" else MODE.split(","))
print("PASSED" if RESULT and all(RESULT.values()) else "FAILED")
