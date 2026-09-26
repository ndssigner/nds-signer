# NDS-Signer: SeedSigner renders QR images with `qrcode` + Pillow. On the DSi
# QR codes are drawn natively from the text payload (QRDisplayScreen), so the
# encoders' image helpers are not available.


class QR:
    def qrimage(self, *args, **kwargs):
        raise NotImplementedError("QR images are rendered natively on NDS-Signer")

    qrimage_io = qrimage
