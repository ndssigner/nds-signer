#!/usr/bin/env python3
"""A WAV of a UR's parts as ur-tones frames, for melonDS's microphone (the
AUTOPILOT=tones emulator run): one part per line in the input file.

    tools/dev/tones_wav.py tests/vectors/psbt_base64_singlesig.ur.txt build/tones.wav
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "third_party" / "ur-tones" / "reference" / "python"))
import ur_tones  # noqa: E402

parts = [line.strip() for line in pathlib.Path(sys.argv[1]).read_text().split() if line.strip()]
frames = [ur_tones.ur_to_frame(p) for p in parts]
rate = int(sys.argv[3]) if len(sys.argv) > 3 else 16000
samples = ur_tones.render(frames, rate, 40, 20, pause_ms=400)
ur_tones.write_wav(sys.argv[2], samples, rate)
print("%d frames, %.1f s" % (len(frames), len(samples) / rate))
