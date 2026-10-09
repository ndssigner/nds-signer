# Third-party software

NDS-Signer is built on the work of these projects. Their licenses apply to
their code; NDS-Signer's own code is MIT ([LICENSE](LICENSE)).

## In the ROM

| Project | Use | License |
| :--- | :--- | :--- |
| [SeedSigner](https://github.com/SeedSigner/seedsigner) (`third_party/seedsigner`) | Views, PSBT verification, seeds, settings, QR encoding/decoding: run unmodified | MIT |
| [SeedSigner translations](https://github.com/SeedSigner/seedsigner-translations) | User interface languages | MIT |
| SeedSigner fonts: Open Sans, Inconsolata, Font Awesome 6 Free (Solid), seedsigner-icons | Rasterised into the ROM at build time (`tools/ttf_to_ndsfont.py`) | Open Sans, Inconsolata, Font Awesome fonts: SIL Open Font License 1.1; seedsigner-icons: SeedSigner (MIT) |
| [embit](https://github.com/diybitcoinhardware/embit) (`third_party/embit`) | Bitcoin library used by SeedSigner | MIT |
| [urtypes](https://github.com/selfcustody/urtypes) (`third_party/urtypes`) | Uniform Resources (animated QR) types | MIT |
| [MicroPython](https://github.com/micropython/micropython) and micropython-lib (`third_party/micropython`) | Python runtime on the DSi | MIT (micropython-lib modules: MIT or Python Software Foundation License, see their headers) |
| [libsecp256k1](https://github.com/bitcoin-core/secp256k1) (`third_party/secp256k1`) | Elliptic curve signatures | MIT |
| [secp256k1-embedded](https://github.com/diybitcoinhardware/secp256k1-embedded) and [f469-disco](https://github.com/diybitcoinhardware/f469-disco) MicroPython modules (`lib/mpy-usermods`) | libsecp256k1 and hashlib bindings for MicroPython | MIT; crypto files from trezor-crypto: MIT/BSD-3-Clause (see headers) |
| [utf8proc](https://github.com/JuliaStrings/utf8proc) (`third_party/utf8proc`) | Unicode normalisation (BIP-39 passphrases) | MIT |
| [quirc](https://github.com/dlbeer/quirc) (`lib/quirc`) | QR code decoding from the camera | ISC |
| [ur-tones](https://github.com/ndssigner/ur-tones) (`third_party/ur-tones`) | Tones (experimental): frames, repairs, seed PIN, receiver (`c/ur_tones.c`); its bytewords list is Blockchain Commons' | MIT |
| [QR Code generator](https://github.com/nayuki/QR-Code-generator) (`lib/qrcodegen`) | QR code generation | MIT |
| [Spleen](https://github.com/fcambus/spleen) 5x8 (`lib/fonts`) | Console font for error screens | BSD-2-Clause |
| [dsi-camera](https://github.com/Epicpkmn11/dsi-camera) | Basis of the DSi camera driver (`arm7/src/aptina*.c`, `arm9/src/camera.c`) | Unlicense (public domain) |
| [calico and libnds](https://github.com/devkitPro) (devkitPro) | DS system library, linked into the ROM | calico: Zope Public License 2.1 (ZPL-2.1); libnds: zlib |
| devkitARM runtime (newlib, libgcc) | C runtime, linked into the ROM | newlib: BSD-style licenses; libgcc: GPL with the GCC Runtime Library Exception |

Details on vendored copies and their modifications: [lib/README.md](lib/README.md).

## Build and test tools only

devkitPro's `devkitarm` Docker image, Pillow, FreeType, `qrcode` (Python),
melonDS (emulator, not distributed). None of them end up in the ROM.
