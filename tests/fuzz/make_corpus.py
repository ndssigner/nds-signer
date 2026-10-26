"""Seed corpora for tests/fuzz from the payloads in tests/vectors: each as raw
bytes (fuzz_qr_type), as a QR code's cell grid (fuzz_decode) and as a small
grayscale image of it (fuzz_image). Needs the `qrcode` package.
Usage: make_corpus.py <tests/vectors> <out dir>"""
import os
import sys

import qrcode


def payloads(vectors):
    for name in sorted(os.listdir(vectors)):
        if not name.endswith(".txt"):
            continue
        with open(os.path.join(vectors, name), "rb") as f:
            for item in f.read().split():
                if 0 < len(item) <= 1200:
                    yield item
    # CompactSeedQR: the 16 or 32 entropy bytes themselves, in byte mode
    yield bytes(range(16))
    yield bytes(range(255, 223, -1))


def matrix(data):
    qr = qrcode.QRCode(border=0, error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.version, qr.get_matrix()


def main():
    vectors, out = sys.argv[1], sys.argv[2]
    for h in ("fuzz_qr_type", "fuzz_decode", "fuzz_image"):
        os.makedirs(os.path.join(out, h), exist_ok=True)
    seen = set()
    for n, data in enumerate(payloads(vectors)):
        if data in seen:
            continue
        seen.add(data)
        with open(os.path.join(out, "fuzz_qr_type", "v%03d" % n), "wb") as f:
            f.write(data)
        version, m = matrix(data)
        size = len(m)
        bits = bytearray((size * size + 7) // 8)
        for y, row in enumerate(m):
            for x, black in enumerate(row):
                if black:
                    i = y * size + x
                    bits[i >> 3] |= 1 << (i & 7)
        with open(os.path.join(out, "fuzz_decode", "v%03d" % n), "wb") as f:
            f.write(bytes([version - 1]) + bits)
        scale = 2 if size * 2 + 16 <= 263 else 1
        side = size * scale + 16
        if side > 263:
            continue
        img = bytearray([255]) * (side * side)
        for y in range(side):
            for x in range(side):
                cx, cy = (x - 8) // scale, (y - 8) // scale
                if 0 <= cx < size and 0 <= cy < size and m[cy][cx]:
                    img[y * side + x] = 0
        with open(os.path.join(out, "fuzz_image", "v%03d" % n), "wb") as f:
            f.write(bytes([side - 8, side - 8]) + img)
    print("corpus:", len(seen), "payloads")


main()
