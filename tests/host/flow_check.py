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
    from seedsigner.gui.screens.screen import QRDisplayScreen
    from seedsigner.models.decode_qr import DecodeQR

    parts = QRDisplayScreen.last_parts
    if not parts:
        raise FlowBasedTestException("no QR was displayed")
    decoder = DecodeQR()
    for part in parts:
        decoder.add_data(part)
    ok = decoder.is_complete and decoder.get_psbt().to_string() == read(prefix + ".signed_trimmed.txt")
    RESULT[prefix] = ok
    print("ok  " if ok else "FAIL", prefix, "flow: signed PSBT QR (%d parts)" % len(parts))


def stop():
    raise StopFlowBasedTest()


def dump():
    if VERBOSE:
        nds.sim_dump()


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
    events += [("call", dump), ("call", lambda: check_signed(prefix)), ("call", stop)]
    nds.sim_script(events)
    controller.start(initial_destination=Destination(MainMenuView))


# The taps a user makes on the bottom screen, by button label.
SINGLESIG_TAPS = ["Scan", "8b218e81", "Review details", "Continue", "Review recipients",
                  "Next recipient", "Next", "Approve transaction"]

TAPS = sys.argv[2].split(",") if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else SINGLESIG_TAPS
run_flow("psbt_base64_singlesig", TAPS)
print("PASSED" if RESULT and all(RESULT.values()) else "FAILED")
