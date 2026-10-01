# NDS-Signer: the DSi cameras are driven natively (arm9/src/camera.c,
# qr_scanner.c) through the `nds` module; see gui/screens/scan_screens.py.
# For the camera entropy tool, frames are NdsFrame objects instead of Pillow
# images: upstream's views only call tobytes() on them.
from seedsigner.models.singleton import Singleton


class CameraConnectionError(Exception):
    pass


class NdsFrame:
    """A camera frame as entropy: `data` is the raw frame (YUV422 640x480),
    or for the 50 live preview frames its SHA-256 digest (50 raw frames do
    not fit in memory; upstream hashes each frame's bytes into a chain, so
    the digest carries the frame's entropy)."""

    def __init__(self, data):
        self.data = data

    def tobytes(self):
        return bytes(self.data)


def use_front_camera():
    from seedsigner.gui import CAMERA__FRONT, SETTING__NDS_CAMERA
    from seedsigner.models.settings import Settings
    return Settings.get_instance().get_value(SETTING__NDS_CAMERA) == CAMERA__FRONT


class Camera(Singleton):
    def start_video_stream_mode(self, *args, **kwargs):
        pass

    def stop_video_stream_mode(self):
        pass

    def read_video_stream(self, as_image=False):
        return None

    # The camera entropy tool's final image (ToolsImageEntropyFinalImageView)
    SETTLE_MS = 1500  # a camera just switched on: let its auto exposure settle

    def start_single_frame_mode(self, *args, **kwargs):
        pass

    def capture_frame(self):
        """A full-resolution frame (640x480). The live preview screen leaves
        the camera running for it; otherwise it is started (and given time
        to adjust to the light)."""
        from seedsigner.gui.hw import nds
        settle = 0
        if not nds.camera_running():
            if not nds.camera_start(use_front_camera()):
                raise CameraConnectionError("camera")
            settle = self.SETTLE_MS
        nds.camera_decode(False)
        buf = bytearray(nds.CAMERA_FRAME_BYTES)
        start = nds.ticks_ms()
        try:
            while True:
                nds.frame()
                nds.camera_poll()
                if nds.camera_grab(buf) == 1 and nds.ticks_ms() - start >= settle:
                    return NdsFrame(buf)
        finally:
            nds.camera_stop()

    def stop_single_frame_mode(self):
        pass
