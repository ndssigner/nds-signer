# NDS-Signer: the constant classes are copied verbatim from upstream
# gui/components.py at build time (gui/_upstream.py, tools/gen_gui_api.py).
from seedsigner.gui._upstream import (  # noqa: F401
    FontAwesomeIconConstants,
    GUIConstants,
    SeedSignerIconConstants,
)


class BaseComponent:
    pass


# Pillow-based helpers that some upstream views import (e.g. the camera
# entropy tool). NDS-Signer renders natively, so calling them is a bug.
class Fonts:
    @classmethod
    def get_font(cls, *args, **kwargs):
        raise NotImplementedError("Pillow fonts are not available on NDS-Signer")


def load_image(*args, **kwargs):
    raise NotImplementedError("Pillow images are not available on NDS-Signer")


def resize_image_to_fill(*args, **kwargs):
    raise NotImplementedError("Pillow images are not available on NDS-Signer")
