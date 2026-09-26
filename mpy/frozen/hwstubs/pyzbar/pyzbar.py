# NDS-Signer - `pyzbar` stand-in. SeedSigner decodes camera frames with zbar;
# on the DSi QR codes are decoded natively (quirc, arm9/src/qr_scanner.c) and
# the payload text is fed to DecodeQR.add_data(). Decoding images here would be
# a bug, so it fails loudly.


class ZBarSymbol:
    QRCODE = 64


def decode(image, symbols=None):
    raise NotImplementedError("image decoding is native on NDS-Signer (quirc)")
