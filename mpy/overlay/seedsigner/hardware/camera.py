# NDS-Signer: the DSi cameras are driven natively (arm9/src/camera.c,
# qr_scanner.c) through the `nds` module; see gui/screens/scan_screens.py.
from seedsigner.models.singleton import Singleton


class CameraConnectionError(Exception):
    pass


class Camera(Singleton):
    def start_video_stream_mode(self, *args, **kwargs):
        pass

    def stop_video_stream_mode(self):
        pass

    def read_video_stream(self, as_image=False):
        return None
