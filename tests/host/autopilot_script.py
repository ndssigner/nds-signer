# Taps for the unattended emulator run (make AUTOTEST=1 MPY_APP=1): the seed
# is typed on the touch keyboard, then the camera scans the PSBT QR
# (tools/qr_to_png.py tests/vectors/psbt_base64_singlesig.txt) and it is signed.
#
# Setup a user would do in Settings, until that screen is native: testnet.
SETUP = """
from seedsigner.models.settings import Settings, SettingsConstants
Settings.get_instance().set_value(SettingsConstants.SETTING__NETWORK, SettingsConstants.TESTNET)
"""

# PUBLIC test seed of the vector (tests/vectors/psbt_base64_singlesig.mnemonic.txt)
WORDS = "height demise useless trap grow lion found off key clown transfer enroll".split()


def _type(words):
    events = []
    for n, word in enumerate(words):
        for i, letter in enumerate(word[:4]):
            events.append(("tap_key", letter))
            if n == 1 and i == 1:
                events.append(("wait", 240))  # screenshot: keyboard mid-word
        events.append(("tap_label", word))
    return events


EVENTS = ([("log", "start"), ("exec", SETUP), ("tap_label", "Seeds"),
           ("tap_label", "Enter 12-word seed")] + _type(WORDS) +
          [("wait", 180), ("tap_label", "Done"), ("wait", 180), ("tap_label", "Scan transaction")] +
          [("tap_label", label) for label in ("Review details", "Continue", "Review recipients",
                                              "Next recipient", "Next", "Approve transaction")] +
          [("log", "done")])
