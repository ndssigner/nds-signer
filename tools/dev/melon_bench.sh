#!/bin/sh
# dev helper: runs nds-signer.nds (built with DEVBUILD=1 AUTOTEST=1
# AUTOPILOT=dev) in melonDS, waits for the diagnostics report QR and decodes it.
# usage: tools/dev/melon_bench.sh <out.png> [timeout_s]
cd "$(dirname "$0")/../.."
OUT=$1; LIMIT=${2:-300}
pkill -9 -x melonDS
(emulator/melonDS.app/Contents/MacOS/melonDS "$(pwd)/nds-signer.nds" >/dev/null 2>&1 &)
perl -e 'select(undef,undef,undef,5)'
WID=$(swift tools/dev/melon_window.swift 2>/dev/null | head -1 | cut -d' ' -f1)
t=0
while [ $t -lt "$LIMIT" ]; do
	perl -e 'select(undef,undef,undef,10)'; t=$((t + 10))
	screencapture -x -o -l "$WID" "$OUT"
	tools/dev/decode_photo.sh "$OUT" 2>&1 | grep -q "no QR" || break
done
echo "after ${t}s"
tools/dev/decode_photo.sh "$OUT"
pkill -9 -x melonDS
