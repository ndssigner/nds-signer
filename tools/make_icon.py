#!/usr/bin/env python3
"""Draws NDS-Signer's 32x32 icon for the DS/DSi menu (banner icon, passed to
ndstool -b): SeedSigner's "sign" icon on a rounded orange tile, written as
the 16-colour (4-bit) BMP ndstool expects; palette entry 0 is transparent.

    make_icon.py <seedsigner src dir> <out.bmp> [<preview.png>]

Runs in the builder image (Pillow pinned), so the output is reproducible.
"""
import pathlib
import struct
import sys

from PIL import Image, ImageDraw, ImageFont

SIZE, SUPER = 32, 8
ORANGE, DARK = (247, 147, 26), (24, 24, 24)
SIGN = ""  # SeedSignerIconConstants.SIGN


def draw(fonts_dir):
    big = SIZE * SUPER
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((SUPER, SUPER, big - SUPER - 1, big - SUPER - 1), radius=7 * SUPER,
                        fill=ORANGE + (255,))
    font = ImageFont.truetype(str(fonts_dir / "seedsigner-icons.otf"), 21 * SUPER)
    d.text((big // 2, big // 2 + SUPER // 2), SIGN, font=font, fill=DARK + (255,), anchor="mm")
    return img.resize((SIZE, SIZE), Image.LANCZOS)


def to_4bit(img):
    """(palette of 16 RGB, rows of indices); transparent pixels -> index 0."""
    alpha = img.getchannel("A")
    solid = Image.new("RGB", img.size, ORANGE)
    solid.paste(img.convert("RGB"), mask=alpha)
    quant = solid.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = quant.getpalette()[:45]
    palette = [(255, 0, 255)] + [tuple(pal[i:i + 3]) for i in range(0, 45, 3)]
    rows = [[0 if alpha.getpixel((x, y)) < 128 else quant.getpixel((x, y)) + 1
             for x in range(SIZE)] for y in range(SIZE)]
    return palette, rows


def write_bmp(path, palette, rows):
    row_bytes = SIZE // 2  # 16, already a multiple of 4
    pixels = b"".join(bytes((r[x] << 4) | r[x + 1] for x in range(0, SIZE, 2))
                      for r in reversed(rows))
    pal = b"".join(bytes((b, g, r, 0)) for r, g, b in palette)
    offset = 14 + 40 + len(pal)
    header = b"BM" + struct.pack("<IHHI", offset + len(pixels), 0, 0, offset)
    info = struct.pack("<IiiHHIIiiII", 40, SIZE, SIZE, 1, 4, 0, row_bytes * SIZE, 2835, 2835,
                       16, 16)
    path.write_bytes(header + info + pal + pixels)


def main():
    fonts_dir = pathlib.Path(sys.argv[1]) / "seedsigner" / "resources" / "fonts"
    img = draw(fonts_dir)
    palette, rows = to_4bit(img)
    write_bmp(pathlib.Path(sys.argv[2]), palette, rows)
    if len(sys.argv) > 3:  # what the menu shows, enlarged
        preview = Image.new("RGB", (SIZE, SIZE))
        preview.putdata([palette[i] if i else (40, 40, 40) for r in rows for i in r])
        preview.resize((SIZE * 8, SIZE * 8), Image.NEAREST).save(sys.argv[3])


if __name__ == "__main__":
    main()
