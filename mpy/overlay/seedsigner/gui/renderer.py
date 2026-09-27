# NDS-Signer: SeedSigner's Renderer owns a Pillow canvas; here drawing is done
# by the native screens, so this only keeps the API the views/controller use.
from seedsigner.models.singleton import ConfigurableSingleton


class _NoLock:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _NoDisplayDriver:
    """SeedSigner's display driver: settings call disp.invert() (the
    "Invert colors" hardware setting for its LCD). Nothing to do here."""

    def invert(self, enabled=True):
        pass


class Renderer(ConfigurableSingleton):
    canvas_width = 256
    canvas_height = 192
    canvas = None
    draw = None
    disp = _NoDisplayDriver()
    is_screenshot_generator = False
    lock = _NoLock()

    @classmethod
    def configure_instance(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def initialize_display(self):
        pass

    def show_image(self, *args, **kwargs):
        pass

    def display_blank_screen(self):
        from seedsigner.gui.hw import nds
        nds.top_clear()
        nds.bottom_clear()
