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
elif MODE == "settings":
    run_settings_flow()
elif MODE == "passphrase":
    run_passphrase_flow("psbt_base64_singlesig")
else:
    run_flow("psbt_base64_singlesig", SINGLESIG_TAPS if MODE == "preloaded" else MODE.split(","))
print("PASSED" if RESULT and all(RESULT.values()) else "FAILED")
