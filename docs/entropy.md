# New seed entropy

How the **Tools → New seed** sources turn input into a BIP-39 mnemonic. Part of
the [threat model](threat-model.md).

| Source | Code | Whose |
| :--- | :--- | :--- |
| Camera image | SeedSigner's `tools_views.ToolsImageEntropy*`, unmodified; camera frames from `arm9/src/qr_scanner.c` | SeedSigner |
| Dice | SeedSigner's dice tool, unmodified | SeedSigner |
| Scribble + microphone | `mpy/overlay/seedsigner/gui/screens/tools_screens.py` (`ToolsScribbleMicEntropyScreen`), `mpy/overlay/seedsigner/views/nds_tools_views.py` (`ToolsScribbleMicEntropyView`), `arm9/src/mic_entropy.c` | NDS-Signer |

Dice are the only source whose entropy the user can count. The other two
depend on the code and the hardware doing what this page says.

## Scribble + microphone

### What goes in

All of it feeds one SHA-256 hash, started with the tag
`b"NDS-Signer scribble + mic entropy v1"`:

- **Touch:** every new stylus position, as `struct.pack("<HHI", x, y,
  ticks_ms)` — x, y in screen pixels (256 × 192) and the millisecond
  counter. The DSi touch screen reports no pressure.
- **Microphone:** every recorded buffer, raw: 4096 signed 16-bit samples
  (8192 bytes), ¼ s each at the rate set in `arm9/src/mic_entropy.c`
  (`MicRate_Div2`; the header documents it as 16 kHz).
- **End:** `ticks_ms` when the user presses Done.

Samples and touch points are only hashed; they are never stored or sent
(`arm9/src/mic_entropy.c`), and the buffers are cleared when recording
stops.

### When Done is allowed

- at least **256 distinct** stylus positions inside the canvas, and
- at least **16** microphone buffers that pass the **health tests** below.

Every buffer is hashed, healthy or not; only healthy ones count towards the
16. "16 buffers" means 16 buffers *taken* by the screen: if it polls more
slowly than every ¼ s, a new buffer replaces one not yet taken, so
recording can last longer than 4 s. `mic_entropy.c` counts those dropped
buffers (`nds.mic_dropped()`).

### Health tests

NIST SP 800-90B §4.4's two online tests, run in C on each 4096-sample
buffer (`arm9/src/mic_health.c`):

- **Samples:** each sample's 4 lowest bits *that vary* in the buffer (an
  ADC whose lowest bits are always zero is judged on the bits it has).
- **Repetition Count Test:** fails at 11 identical samples in a row.
- **Adaptive Proportion Test:** in each window of 512 samples, fails if
  the window's first value appears 177 times.

Both cutoffs assume at least H = 2 bits of min-entropy per 4-bit sample,
with a false-alarm rate of 2⁻²⁰ per test. A flat buffer (every sample
identical) fails too. `tests/host/test_mic_health.c` checks that noise
passes (also on a 12-bit ADC, and with mains hum on top) and that a dead
microphone, an ADC stuck alternating two values, a DC offset with ±1 LSB
of jitter, and noise that gets stuck all fail.

These tests catch a source that has **broken down**; they are not an
entropy measurement. A predictable but busy signal can pass: the low bits
of mains hum look random to them. A microphone covered with a finger
passes too (checked on a DSi XL): the amplifier's own noise is still
there. How much entropy that noise carries is part of the measurement
below. A made-up tones PIN uses the same tests
(four healthy buffers; none within 10 s, and it is refused).

### What comes out

The 32-byte digest is the mnemonic's entropy: all 32 bytes for 24 words,
the first 16 bytes for 12 words (as SeedSigner's camera tool). The
mnemonic is built by SeedSigner's `mnemonic_generation.generate_mnemonic_from_bytes`.

### Estimate [NEEDS INVESTIGATION]

There is no measured figure yet. Reasoning, to be checked:

- 256 hand-drawn points carry far less than 256 × (x, y, time) bits of
  entropy: strokes are continuous and positions are correlated. Timing at
  1 ms resolution adds some.
- Microphone noise is likely the main contribution: 16 or more buffers of
  64 000+ samples, whose low bits are dominated by analogue noise even in a
  quiet room. How much of it is truly unpredictable on the DSi's
  microphone and ADC has not been measured.
- SHA-256 does not add entropy; it only concentrates what goes in.

Missing work: record raw microphone buffers from several consoles (silent
room, speech, covered microphone) and estimate min-entropy per buffer, e.g.
with NIST SP 800-90B's `ea_non_iid` tool.

## Tests

`tests/host/test_mic_health.c` (above) and the simulator flows, where flat
and stuck buffers must not count. Things an auditor can do:

- Run the tool twice with similar scribbles: the words must differ.
- Check the code above: that every buffer and point goes into the hash,
  and that nothing else (a fixed value, a reused buffer) can replace it.
- For full independence from this code, use dice.
