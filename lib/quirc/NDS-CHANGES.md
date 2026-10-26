# NDS-Signer changes to quirc

quirc (ISC license, Daniel Beer, https://github.com/dlbeer/quirc) is vendored
here. Upstream behaviour is unchanged unless these compile-time options are
set. arm9/Makefile sets all of them for the ROM:

| Option | What it does |
|---|---|
| `QUIRC_FIXED_POINT_GRID` | Grid cell sampling (`fitness_cell`, `read_cell`) maps points with a Q32 integer transform instead of floating point. Out-of-range values fall back to the float/double code. |
| `QUIRC_DIV_ROUND=<fn>` | Rounded 64-bit division for that mapping. The ROM passes the DS hardware divider (`arm9/src/quirc_nds.c`). |
| `QUIRC_LAZY_JIGGLE` | `quirc_end()` skips the perspective fitness search (`jiggle_perspective`). The new `quirc_refine(q, index)` runs it on demand, when a grid does not decode. |
| `QUIRC_STAGE_MARK=<fn>` | Timing hook between the stages of `quirc_end()`, for developer builds only. |

Why: the DSi's ARM946E-S has no FPU. With upstream quirc, the fitness
search (81 × `fitness_all`, ~160,000 `perspective_map` calls in software
floating point) took 1.1–2.2 s of every frame that contained a QR code. With
lazy refinement, a frame is processed in ~0.2 s. See `decode()` in
arm9/src/qr_scanner.c for when the scanner refines.

Check: `make -C tests/host quirc` decodes seeded synthetic camera frames
(scale, rotation, perspective, blur, noise, lighting) with upstream quirc
and with the ROM's configuration. It fails if the ROM build loses any frame
that upstream decodes, or decodes a wrong payload. It runs under ASan and
UBSan, so an integer overflow in the fixed-point code fails the check.

## Fixes found by fuzzing (`tests/fuzz`)

Applied whatever the options; behaviour is otherwise upstream's.

- `quirc_resize()`: on the first resize `q->image` is NULL and was passed
  to `memcpy` with a length of 0 (undefined behaviour, harmless in
  practice). The copy is now skipped when there is nothing to copy.
- `fitness_all()`: the version table entry was addressed before the
  version was range-checked, so a grid measured smaller than 21 cells
  formed `&quirc_version_db[-1]` (undefined behaviour; it was not read).
  Found by `fuzz_image`. The entry is now taken after the check.
- `quirc_extract()`: `index > q->num_grids` let `index == num_grids`
  through; now `>=`, and the grid is looked up after the check. NDS-Signer
  never passes such an index.
