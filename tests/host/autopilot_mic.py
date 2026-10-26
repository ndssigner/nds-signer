# Taps for the unattended emulator run of the microphone's health tests (make
# AUTOTEST=1 MPY_APP=1 AUTOPILOT=mic): Scan -> Listen to tones -> PIN ->
# Make one up. melonDS feeds the microphone only while its microphone hotkey
# is held: with [Mic] InputType = 2 (noise) and the key held, a PIN is made
# up ("Type it on the other device"); otherwise the DSi hears zeros and the
# health tests refuse it ("Too quiet or too regular").
EVENTS = ([("log", "start"), ("tap_label", "Scan"), ("tap_label", "Listen to tones (experimental)"),
           ("wait", 60), ("tap_label", "PIN: none"), ("wait", 30), ("tap_key", "Make one up"),
           ("wait", 900), ("log", "done")])
