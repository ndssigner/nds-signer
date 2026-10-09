#!/bin/sh
# dev helper: the README's screenshots (docs/images/), rendered on the host
# from the simulator's display lists with the ROM's fonts and sizes
# (tools/dev/render_gallery.py). The camera image is not simulated, so no
# scanning screens; the tones' screens are (tests/host/sim: the reference
# implementation stands in for the microphone and the speaker).
#   tools/dev/readme_screenshots.sh <python with Pillow and qrcode> [version]
cd "$(dirname "$0")/../.."
PY=$1; VERSION=${2:-$(git describe --tags --abbrev=0 2>/dev/null || echo dev)}
rm -rf build/shots build/shots_png && mkdir -p build/shots docs/images
make -s -C tests/host frozen >/dev/null
for m in preloaded explorer transcribe scribble_mic tones tones_seed tones_export; do
	tools/dev/runflow.sh -X heapsize=6M flow_check.py /source/tests/vectors $m \
		--gallery=/source/build/shots --version="$VERSION" 2>&1 | grep -E "^(ok|FAIL)" | cut -c1-60
done
"$PY" tools/dev/render_gallery.py build/shots build/shots_png --all >/dev/null
"$PY" - <<'PYEOF'
from PIL import Image
shots = [("home", "flow-preloaded_01_MainMenuScreen"),
         ("review", "flow-preloaded_03_PSBTOverviewScreen"),
         ("recipient", "flow-preloaded_06_PSBTAddressDetailsScreen"),
         ("math", "flow-preloaded_05_PSBTMathScreen"),
         ("signed-qr", "flow-preloaded_09_QRDisplayScreen"),
         ("addresses", "flow-explorer_06_ToolsAddressExplorerAddressListScreen"),
         ("seedqr-map", "flow-transcribe_07_SeedTranscribeSeedQRZoomedInScreen"),
         ("new-seed", "flow-scribble_mic_03_ToolsScribbleMicEntropyScreen"),
         # ur-tones (experimental): listening, a made-up PIN, playing, a seed as tones
         ("tones-listen", "flow-tones_06_ScanScreen"),
         ("tones-pin", "flow-tones_seed_04_ScanScreen"),
         ("tones-play", "flow-tones_29_QRDisplayScreen"),
         ("tones-export", "flow-tones_export_08_ButtonListScreen")]
for name, src in shots:
    im = Image.open("build/shots_png/%s.png" % src).convert("RGB")
    # both screens with the gap between them, on a dark rounded "console"
    pad = 16
    out = Image.new("RGB", (im.width + 2 * pad, im.height + 2 * pad), (40, 40, 44))
    out.paste(im, (pad, pad))
    out.save("docs/images/%s.png" % name, optimize=True)  # no metadata
    print("docs/images/%s.png" % name)
PYEOF
