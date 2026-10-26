# Threat model

What NDS-Signer protects, what it trusts, and where an attacker could get in.
It is a starting point for auditors, not a claim of security: NDS-Signer is an
alpha and has not been audited. See also [AUDIT.md](../AUDIT.md) (where to
look) and [entropy.md](entropy.md) (how new seeds are made).

## Assets

| Asset | Where it lives | How long |
| :--- | :--- | :--- |
| Seed (BIP-39 words, passphrase) | ARM9 RAM | Until the seed is discarded, the lid is closed or the console is switched off |
| Private keys | ARM9 RAM, derived on demand by embit / libsecp256k1 | While signing |
| PSBTs (unsigned and signed) | ARM9 RAM, camera frames, QR on screen | While scanning / showing |
| xpubs, addresses | Shown as QR | Public, but they reveal the wallet's history |

NDS-Signer never writes to the SD card or any other non-volatile memory
(`mpy/overlay/seedsigner/hardware/microsd.py` always reports no card).
Closing the lid or pressing power overwrites everything that may hold a
secret and switches the console off instead of sleeping
(`arm9/src/wipe.c`, `arm7/src/main.c`).

## Trust chain

```
Power on → DSi boot ROM and firmware (Nintendo, closed)
         → Unlaunch (exploit-based loader)
         → TWiLight Menu++ (from the SD card)
         → NDS-Signer ROM (.nds file on the SD card)
```

NDS-Signer does not and cannot verify anything that runs before it. Whoever
can write to the SD card can replace the ROM. Users are expected to check
the ROM's hash against the release (see [install.md](install.md)) — the
check happens on another computer, not on the console.

The launcher also hands over the hardware in whatever state it leaves it.
NDS-Signer powers the wireless hardware off at start and links no network
or SD/NAND driver (`arm7/src/main.c`), but resets nothing else to a known
state: registers, other peripherals, memory contents. What an honest
launcher leaves behind has not been inventoried yet
([#12](https://github.com/ndssigner/nds-signer/issues/12)).

## Attack surfaces

### 1. New seed generation

Three sources: camera image and dice (SeedSigner's own tools) and scribble +
microphone (NDS-Signer's own). If the input is predictable, the seed is.
Details and open questions: [entropy.md](entropy.md).

### 2. Data coming in through the camera

Every QR the console reads is attacker-controlled: PSBTs, SeedQR, xpubs,
descriptors, animated UR parts. The path is camera driver
(`arm7/src/aptina*.c`, `arm9/src/camera.c`) → decoder (quirc,
`arm9/src/quirc_nds.c`, `arm9/src/qr_scanner.c`, `arm9/src/qr_type.c`) →
Python (SeedSigner / embit / urtypes). Questions:

- Can a crafted QR cause memory corruption in the C decoding path?
- Can a crafted PSBT crash the app or exhaust its memory (MicroPython heap)?
- Does anything behave differently from SeedSigner on a Raspberry Pi
  because of the port (`mpy/frozen/compat`, `mpy/frozen/hwstubs`)?

PSBT verification itself (change detection, amounts, fees) is SeedSigner's
and embit's code, run unmodified; problems there belong upstream (see
[SECURITY.md](../SECURITY.md)).

### 3. What is shown vs. what is signed

SeedSigner's views decide what to show; NDS-Signer redraws them for two
screens (`mpy/overlay/seedsigner/gui/`). An error in that layer could show
an address or amount that is not the one being signed (truncation, wrong
field, stale screen). This layer is NDS-Signer's own and is in scope.

### 4. Data going out

Signed PSBTs, xpubs and seeds (SeedQR, tones) leave the device as QR codes
(`arm9/src/qr_display.c`) or, experimentally, as sound
(`arm9/src/tones_audio.c`, `mpy/overlay/seedsigner/gui/nds_tones.py`,
`third_party/ur-tones`). Sound reaches anything nearby with a microphone;
tones that carry a seed are protected by a PIN, whose design is in the
ur-tones repository.

### 5. Side channels and physical access

- Timing: signing uses libsecp256k1 (constant-time by design); the
  MicroPython layers above it are not.
- Power, electromagnetic emissions, cold-boot RAM reading, modified
  hardware: out of scope (see below). The wipe on lid close reduces, not
  removes, the cold-boot window.

### 6. Build and supply chain

The ROM is built from pinned submodules (see [AUDIT.md](../AUDIT.md)) in
the devkitPro Docker image, and the build is reproducible: building the same
version gives the same SHA-256 as the release (see [install.md](install.md)).
An auditor can check that the published ROM comes from the published code.

## Scope

**In scope:** everything under `arm7/`, `arm9/`, `mpy/`, `shared/`, `lib/`
modifications (listed in [lib/README.md](../lib/README.md)), the build, and
the documentation's instructions.

**Out of scope:** bugs in SeedSigner, embit, libsecp256k1 or MicroPython
that also affect them elsewhere (report upstream, tell us too); anything
that runs before NDS-Signer (boot chain, SD card contents); physical attacks;
emulators, which are for development only.

## Open questions

- How much entropy does the scribble + microphone source really contribute?
  ([entropy.md](entropy.md))
- Has the C QR path (quirc + NDS glue) been fuzzed? Not yet.
- Has anyone other than the maintainer reproduced a release build? One
  person so far: v0.2.1-alpha on Linux x86_64 and macOS arm64, both
  matching ([#11](https://github.com/ndssigner/nds-signer/issues/11)); a
  second is still wanted.
- What state does the launcher leave the hardware in, and what should
  NDS-Signer reset at start? ([#12](https://github.com/ndssigner/nds-signer/issues/12))
