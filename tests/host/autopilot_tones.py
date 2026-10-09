# Taps for the unattended emulator run of ur-tones (make AUTOTEST=1 MPY_APP=1
# AUTOPILOT=tones): the seed is typed, then Scan transaction -> Listen to
# tones (experimental) -> Start listening, with melonDS's microphone playing
# a WAV of the PSBT's frames (tools/dev/tones_wav.py); then it is signed, and
# the signed PSBT is played back as tones.
from autopilot_script import SETTINGS, WORDS, _type

EVENTS = ([("log", "start")] + SETTINGS + [("tap_label", "Seeds"), ("tap_label", "Enter 12-word seed")]
          + _type(WORDS) +
          [("wait", 60), ("tap_label", "Done"), ("wait", 60), ("tap_label", "Scan transaction"),
           ("tap_label", "Listen to tones (experimental)"), ("wait", 120),
           # developer builds: the frames, synthesised by the DSi itself, stand in
           # for the microphone (melonDS plays a WAV only while a key is held)
           ("exec", "from seedsigner.gui.hw import nds\nimport test_vectors\n"
                    "parts = test_vectors.DATA['psbt_base64_singlesig.ur.txt'].split()\n"
                    "print('autopilot: loopback', nds.tones_loopback('\\n'.join(nds.tones_ur_to_frame(p) for p in parts)))"),
           ("tap_label", "Start listening"),
           ("log", "listening")] +
          [("tap_label", label) for label in ("Review details", "Continue", "Review recipients",
                                              "Next recipient", "Next", "Approve transaction")] +
          # and the signed PSBT back as tones, for 30 s, then Stop
          [("wait", 120), ("tap_label", "Play as tones (experimental)"), ("wait", 60),
           ("tap_label", "Start playing"), ("log", "playing"), ("wait", 1800), ("tap_label", "Stop"),
           ("log", "done")])
