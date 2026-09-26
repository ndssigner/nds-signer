# Taps for the unattended emulator run (make AUTOTEST=1 MPY_APP=1): the same
# flow as flow_check.py, with the emulated camera looking at the PSBT QR
# (tools/qr_to_png.py tests/vectors/psbt_base64_singlesig.txt).
#
# Setup a user would do by hand, until seed entry and settings screens exist:
# testnet network and the PUBLIC test seed of the vector.
SETUP = """
from seedsigner.controller import Controller
from seedsigner.models.seed import Seed
from seedsigner.models.settings import Settings, SettingsConstants
Settings.get_instance().set_value(SettingsConstants.SETTING__NETWORK, SettingsConstants.TESTNET)
storage = Controller.get_instance().storage
storage.set_pending_seed(Seed("height demise useless trap grow lion found off key clown transfer enroll".split()))
storage.finalize_pending_seed()
"""

EVENTS = [("log", "start"), ("exec", SETUP)] + [("tap_label", label) for label in (
    "Scan", "8b218e81", "Review details", "Continue", "Review recipients",
    "Next recipient", "Next", "Approve transaction")] + [("log", "done")]
