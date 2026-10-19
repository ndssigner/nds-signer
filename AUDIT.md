# Auditing NDS-Signer

A map for anyone who wants to review NDS-Signer's security. Read the
[threat model](docs/threat-model.md) first; report findings as in
[SECURITY.md](SECURITY.md) (privately for anything that can lose funds or
leak a seed).

NDS-Signer is SeedSigner and embit, run unmodified on MicroPython, plus a
DSi layer. Review effort is best spent on that layer: it is new code and
nobody else has looked at it.

## Getting started

- Build: see [README.md](README.md#build) (devkitPro Docker image). The
  build is reproducible: compare your ROM's SHA-256 with the release's.
- Host tests: `tests/host/Makefile` (targets `seedsigner`, `crawl`,
  `quirc`, `re-compat`, `unicode`, `test_qr_type`); test vectors in
  `tests/vectors/`.
- Architecture: [docs/architecture.md](docs/architecture.md).

## Where to look, by priority

### 1. Secrets and entropy

| Path | What it does |
| :--- | :--- |
| `mpy/overlay/seedsigner/gui/screens/tools_screens.py`, `mpy/overlay/seedsigner/views/nds_tools_views.py` | Scribble + microphone seed generation ([docs/entropy.md](docs/entropy.md)) |
| `arm9/src/mic_entropy.c` | Microphone recording for entropy |
| `arm9/src/wipe.c`, `arm7/src/main.c` | Wiping RAM and powering off on lid close / power button |
| `mpy/overlay/seedsigner/hardware/microsd.py` | Guarantees no SD card access |
| `lib/mpy-usermods/` | libsecp256k1 and hashlib bindings, **modified** from upstream (see [lib/README.md](lib/README.md)) |

### 2. Untrusted input (camera → QR → Python)

| Path | What it does |
| :--- | :--- |
| `arm7/src/aptina.c`, `arm7/src/aptina_i2c.c`, `arm7/src/camera_server.c`, `arm9/src/camera.c`, `shared/include/camera_pxi.h` | Camera driver and ARM7↔ARM9 transfer |
| `arm9/src/qr_scanner.c`, `arm9/src/quirc_nds.c`, `arm9/src/qr_type.c`, `lib/quirc/` | QR decoding in C |
| `mpy/usermods/nds/modnds.c`, `arm9/src/nds_bridge.c` | Boundary between C and Python: buffer lengths, types |
| `mpy/overlay/seedsigner/helpers/qr.py`, `mpy/overlay/seedsigner/helpers/ur2/` | QR output: drawn natively instead of SeedSigner's image helpers; UR (animated QR) parts |

### 3. What the user sees

| Path | What it does |
| :--- | :--- |
| `mpy/overlay/seedsigner/gui/screens/psbt_screens.py` | PSBT review screens (addresses, amounts, fees) |
| `mpy/overlay/seedsigner/gui/screens/seed_screens.py` | Seed words, SeedQR, backup check |
| `mpy/overlay/seedsigner/gui/` (rest), `arm9/src/gfx.c`, `arm9/src/qr_display.c` | Drawing on two screens; QR output |

### 4. Experimental: tones

`arm9/src/tones_audio.c`, `mpy/overlay/seedsigner/gui/nds_tones.py`,
`third_party/ur-tones` (its protocol and the seed PIN are specified there).

### 5. Port compatibility

`mpy/frozen/compat/`, `mpy/frozen/hwstubs/`: stand-ins for CPython and
Raspberry Pi modules that SeedSigner expects. A difference in behaviour here
could change what upstream code does.

## Pinned dependencies

Git submodules in `third_party/` (exact commits: `git submodule status`):

| Dependency | Version |
| :--- | :--- |
| SeedSigner | commit `cfaf443` |
| embit | v0.8.0 (`84cce66`) |
| libsecp256k1 | v0.8.0 (`6e2c8bc`) |
| MicroPython | v1.29.0 (`0fd6c57`) |
| urtypes | `7fb280e` |
| utf8proc | v2.12.0 (`79cdd5a`) |
| ur-tones | `434723e` |

Vendored code in `lib/` with its origins and modifications:
[lib/README.md](lib/README.md). Licences: [THIRD_PARTY.md](THIRD_PARTY.md).

## Known gaps

- No independent audit.
- The scribble + microphone source has no measured entropy figure
  ([docs/entropy.md](docs/entropy.md)).
- The C QR path has not been fuzzed.
