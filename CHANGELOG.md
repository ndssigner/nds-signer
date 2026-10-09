# Changelog

## Unreleased

- Experimental: *Scan → Listen to tones* hears PSBTs, seeds (with an
  optional PIN) and other URs sent as telephone tones
  ([ur-tones](https://github.com/ndssigner/ur-tones)), by cable or through
  the air; the receiver is ur-tones' C library (integers only). The top
  screen shows the progress (frames, the current frame, the tones as they
  come, the level), the bottom one Cancel and the microphone's gain; a PIN
  can be made up from the microphone's noise, for the sender to type.

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
