#!/usr/bin/env python3
"""Synthetic camera-like frames (640x480, 8-bit PGM) of the QR codes
NDS-Signer scans: UR parts at SeedSigner's three densities, a base64 PSBT,
SeedQR, xpub. Random but seeded: scale, rotation, perspective, blur, noise,
contrast and uneven lighting. Used to compare quirc builds (make quirc).

    quirc_images.py <vectors dir> <out dir> [count] [seed]
"""
import pathlib
import random
import sys
from binascii import a2b_base64

import qrcode
from PIL import Image, ImageChops, ImageFilter

vectors, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
count = int(sys.argv[3]) if len(sys.argv) > 3 else 300
rng = random.Random(int(sys.argv[4]) if len(sys.argv) > 4 else 1)
out.mkdir(parents=True, exist_ok=True)

payloads = []
for name in ("psbt_base64_10in.ur.txt", "psbt_base64_singlesig.ur.txt",
             "psbt_base64_singlesig.xpub_ur.txt"):
    payloads += (vectors / name).read_text().split()[:8]
payloads.append((vectors / "psbt_base64_singlesig.txt").read_text().strip())
payloads.append((vectors / "psbt_base64_singlesig.seedqr.txt").read_text().strip())
try:  # UR parts at low and high density too, if SeedSigner's encoder is importable
    from seedsigner.helpers.ur2.ur import UR
    from seedsigner.helpers.ur2.ur_encoder import UREncoder
    from urtypes.crypto import PSBT as UR_PSBT
    psbt = a2b_base64((vectors / "psbt_base64_10in.txt").read_text().strip())
    for fragment in (10, 120):
        enc = UREncoder(ur=UR("crypto-psbt", UR_PSBT(psbt).to_cbor()), max_fragment_len=fragment)
        payloads += [enc.next_part().upper() for _ in range(6)]
except ImportError:
    pass


def frame(text):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, border=rng.randint(1, 4))
    qr.add_data(text)
    qr.make(fit=True)
    modules = qr.modules_count + 2 * qr.border
    box = rng.randint(max(2, 160 // modules), max(3, 470 // modules))
    dark, light = rng.randint(10, 100), rng.randint(140, 250)
    qr.box_size = box
    img = qr.make_image().get_image().convert("L")
    img = img.point(lambda v: light if v else dark)
    img = img.rotate(rng.uniform(-35, 35), expand=True, fillcolor=light, resample=Image.BILINEAR)

    canvas = Image.new("L", (640, 480), rng.randint(60, 200))
    w, h = img.size
    if w > 640 or h > 480:
        img = img.resize((min(w, 620), min(h, 460)), Image.BILINEAR)
        w, h = img.size
    canvas.paste(img, (rng.randint(0, 640 - w), rng.randint(0, 480 - h)))

    # perspective: move the corners by up to 7% of the frame
    j = lambda: rng.uniform(-0.07, 0.07)
    quad = (640 * j(), 480 * j(), 640 * j(), 480 * (1 + j()), 640 * (1 + j()), 480 * (1 + j()),
            640 * (1 + j()), 480 * j())
    canvas = canvas.transform((640, 480), Image.QUAD, quad, resample=Image.BILINEAR, fillcolor=128)
    canvas = canvas.filter(ImageFilter.GaussianBlur(rng.uniform(0, 1.6)))

    # uneven lighting and sensor noise (PIL ops: no per-pixel Python)
    strength = rng.randint(0, 90)
    ramp = Image.linear_gradient("L").rotate(rng.uniform(0, 360)).resize((640, 480))
    ramp = ramp.point(lambda v: v * strength // 255)
    canvas = ImageChops.subtract(canvas, ramp, offset=-strength // 2)
    sigma = rng.uniform(0, 18)
    if sigma > 1:
        noise = Image.effect_noise((640, 480), sigma)  # centred on 128
        canvas = ImageChops.add(canvas, noise, offset=-128)
    return canvas


for i in range(count):
    text = payloads[i % len(payloads)]
    img = frame(text)
    path = out / ("%04d.pgm" % i)
    with open(path, "wb") as f:
        f.write(b"P5 640 480 255\n" + img.tobytes())
    (out / ("%04d.txt" % i)).write_text(text)
