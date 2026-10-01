#!/usr/bin/env python3
"""Every character drawn by the flow tests (their display-list snapshots,
flow_check.py --gallery=DIR) must exist in the font it is drawn with
(build/generated/gfx_fonts.c); a missing glyph shows as "?" on the DSi.

    glyph_check.py <snapshot dir> <gfx_fonts.c>
"""
import json
import pathlib
import re
import sys

snaps, fonts_c = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]).read_text()
# glyph tables in the order of g_gfxFonts (= font ids)
tables = re.findall(r"static const GfxGlyph s_(\w+)_glyphs\[\d+\] = \{(.*?)\};", fonts_c, re.S)
order = re.findall(r"\{s_(\w+)_glyphs, sizeof", fonts_c.split("const GfxFont g_gfxFonts")[1])
points = {name: {int(cp, 16) for cp in re.findall(r"\{0x([0-9a-f]+),", body)} for name, body in tables}
by_id = [points[name] for name in order]

missing = {}
count = 0
for path in sorted(snaps.glob("*.json")):
    snap = json.loads(path.read_text())
    for ops in (snap["top"], snap["bottom"]):
        for op in ops:
            if op[0] != "text":
                continue
            text, font = op[3], op[4]
            count += len(text)
            for ch in text:
                if ord(ch) not in by_id[font]:
                    missing.setdefault((order[font], ch), path.stem)
if missing:
    for (font, ch), where in sorted(missing.items()):
        print("FAIL glyph U+%04X %r not in font %s (%s)" % (ord(ch), ch, font, where))
    sys.exit(1)
print("ok   glyphs: %d characters drawn by the flows, all in their fonts" % count)
