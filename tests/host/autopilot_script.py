# Taps for the unattended emulator run (make AUTOTEST=1 MPY_APP=1): the seed
# is typed on the touch keyboard, then the camera scans the PSBT QR
# (tools/qr_to_png.py tests/vectors/psbt_base64_singlesig.txt), after the scan
# preparation screen, and it is signed.
#
# Everything goes through the UI, as a user would do it: first the network
# (Settings -> Advanced -> Bitcoin network -> Testnet), back home with B.
KEY_B = 1 << 1
SETTINGS = ([("tap_label", label) for label in ("Settings", "Advanced", "Bitcoin network", "Testnet")]
            + [("key", KEY_B), ("wait", 10)] * 3)

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


EVENTS = ([("log", "start")] + SETTINGS + [("tap_label", "Seeds"),
           ("tap_label", "Enter 12-word seed")] + _type(WORDS) +
          [("wait", 180), ("tap_label", "Done"), ("wait", 180), ("tap_label", "Scan transaction"),
           ("tap_label", "Start scanning")] +
          [("tap_label", label) for label in ("Review details", "Continue", "Review recipients",
                                              "Next recipient", "Next", "Approve transaction")] +
          [("log", "done")])
