# NDS-Signer architecture: reusing SeedSigner

Status: **proposed** (2026-09-26). To be confirmed by the MicroPython spike
described at the end of this document.

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
