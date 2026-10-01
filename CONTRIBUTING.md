# Contributing

Thanks for helping. NDS-Signer handles Bitcoin seeds, so changes are
reviewed strictly: please read the rules below before opening a pull
request. Security problems go through [SECURITY.md](SECURITY.md), not
public issues.

## Most welcome

- Testing on real hardware (DSi, DSi XL, 3DS in DSi mode) and reporting what
  works and what does not, with photos of the screen.
- Fixes to NDS-Signer's own layer: screens, drivers, build, tests, docs.
- The open problems in [docs/help-wanted.md](docs/help-wanted.md).
- Translations of NDS-Signer's own strings (`l10n/<locale>.po`); SeedSigner's
  strings are translated upstream, in
  [seedsigner-translations](https://github.com/SeedSigner/seedsigner-translations).

## Rules: changes that are always rejected

1. **Networking.** Anything that initialises, links or talks to the wireless
   hardware, or adds any other way to send data out (besides showing QR
   codes on the screen).
2. **Storage.** Anything that writes to the SD card or the internal memory,
   or links a storage driver. Seeds, passphrases, keys and PSBTs live in RAM
   only.
3. **Entropy.** Any change to where new seeds get their randomness from, or
   any use of a pseudo-random generator for key material. New entropy sources
   need a design discussion in an issue first.
4. **SeedSigner's and embit's code.** NDS-Signer runs them unmodified.
   PSBT verification, seed handling and signing are fixed upstream, then the
   pinned versions are updated here. Build-time adaptations
   (`tools/upy_transform.py`) must stay mechanical and must not change what
   the code does.
5. **Dependencies.** No new dependencies, and no changes to the pinned
   versions (submodules, `lib/`, the Docker image digest, packages in the
   `Dockerfile`), unless the pull request explains why and links the
   upstream release or commit. Vendored code is copied unmodified, or its
   changes are listed in [lib/README.md](lib/README.md).
6. **Obfuscation.** Generated, minified or binary files that cannot be
   reviewed, unless they are produced by the build from files in this
   repository.
7. **Weakening the wipe.** Anything that keeps secrets in memory longer than
   needed, or that lets the console sleep with a seed loaded.

## How to send a change

1. Open an issue first for anything bigger than a small fix.
2. Keep pull requests small and focused; explain what and why.
3. The build must stay reproducible (same commit, same SHA-256).
4. Run the host tests and add one for your change:
   `make -C tests/host all seedsigner PYTHON=<python with tests/requirements.txt>`
   (see the README). CI runs them on every pull request.
5. If the change affects the console (screens, camera, input), say how you
   tested it on real hardware, or ask for help testing.

## Style

Follow the code around your change: SeedSigner's names and texts where the
code mirrors SeedSigner, short comments that explain why, English in code
and technical docs.
