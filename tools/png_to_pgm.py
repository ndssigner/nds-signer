#!/usr/bin/env python3
"""Minimal PNG (8-bit gray/RGB/RGBA, non-interlaced) to binary PGM converter,
standard library only. Used to feed emulator screenshots to tests/host/qrdecode.
    tools/png_to_pgm.py shot.png > shot.pgm
"""
import struct
import sys
import zlib


def read_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, idat, info = 8, b"", None
    while pos < len(data):
        length, tag = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            info = struct.unpack(">IIBBBBB", body)
        elif tag == b"IDAT":
            idat += body
        pos += 12 + length
    width, height, depth, ctype, _c, _f, interlace = info
    assert depth == 8 and interlace == 0, "unsupported PNG"
    bpp = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = width * bpp
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(height):
        ftype = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if ftype == 1:
                line[x] = (line[x] + a) & 255
            elif ftype == 2:
                line[x] = (line[x] + b) & 255
            elif ftype == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[x] = (line[x] + pred) & 255
        rows.append(line)
        prev = line
    gray = bytearray()
    for line in rows:
        for x in range(width):
            px = line[x * bpp:x * bpp + bpp]
            gray.append(px[0] if bpp <= 2 else (px[0] * 299 + px[1] * 587 + px[2] * 114) // 1000)
    return width, height, gray


w, h, gray = read_png(sys.argv[1])
sys.stdout.buffer.write(b"P5 %d %d 255\n" % (w, h) + bytes(gray))
