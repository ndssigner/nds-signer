#!/usr/bin/env python3
"""Render a payload as a QR code PNG to use as the melonDS camera image.

melonDS (the macOS build bundled for development) can only load PNG files as
camera input, and it misreads grayscale PNGs, so the image is written as 8-bit
RGB. The image is 640x480, the DSi camera capture resolution.

Examples:
    tools/qr_to_png.py tests/vectors/psbt_base64_singlesig.txt
    tools/qr_to_png.py --text "tb1q..." -o /tmp/qr.png

Only the Python standard library is needed; the QR encoder is Project Nayuki's
qrcodegen (MIT), vendored in tools/third_party.
"""
import argparse
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "third_party"))
from qrcodegen import QrCode  # noqa: E402

WIDTH, HEIGHT = 640, 480
QUIET_ZONE = 4  # modules, as required by the QR spec
DEFAULT_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "emulator", "camera-test.png")


def write_png_rgb(path, width, height, rows):
    """rows: iterables of 8-bit gray values, expanded to RGB."""
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes(v for g in row for v in (g, g, g)) for row in rows)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))


def render(payload, size_ratio):
    qr = QrCode.encode_binary(payload, QrCode.Ecc.LOW)
    modules = qr.get_size() + 2 * QUIET_ZONE
    scale = max(1, int(HEIGHT * size_ratio) // modules)
    side = modules * scale
    x0, y0 = (WIDTH - side) // 2, (HEIGHT - side) // 2

    rows = []
    for y in range(HEIGHT):
        row = bytearray([255] * WIDTH)
        my = (y - y0) // scale - QUIET_ZONE
        if 0 <= y - y0 < side:
            for x in range(x0, x0 + side):
                mx = (x - x0) // scale - QUIET_ZONE
                if qr.get_module(mx, my):
                    row[x] = 0
        rows.append(row)
    return qr, scale, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("file", nargs="?", help="file whose contents are the QR payload")
    src.add_argument("--text", help="payload given on the command line")
    ap.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help="PNG to write (default: emulator/camera-test.png)")
    ap.add_argument("--size", type=float, default=0.9, help="QR height as a fraction of the image (default 0.9)")
    args = ap.parse_args()

    if args.text is not None:
        payload = args.text.encode()
    else:
        with open(args.file, "rb") as f:
            payload = f.read().strip()

    qr, scale, rows = render(payload, args.size)
    write_png_rgb(args.output, WIDTH, HEIGHT, rows)
    print(f"{args.output}: QR version {qr.get_version()}, {qr.get_size()}x{qr.get_size()} modules, "
          f"{scale}px/module, {len(payload)} bytes")


if __name__ == "__main__":
    main()
