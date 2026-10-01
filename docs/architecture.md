# NDS-Signer architecture: reusing SeedSigner

Status: **implemented.** Proposed on 2026-09-26; the MicroPython spike (end
of this document) succeeded in the emulator and then on a real DSi XL, and
NDS-Signer v0.1.0-alpha is built this way. Sections below keep the reasoning
as it was written; [how-it-was-built.md](how-it-was-built.md) tells the rest.

## Goal

NDS-Signer must track [SeedSigner](https://github.com/SeedSigner/seedsigner)
as closely as possible: its PSBT verification logic, UX flows and texts are
battle-tested and keep improving. SeedSigner is written in Python for a
Raspberry Pi Zero, so the question is how to reuse that Python on a Nintendo
DSi (ARM946E-S @ 134 MHz, no FPU, 16 MB RAM, no OS).

## Why not a Python-to-C transpiler

| Tool | Output | Problem |
| :--- | :--- | :--- |
| Cython, Nuitka, mypyc | C | The generated C still calls into the CPython runtime (libpython), which would have to be ported and shipped too. |
| Shed Skin, LPython, py2many | C / C++ | Only a statically typed subset of Python. |
| Codon | LLVM binary | Not fully Python-compatible, no bare-metal ARMv5 target, license not fully open. |

The subset-only tools share a blocker: **integers are fixed-width (64 bit)**,
while Bitcoin code (embit, and SeedSigner through it) relies on arbitrary
precision integers (base58, BIP-32, amounts). SeedSigner also uses Pillow,
threads, gettext and dynamic imports. Making it compile would mean rewriting it
in a subset, i.e. a fork that no longer syncs with upstream. The generated C is
also unreadable, which is unacceptable for auditable wallet software.

## What changes in SeedSigner

Git history analysis from v0.8.0 (2024-08-17) to 2026-09-25 (upstream
`cfaf443`). The project has 2,386 commits since 2020, ~400 per year.

| Component | Activity | Nature of the changes |
| :--- | :--- | :--- |
| `models/psbt_parser.py` | 30 commits, churn 1.4x its size | **Security**: change-output ownership, multisig cosigner checks, high-fee warning (many in Sep 2026) |
| embit (dependency) | 44 commits | **Security**: stricter PSBT validation per BIP-174/370 (Aug-Sep 2026) |
| `views/` (screen flows) | 115 commits | Features and flows; covered by the `test_flows_*` suites |
| `gui/` (Pillow rendering) | ~120 commits | Layout for a 240x240 joystick display |
| `settings_definition.py` + translations | ~16k lines in catalogs | New languages and settings |
| `decode_qr`, `encode_qr`, `seed`, `ur2`, `qr_type` | Low (`seed.py`: 0 commits) | Occasional bug fixes |
| `hardware/` | Medium | Raspberry Pi drivers (not applicable) |

Key finding: **the part that changes most, and where a porting mistake is most
dangerous, is PSBT verification** (SeedSigner + embit). A manual C port would
always lag behind security fixes. The parts that cannot be reused (`gui/`,
`hardware/`) are not blocked by the language: they are tied to Pillow, the
Raspberry Pi and a 240x240 screen.

## Proposed hybrid: C for the machine, Python for the knowledge

| Component | Technique |
| :--- | :--- |
| `models/` (`psbt_parser`, `decode_qr`, `encode_qr`, `seed`, `settings`), `helpers/ur2`, embit | **Upstream Python, unmodified**, precompiled to bytecode with `mpy-cross` and frozen into the ROM (MicroPython) |
| `views/` (flows, texts, navigation) | **Upstream Python, unmodified.** Views never draw: they call `self.run_screen(ScreenClass, **kwargs)`, a ready-made boundary |
| `gui/screens` | **Native rewrite** for the dual screen + touch UI, keeping the same class names and parameters the views pass |
| Translations, BIP-39 wordlist, settings definitions | **Build-time generators**: upstream data files (`.po`, JSON, wordlists) turned into tables automatically |
| Camera, QR decoding (quirc), display, touch | **Native C** (phases 1-3) |
| Cryptography (libsecp256k1) | **Native C**, through the MicroPython binding embit already supports (Specter-DIY) |
| `hardware/`, `version.py`, CI tooling | Not applicable |

### Staying in sync with upstream

- SeedSigner and embit are added as git submodules pinned to a specific commit.
- Syncing means bumping the submodule, rebuilding and running the tests.
- Upstream's own tests (67 in `test_psbt_parser.py`, 18 in
  `test_decodepsbtqr.py`, the flow suites) are reused, and also verify that our
  native screens accept exactly what the views pass them.

