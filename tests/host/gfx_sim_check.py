# NDS-Signer: the simulator's font metrics (tests/host/sim/nds.py) must match
# the generated font tables (build/generated/gfx_fonts.c), so screen layouts
# computed on the host are the ones the DSi draws.
import re
import sys

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "sim")
import nds

src = open(sys.argv[2] if len(sys.argv) > 2 else "../../build/generated/gfx_fonts.c").read()
table = src.split("const GfxFont g_gfxFonts")[1]
metrics = [(int(a), int(b)) for a, b in re.findall(r"sizeof\(GfxGlyph\), (\d+), (\d+),", table)]
ok = metrics == nds.FONT_METRICS
print("ok  " if ok else "FAIL", "simulator font metrics match build/generated/gfx_fonts.c (%d fonts)" % len(metrics))
if not ok:
    print("generated:", metrics)
    print("simulator:", nds.FONT_METRICS)
    sys.exit(1)
