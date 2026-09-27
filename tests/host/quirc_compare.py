#!/usr/bin/env python3
"""Compares quirc_scan outputs (unmodified quirc vs the ROM's build) against
the expected payloads of the synthetic frames. Fails if the ROM's build
loses a frame the unmodified quirc decodes, or decodes a wrong payload."""
import pathlib
import sys

images = pathlib.Path(sys.argv[1])


def load(path):
    rows = {}
    for line in pathlib.Path(path).read_text().splitlines():
        name, *codes = line.split()
        rows[name] = codes
    return rows


double, fixed = load(sys.argv[2]), load(sys.argv[3])
counts = {"double": 0, "fixed": 0}
differ = []
for name in sorted(double):
    expected = (images / name.replace(".pgm", ".txt")).read_text().encode().hex()
    for label, rows in (("double", double), ("fixed", fixed)):
        if "ok:" + expected in rows[name]:
            counts[label] += 1
    if double[name] != fixed[name]:
        differ.append(name)
        if "ok:" + expected in double[name] and "ok:" + expected not in fixed[name]:
            counts.setdefault("lost", []).append(name)
        for codes in (double[name], fixed[name]):
            if any(c.startswith("ok:") and c != "ok:" + expected for c in codes):
                counts.setdefault("wrong", []).append(name)
n = len(double)
print("%s quirc ROM build: %d/%d frames decoded (unmodified quirc: %d/%d), %d differ%s" % (
    "ok  " if not counts.get("lost") and not counts.get("wrong") else "FAIL",
    counts["fixed"], n, counts["double"], n, len(differ),
    (" " + " ".join(differ[:10])) if differ else ""))
if counts.get("lost") or counts.get("wrong"):
    print("lost:", counts.get("lost"), "wrong payload:", counts.get("wrong"))
    sys.exit(1)