### Precedents

MicroPython + embit is the stack of other air-gapped signers:
[Specter-DIY](https://github.com/cryptoadvance/specter-diy) (STM32) and
[Krux](https://github.com/selfcustody/krux) (Kendryte K210, 8 MB RAM). The DSi
has 16 MB. `urtypes`, a SeedSigner dependency, comes from the Krux project.

## Risk and plan B

**Risk to measure first:** whether MicroPython on the DSi has enough memory and
speed to load all the views and sign a PSBT. The original DS (4 MB) is likely
out of reach with this approach; DSi / 3DS are the targets anyway (camera).

**Plan B**, if MicroPython does not work out: keep porting to C near
line-by-line, with automatic drift detection. Our C modules are built as a
host shared library and SeedSigner's Python tests run against them, so when
upstream fixes a bug and adds a test, the test fails on our side too.

Either way, the work already done (camera driver, quirc integration, touch UI)
is kept: it becomes the native modules of the hybrid design.

## Next step: MicroPython spike

Success criteria, all in melonDS:

1. MicroPython runs as the ARM9 application on top of the existing C core.
2. Upstream embit and `models/psbt_parser.py`, **unmodified**, parse the
   testnet PSBT from `tests/vectors/` and sign it with a test seed.
3. Measurements recorded: ROM size, free RAM, time to parse and sign.

### Spike results (2026-09-26, melonDS, DSi mode, ARM9 @ 134 MHz)

Branch `spike/micropython`: MicroPython v1.29.0 + embit v0.8.0 **unmodified**
(frozen bytecode) + libsecp256k1 as a native module. Signing the testnet PSBT
from `tests/vectors/` with its test seed produces **byte-identical output** to
embit 0.8.0 on CPython.

| Step | Time |
| :--- | ---: |
| Import embit (frozen) | 59 ms |
| BIP-39 seed (PBKDF2-HMAC-SHA512, 2048 rounds) | 718 ms |
| BIP-32 root key | 29 ms |
| Parse PSBT | 22 ms |
| Sign (1 input) | 167 ms |
| **Total** | **~1.15 s** |

Python heap in use after signing: 24 KB (of 4 MB reserved). ROM grows from
201 KB to 750 KB. Timings come from the emulator; they must be confirmed on a
real DSi (melonDS does not model memory/cache timing exactly).

Milestone 3: SeedSigner's own `models/psbt_parser.py` (upstream `cfaf443`,
unmodified) runs on the DSi on top of it and produces the same summary as on
CPython (amounts, fee, destinations, change detection):
`tests/vectors/psbt_base64_singlesig.summary.txt`. Import + parse: ~1.0 s,
mostly the second PBKDF2 inside `Seed()`.

Scaling (synthetic 10-input P2WPKH PSBT, `tests/vectors/psbt_base64_10in*`,
results identical to CPython): parse ~0.75 s, sign 1.7 s (~170 ms per input,
mostly Python-side BIP-32 derivation, not the C crypto), Python heap 74 KB.
A 10-input PSBT is ~2,000 base64 characters: too dense for a single QR on the
DSi camera, so animated UR QR scanning will be required, as in SeedSigner.

To make upstream code importable, two techniques were needed:

- `tools/upy_transform.py`: build-time AST rewrite of upstream sources for the
  few constructs MicroPython cannot run. Today only `@dataclass` (MicroPython
  drops class annotations, so fields are recorded explicitly). Output is
  readable Python in `build/frozen_py/`.
- `mpy/frozen/compat/`: small stand-ins for CPython stdlib modules
  (`dataclasses`, `typing`, `gettext`, `os`, `pathlib`, `platform`, `time`).
  Anything touching storage fails on purpose.
- `unicodedata.normalize` (BIP-39 mnemonic/passphrase NFKD) is a native module
  backed by utf8proc v2.12.0 (`lib/mpy-usermods/unicodedata`). Verified against
  CPython 3.11 for every character assigned in Unicode 14 plus 20k combining
  sequences in all four forms (0 mismatches), and with the 24 official Japanese
  BIP-39 vectors (NFKD mnemonic + passphrase -> seed), also on the DSi.

Milestone 4a: SeedSigner's `models/decode_qr.py` (QR type detection, base64
and animated UR PSBTs, addresses, SeedQR) runs unmodified on the DSi. It needed
a `re` compatibility layer: MicroPython's regex engine has no flags and no
counted repetition (`\d{3}` silently never matches) and cannot fit ranges like
`{25,62}` at all, so `mpy/frozen/compat/re.py` translates what it can and
falls back to a small pure-Python engine (`_pyre.py`) for the rest. It is
verified against CPython with SeedSigner's patterns plus 6,000 random inputs.

