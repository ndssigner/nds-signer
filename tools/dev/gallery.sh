#!/bin/sh
# dev helper: screenshots of every screen, rendered on the Mac from the
# simulator (menu crawler with several scan payloads + the flow tests), as
# build/gallery_png/*.png and build/gallery_png/index.html.
#   tools/dev/gallery.sh <python with Pillow and qrcode> [payloads...]
cd "$(dirname "$0")/../.."
PY=$1; shift
PAYLOADS=${*:-"none psbt_base64_singlesig.txt own_address signmessage settingsqr"}
rm -rf build/gallery build/gallery_png && mkdir -p build/gallery
make -s -C tests/host frozen >/dev/null
for p in $PAYLOADS; do
	build/runflow.sh -X heapsize=32M menu_crawl.py "$p" --gallery=/source/build/gallery 2>&1 | grep "^crawl" | cut -c1-70
done
for m in preloaded typed seedqr passphrase settings xpub address address_foreign backup \
		transcribe transcribe_compact explorer dice final_word; do
	build/runflow.sh flow_check.py /source/tests/vectors $m --gallery=/source/build/gallery 2>&1 \
		| grep -E "^(ok|FAIL)" | cut -c1-60
done
"$PY" tools/dev/render_gallery.py build/gallery build/gallery_png
