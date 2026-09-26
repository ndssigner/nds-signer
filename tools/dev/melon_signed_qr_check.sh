#!/bin/bash
# macOS dev helper: runs nds-signer.nds in melonDS (emulator/melonDS.app),
# waits, screenshots the animated signed QR several times, decodes the frames
# with the host quirc (build/qrdecode) and reassembles them with SeedSigner's
# DecodeQR. Usage: tools/dev/melon_signed_qr_check.sh <seconds> <python-with-embit>
set -e
cd "$(dirname "$0")/../.."
WAIT=${1:-50}; PY=${2:-python3}
OUT=$(mktemp -d)
pkill -9 -x melonDS 2>/dev/null || true; sleep 1
(emulator/melonDS.app/Contents/MacOS/melonDS "$(pwd)/nds-signer.nds" > "$OUT/melon.log" 2>&1 &)
sleep "$WAIT"
osascript -e 'tell application "System Events" to set frontmost of (first process whose name is "melonDS") to true' >/dev/null 2>&1
sleep 1
read -r WID _ < <(swift tools/dev/melon_window.swift 2>/dev/null)
for i in $(seq 1 30); do screencapture -x -o -l "$WID" "$OUT/f_$i.png"; sleep 0.12; done
for i in $(seq 1 30); do tools/png_to_pgm.py "$OUT/f_$i.png" | build/qrdecode || true; done | sort -u > "$OUT/parts.txt"
echo "decoded parts: $(wc -l < "$OUT/parts.txt")"
PYTHONPATH=third_party/seedsigner/src:mpy/frozen/hwstubs "$PY" - "$OUT/parts.txt" <<'PYEOF'
import sys
from seedsigner.models.decode_qr import DecodeQR
d = DecodeQR()
for line in open(sys.argv[1]):
    d.add_data(line.strip())
    if d.is_complete:
        break
ref = open("tests/vectors/psbt_base64_singlesig.signed_trimmed.txt").read().strip()
ok = d.is_complete and d.get_psbt().to_string() == ref
print("signed PSBT from screenshots matches reference:", ok)
sys.exit(0 if ok else 1)
PYEOF
cp "$OUT/f_1.png" build/last_melon_screenshot.png
