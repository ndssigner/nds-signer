# NDS-Signer - Pillow stand-in for ImageOps. The camera entropy view boosts the
# contrast of the final image only for display; NDS-Signer's frames
# (seedsigner.hardware.camera.NdsFrame) are shown natively, unchanged.


def autocontrast(image, *args, **kwargs):
    return image
