# NDS-Signer: no Pillow splash screen or screensaver (yet).
from seedsigner.views.view import View


class OpeningSplashView(View):
    def run(self, **kwargs):
        return None


class ScreensaverScreen:
    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        pass

    def stop(self):
        pass
