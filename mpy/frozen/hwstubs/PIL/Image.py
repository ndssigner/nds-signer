# NDS-Signer - Pillow stand-in. SeedSigner renders with Pillow; NDS-Signer
# renders natively, so only type names used in annotations exist here.


class Image:
    pass


def new(*args, **kwargs):
    raise NotImplementedError("Pillow is not available on NDS-Signer")