Host test loop (no emulator, ~0.5 s): the MicroPython unix port is built with
the same native modules (`make mpy-unix`), and `make -C tests/host seedsigner`
runs the same scripts on MicroPython and CPython and diffs the results. The
same scripts also run unchanged on the DSi (`make MPY_SPIKE=1`).

Milestone 4b: SeedSigner's own `controller.py` and `views/` run unmodified on
NDS-Signer's native screens. In melonDS (`make AUTOTEST=1 MPY_APP=1`), with the
emulated camera looking at the testnet PSBT QR, the full flow (Home -> Scan ->
select signer -> review, incl. upstream's "Full Spend!" warning -> recipients
-> approve) runs in under 15 s and ends with the signed PSBT as an 8-part
animated UR, identical to what SeedSigner produces on CPython.

Milestone 4c: the signed PSBT is shown as an animated QR code drawn natively
(Project Nayuki's qrcodegen, ECC L like SeedSigner, a new part every 5/30 s,
UP/DOWN change the background brightness and are saved to Settings, as
upstream). Frames are composed off-screen and copied by DMA after VBlank, so a
half-drawn QR is never visible. Verified from the outside: screenshots of the
emulator decoded on the host (`tools/png_to_pgm.py | build/qrdecode`, same
quirc) reassemble, via SeedSigner's DecodeQR, the exact signed PSBT expected.

How the upstream UI code is reused:

- Views call `self.run_screen(ScreenClass, **kwargs)`. NDS-Signer implements
  the screen classes natively (`mpy/overlay/seedsigner/gui`), with upstream's
  class names. Their accepted arguments, default texts and the titles/buttons
  upstream screens set in `__post_init__` are **generated from the upstream
  sources** (`tools/gen_gui_api.py` -> `gui/_upstream.py`), so they follow
  upstream changes automatically. Screens without a native version yet get a
  generic stand-in (title, text, buttons), so every upstream view imports.
- `tools/upy_transform.py` also rewrites PEP 585 generic bases, `cls.__new__`
  and f-strings (MicroPython's are limited, e.g. no nested quotes).
- A host simulator of the `nds` module (`tests/host/sim/nds.py`) runs the same
  flow headlessly; `make -C tests/host seedsigner` checks it end to end.

Findings:

- On MicroPython, embit 0.8.0 **requires** the native `secp256k1` module
  (no pure-Python fallback), which matches the plan (crypto in C).
- `random` is replaced by a frozen module that raises on use: embit only needs
  it for key generation helpers, and NDS-Signer must never use a PRNG.
- libsecp256k1 upgraded to v0.8.0 (from the 2021 commit secp256k1-embedded
  used); signatures unchanged, library tests pass in 32-bit mode.
- Timings on a real DSi XL (2026-09-26): PBKDF2 418 ms, BIP-32 derivation
  301 ms, signing 70 ms, faster than in melonDS
  ([history/hardware-reports](history/hardware-reports/)).
