# Help wanted

Open problems that are not needed for the MVP but would make NDS-Signer
better. Each entry records what is already known, so nobody starts from zero.

## Camera exposure when scanning bright screens

**Symptom.** Scanning an animated QR code on a bright computer screen is slow
or stalls. The QR code is in view but most frames do not decode. On a real
DSi XL (2026-09-26), one scan saw the QR in 45 of 51 frames and decoded only
5 (35.6 s). With the screen brightness lowered, the same scan took 5.2 s.

**Cause (likely).** The outer camera's auto-exposure meters the whole frame.
The frame around the screen is dark, so the camera raises the exposure and
the screen saturates: white modules bleed into black ones and quirc cannot
read the grid.

**What was tried.** The Aptina MT9V113 MCU variables `AE_BASETARGET`
(0xA24F, default 0x70 in `arm7/src/aptina.c`) and `AE_WINDOW_POS/SIZE`
(0xA202/0xA203) were written while streaming, followed by `SEQ_CMD` refresh
(0xA103 = 5). On hardware the viewfinder then went dark and black. Frames
stopped matching the 640x480 transfer, and re-sending the capture mode
(`SEQ_CMD` = 2) did not bring them back. melonDS does not model the sensor's
sequencer, so only real hardware can test this. The attempt was removed. See
commits 686695b and 6565c8c for the code.

**Ideas.**
- Write the AE variables without the refresh, or set them in `aptInit()`
  before the first capture, then check whether they take effect.
- Look at how other DSi homebrew or the DSi camera app handles exposure.
- Software side: an adaptive (local) threshold before quirc, which copes
  better with blooming and vignetting than quirc's global Otsu threshold.
  `make -C tests/host quirc` can measure it on synthetic frames. Add
  bloom and vignetting to `tests/host/quirc_images.py` first.

**Safety net already in place.** If no frame arrives for 1 s while scanning,
`scannerPoll()` restarts the transfer and re-sends the capture mode. Its count
is shown as `rs` in the developer build's scan statistics.
