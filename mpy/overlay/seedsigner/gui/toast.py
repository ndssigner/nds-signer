# NDS-Signer: toast overlays are not implemented yet; the classes exist so the
# controller's bookkeeping works.


class BaseToastOverlayManagerThread:
    def __init__(self, *args, **kwargs):
        self._alive = False

    def start(self):
        pass

    def stop(self):
        self._alive = False

    def is_alive(self):
        return self._alive


class RemoveSDCardToastManagerThread(BaseToastOverlayManagerThread):
    pass


class SDCardStateChangeToastManagerThread(BaseToastOverlayManagerThread):
    pass
