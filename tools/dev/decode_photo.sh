#!/bin/bash
# Decodes QR codes in photos (HEIC/JPEG/PNG) the user drops into fotos/,
# e.g. the developer build's diagnostics or error report QR. macOS only (sips).
cd "$(dirname "$0")/../.."
make -s -C tests/host qrdecode >/dev/null
for photo in "${@:-fotos/*}"; do
	[ -f "$photo" ] || continue
	tmp=$(mktemp -d)
	# downscale big phone photos a bit: quirc is faster and just as reliable
	sips -s format png -Z 1600 "$photo" --out "$tmp/p.png" >/dev/null 2>&1
	echo "== $photo"
	tools/png_to_pgm.py "$tmp/p.png" | build/qrdecode || echo "(no QR code found)"
	rm -rf "$tmp"
done
