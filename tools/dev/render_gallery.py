#!/usr/bin/env python3
"""Renders the simulator's screen snapshots (tests/host/menu_crawl.py
--gallery=DIR, JSON display lists) as PNG images of both DS screens, with
the same fonts and sizes as the ROM (tools/ttf_to_ndsfont.py), plus an HTML
index. Needs Pillow and qrcode (the tests' CPython venv).

    render_gallery.py <snapshot dir> <out dir>

Approximations: text in the old console font is drawn in a small fixed-width
font on a dark blue box (to spot what is not graphical yet); the camera
viewfinder is a gray placeholder; QR codes are re-encoded with `qrcode`.
"""
import html
import json
import pathlib
import sys

import qrcode
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[2]
FONTS_DIR = ROOT / "third_party/seedsigner/src/seedsigner/resources/fonts"
sys.path.insert(0, str(ROOT / "tools"))
from ttf_to_ndsfont import FONTS  # noqa: E402  same fonts, same sizes

W, H, SCALE = 256, 192, 2
_fonts = [ImageFont.truetype(str(FONTS_DIR / f), size) for _id, f, size, _cs in FONTS]
_console = ImageFont.truetype(str(FONTS_DIR / "Inconsolata-Regular.ttf"), 9)


def rgb(value):
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def draw_qr(img, data, zone=0, zx=0, zy=0, background=255):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, border=0)
    qr.add_data(bytes.fromhex(data[4:]) if data.startswith("hex:") else data)
    qr.make(fit=True)
    m = qr.get_matrix()
    n = len(m)
    d = ImageDraw.Draw(img)
    if zone:
        scale = 24
        x0 = (W - zone * scale) // 2 - zx * zone * scale
        y0 = (H - zone * scale) // 2 - zy * zone * scale
    else:
        scale = H // (n + 2)
        x0, y0 = (W - n * scale) // 2, (H - n * scale) // 2
        d.rectangle((0, 0, W, H), fill=(background,) * 3)
    for y in range(n):
        for x in range(n):
            inzone = not zone or (x // zone == zx and y // zone == zy)
            dark = m[y][x]
            color = (0, 0, 0) if dark else (255, 255, 255)
            if not inzone:
                color = (32, 32, 32) if dark else (112, 112, 112)
            d.rectangle((x0 + x * scale, y0 + y * scale, x0 + (x + 1) * scale - 1,
                         y0 + (y + 1) * scale - 1), fill=color)


def render(ops):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for op in ops:
        kind = op[0]
        if kind == "clear":
            d.rectangle((0, 0, W, H), fill=rgb(op[1]))
        elif kind == "rect":
            _, x, y, w, h, color, radius = op
            d.rounded_rectangle((x, y, x + w - 1, y + h - 1), radius=radius, fill=rgb(color))
        elif kind == "frame":
            _, x, y, w, h, color, radius, thick = op
            d.rounded_rectangle((x, y, x + w - 1, y + h - 1), radius=radius, outline=rgb(color),
                                width=thick)
        elif kind == "text":
            _, x, y, text, font, color, max_w = op
            f = _fonts[font]
            ascent = f.getmetrics()[0]
            if max_w:
                while text and f.getlength(text) > max_w:
                    text = text[:-1]
            d.text((x, y + ascent), text, font=f, fill=rgb(color), anchor="ls")
        elif kind == "console":
            _, row, col, text = op
            if col < 0:
                col = max(0, (32 - len(text)) // 2)
            if text.strip():
                box = (col * 8, row * 8, col * 8 + len(text) * 8, row * 8 + 8)
                d.rectangle(box, fill=(20, 30, 80))
                d.text((col * 8, row * 8 - 1), text, font=_console, fill=(220, 220, 255))
        elif kind == "camera":
            d.rectangle((0, 0, W, H), fill=(90, 90, 90))
            d.text((W // 2, H // 2), "camera", font=_fonts[0], fill=(200, 200, 200), anchor="mm")
        elif kind == "qr":
            _, text, border, background = op
            draw_qr(img, text, background=background)
            d = ImageDraw.Draw(img)
        elif kind == "transcribe":
            _, data, zone, zx, zy = op
            draw_qr(img, data, zone, zx, zy)
            d = ImageDraw.Draw(img)
    return img


def main():
    src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    items, per_view = [], {}
    for path in sorted(src.glob("*.json")):
        view = path.stem.rsplit("_", 1)[1]
        per_view[view] = per_view.get(view, 0) + 1
        if per_view[view] > 2:  # e.g. the 69 settings entries: 2 are enough
            continue
        snap = json.loads(path.read_text())
        both = Image.new("RGB", (W, 2 * H + 6), (60, 60, 60))
        both.paste(render(snap["top"]), (0, 0))
        both.paste(render(snap["bottom"]), (0, H + 6))
        both = both.resize((both.width * SCALE, both.height * SCALE), Image.NEAREST)
        both.save(out / (path.stem + ".png"))
        items.append(path.stem)
    cards = "\n".join(
        '<figure><img src="%s.png" alt="%s"><figcaption>%s</figcaption></figure>'
        % (name, html.escape(name), html.escape(name.rsplit("_", 1)[1])) for name in items)
    (out / "index.html").write_text(
        "<!doctype html><meta charset=utf-8><title>NDS-Signer screens</title>"
        "<style>body{background:#222;color:#eee;font-family:sans-serif}"
        "figure{display:inline-block;margin:8px;width:260px}img{width:256px}"
        "figcaption{font-size:12px}</style>" + cards)
    print("%d screens -> %s" % (len(items), out))


if __name__ == "__main__":
    main()
