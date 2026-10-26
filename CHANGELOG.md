# Changelog

## Unreleased

- Security: microphone entropy now goes through NIST SP 800-90B's
  Repetition Count and Adaptive Proportion health tests, in C, on every
  buffer; only buffers that pass count towards Done (a stuck or
  near-silent microphone never gets there). A PIN made up for tones uses
  the same tests: before, a dead microphone was accepted. Dropped buffers
  are counted, and [docs/entropy.md](docs/entropy.md) says what "16
  buffers" means ([#8](https://github.com/ndssigner/nds-signer/issues/8),
  tofu_ai).
- Security: closing the lid now also clears the app thread's whole stack,
  where C code that handles keys (libsecp256k1, hashlib, the seed PIN)
  leaves its locals, and the tones' buffers (a seed heard or played as
  tones). `secureZero` clears any length, not only multiples of 4
  ([#12](https://github.com/ndssigner/nds-signer/issues/12), tofu_ai).
  Checked in melonDS over GDB: 6,841 non-zero stack bytes before, none
  after, and the console then powers off.
- ur-tones updated from v0.1.0 to v0.4.0. Same calls and behaviour for
  NDS-Signer; the library now also clears its own copies of seeds, PINs
  and keys, and clears `entropy` when a seed fails to decode (NDS-Signer
  never read it then). Unused parts (fountain codes, public keys) are left
  out by the linker.
- Thanks to merd0ne, who reproduced v0.2.1-alpha's build on two machines,
  and to tofu_ai and DobbyAgent for their review notes.

## v0.2.1-alpha

Security hardening and documentation for reviewers. No new features.

- Security: the Python heap, where seeds, passphrases and PSBTs live, is
  now wiped at start-up too, not only on lid close or power off. Data left
  by the launcher, or by a session that ended without the wipe (battery
  pulled, crash), no longer survives into the next one. Tested in melonDS
  over GDB and on a real DSi; start-up time unchanged.
- Docs for auditors: a [threat model](docs/threat-model.md) (including what
  the launcher leaves behind), an [audit guide](AUDIT.md) with the critical
  files by priority (now with the restore path and the no-network
  guarantee), an [entropy spec](docs/entropy.md), and issues labelled
  [`audit`](https://github.com/ndssigner/nds-signer/labels/audit).
- README and LEEME: documentation grouped by reader; thanks to shadowbip.

## v0.2.0-alpha

Telephone tones ([ur-tones](https://github.com/ndssigner/ur-tones) v0.1.0),
experimental: PSBTs and seeds without a camera, by cable or through the air.
Tested on a DSi XL with Sparrow and the ur-tones web tool, both ways.

- Experimental: *Scan → Listen to tones* hears PSBTs, seeds (with an
  optional PIN) and other URs sent as telephone tones
  ([ur-tones](https://github.com/ndssigner/ur-tones)), by cable or through
  the air; the receiver is ur-tones' C library (integers only). The top
  screen shows the progress (frames, the current frame, the tones as they
  come, the level), the bottom one Cancel and the microphone's gain; a PIN
  can be made up from the microphone's noise, for the sender to type.
- Experimental: the DSi plays tones too — the signed PSBT (*Play as tones*,
  next to its QR code, in UR parts of 100 bytes with fountain codes, in a
  loop until Stop) and a seed with an optional PIN (*Backup seed → Export as
  tones*, showing its fingerprint; for a tape backup, by cable).
- A made-up PIN has 12 characters (60 bits), shown in groups of four; a
  shorter PIN is accepted, with a warning.
- README and LEEME: a section on the tones, and screenshots of their
  screens (`tools/dev/readme_screenshots.sh`, now with the tone flows).

## v0.1.0-alpha

First public version. Runs SeedSigner (pinned at `cfaf443`) and embit 0.8.0
unmodified on the Nintendo DSi, through MicroPython 1.29.

- Scan, review and sign PSBTs (animated UR or static QR); signed PSBT as an
  animated QR code.
- Seeds in RAM only: touch keyboard (12/24 words), SeedQR and CompactSeedQR,
  BIP-39 passphrase.
- New seeds: dice, camera (SeedSigner's image entropy), scribble +
  microphone; final word calculator.
- Backups: seed words, SeedQR transcription with a map of the code, backup
  verification.
- xpub export, address explorer with QR codes, address verification.
- Dual-screen touch interface in SeedSigner's style; 16 languages
  (SeedSigner's translations, console language by default); optional
  sounds; scan preparation with rear/front camera choice.
- Security: wireless driver not linked and wireless chips powered off; no
  storage access; closing the lid or pressing power wipes memory and turns
  the console off; low battery warning before signing or showing secrets.
- Reproducible build in a pinned Docker image.
