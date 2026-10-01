#!/bin/bash
# Builds the files for testing on a real DSi into dist/ (run on the Mac):
#   dist/para-la-dsi/        ROMs to copy to the SD card
#   dist/imagenes-para-el-mac/  test QR codes to show on the computer screen
set -e
cd "$(dirname "$0")/.."
build() {  # $1 = extra make flags, $2 = output name
	docker run --rm -v "$(pwd)":/source nds-signer-builder sh -c \
		"make -s -C mpy TOPDIR=/source clean >/dev/null; make -s -C arm9 clean >/dev/null; make MPY_APP=1 $1 2>&1" \
		| grep -E "error|built ... nds-signer.nds"
	cp nds-signer.nds "dist/para-la-dsi/$2"
}
rm -rf dist && mkdir -p dist/para-la-dsi dist/imagenes-para-el-mac fotos
build "" nds-signer.nds
build "DEVBUILD=1" nds-signer-dev.nds
tools/qr_to_png.py tests/vectors/psbt_base64_singlesig.txt -o dist/imagenes-para-el-mac/1-transaccion-de-prueba.png
tools/qr_to_png.py tests/vectors/psbt_base64_singlesig.seedqr.txt -o dist/imagenes-para-el-mac/2-semilla-de-prueba-SeedQR.png
# the maintainers' hardware test guides (dev-notes/, not in git)
if [ -d dev-notes/pruebas ]; then
	cp dev-notes/pruebas/guia-pruebas-dsi-xl.md dist/LEEME-guia-de-pruebas.md
	cp dev-notes/pruebas/guia-sparrow-signet.md dist/LEEME-2-sparrow-signet.md
	cp dev-notes/pruebas/guia-xpub-sparrow.md dist/LEEME-3-xpub-a-sparrow.md
	cp dev-notes/pruebas/guia-velocidad-escaneo.md dist/LEEME-4-velocidad-escaneo.md
	cp dev-notes/pruebas/guia-menus-nuevos.md dist/LEEME-5-menus-nuevos.md
	cp dev-notes/pruebas/guia-mejoras-1.md dist/LEEME-6-mejoras.md
	cp dev-notes/pruebas/guia-tapa.md dist/LEEME-7-tapa.md
	cp dev-notes/pruebas/guia-semilla-camara.md dist/LEEME-8-semilla-camara.md
	cp dev-notes/pruebas/guia-semilla-garabato.md dist/LEEME-9-semilla-garabato.md
	cp dev-notes/pruebas/guia-bateria.md dist/LEEME-10-bateria.md
fi
(cd dist/para-la-dsi && shasum -a 256 *.nds > SHA256.txt)
echo "dist/ listo:"; find dist -type f | sort
