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
- at least **16** microphone buffers (4 s) that are **not flat** (not every
  sample identical — this catches a dead microphone, nothing more).

These are activity checks, not entropy measurements: there is no
statistical test of the input.

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

None specific to entropy yet. Things an auditor can do:

- Run the tool twice with similar scribbles: the words must differ.
- Check the code above: that every buffer and point goes into the hash,
  and that nothing else (a fixed value, a reused buffer) can replace it.
- For full independence from this code, use dice.
