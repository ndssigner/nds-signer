# How NDS-Signer was built

*[Leer en español](es/como-se-hizo.md)*

NDS-Signer was written by an AI model (Claude Opus 5.5, in Claude Code)
working with one person who set the goals, made the decisions and tested
every build on a real Nintendo DSi XL. This page explains how the project
got to where it is, so anyone can judge how much to trust it, and why.

Short version: **the code that decides what gets signed is not new.** It is
SeedSigner's and embit's, run unmodified. What is new is the layer that
makes it run on a DSi, and that layer is tested against SeedSigner's own
behaviour.

## The starting point

The project started from a written brief:
[history/original-brief.md](history/original-brief.md). It asked for a
SeedSigner-like signer for the DSi in C, with three non-negotiable rules
that still hold:

- **Zero networking**: never initialise or use the wireless hardware.
- **Stateless**: no keys, seeds or PSBTs written to the SD card or any other
  non-volatile memory.
- **No hardware RNG**: entropy comes from the user.

And one directive: *do not reinvent the wheel*, reuse SeedSigner.

## The decision that shaped everything

The first three phases (camera driver, custom ARM7 core, QR scanning with
quirc) were written in C, as planned. Then the plan to *port* SeedSigner to
C was reconsidered ([architecture.md](architecture.md)): SeedSigner's PSBT
verification is the part that changes most often upstream, and it is
security-critical. A hand port would always lag behind its fixes, and every
line translated by hand (or by an AI) is a chance to introduce a bug.

So instead of translating SeedSigner, NDS-Signer **runs it**:
MicroPython on the DSi's ARM9 executes SeedSigner's Python modules and
embit, frozen into the ROM. A series of spikes (tags `spike-m1` to
`spike-m10`) checked each step on the emulated DSi:

1. MicroPython runs on the ARM9 (no OS, no FPU).
2. embit signs a PSBT, **byte-identical** to CPython's result.
3. SeedSigner's `PSBTParser`, `DecodeQR` (including animated UR codes) and
   finally its `Controller` and views run unmodified.
4. Seed entry, passphrase, settings, Unicode normalisation (for BIP-39
   passphrases) and libsecp256k1 v0.8.

Only the screens are rewritten: SeedSigner's views never draw, they call
`run_screen(ScreenClass, **kwargs)`, and NDS-Signer provides screen classes
with the same names and arguments for the dual-screen touch interface.
Mechanical adaptations of upstream code (MicroPython lacks a few Python
features) are made at build time by `tools/upy_transform.py`, never by
editing upstream files. Later, NDS-Signer's menus became its own where the
DS interface needed it (e.g. one *New seed* menu); the core stays upstream.

## Testing

Three layers, from fastest to most real:

- **Host tests** (`tests/host`): a simulator of the DSi screens and input
  drives SeedSigner's real controller through every flow: scan, review and
  sign, seed entry, SeedQR, passphrase, xpub export, address explorer,
  backups, new seeds, settings, languages. Results are compared with
  CPython references (signed PSBTs, UR parts) and upstream's test vectors.
  A crawler presses every reachable menu option. The tests run with the
  ROM's memory size.
- **Emulator** (melonDS): an unattended run types the test seed on the touch
  keyboard, scans a PSBT and signs it; the signed QR code is read back from
  screenshots and checked against the reference.
- **Real hardware**: every feature was tried on a DSi XL, following
  step-by-step guides ([es/pruebas](es/pruebas/)); problems came back as
  photos of the screen, often with the error report as a QR code. Several
  bugs only showed up there (touch readings on the first frame, camera
  sensor behaviour, a missing `/proc/cpuinfo`), and each one led to a host
  test that reproduces it. Reports:
  [history/hardware-reports](history/hardware-reports/).

Milestones on real hardware: first signature (tag `hw-first-signature`),
first real Signet transaction created in Sparrow and broadcast
(`hw-first-signet-tx`), every menu verified (`hw-menus-verified`), the
graphical interface (`hw-ui-style-a`).

## What this means for you

- The AI wrote the DSi layer; it did not write the Bitcoin logic. Review the
  DSi layer critically: [architecture.md](architecture.md) explains where it
  is.
- The project has not been audited by anyone outside it. That is why it is
  an alpha.
- The build is reproducible, so you can check that a release was built from
  this code.
