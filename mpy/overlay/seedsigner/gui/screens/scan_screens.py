# NDS-Signer - native ScanScreen: live preview and QR decoding run natively
# (quirc); decoded payloads are fed to SeedSigner's DecodeQR exactly as its
# ScanScreen does with frames decoded by zbar (DecodeQR.add_data).
from gettext import gettext as _

from seedsigner.gui.hw import nds
from seedsigner.gui import nds_ui
from seedsigner.gui.screens.screen import BaseScreen, RET_CODE__BACK_BUTTON


class ScanScreen(BaseScreen):
    def _render(self):
        nds.top_clear()
        nds.top_print(22, -1, _(self.instructions_text or "Scan a QR code"))

    def _progress(self, status_text):
        nds.bottom_print(0, -1, _("Scanning..."))
        nds.bottom_print(2, 1, nds_ui.pad(status_text, nds_ui.COLS - 2))

    def _run(self):
        from seedsigner.models.decode_qr import DecodeQRStatus

        panel = nds_ui.ButtonPanel([_("Cancel")], show_back=False)
        panel.draw()
        self._progress("")
        if not nds.camera_start():
            return RET_CODE__BACK_BUTTON
        try:
            while True:
                nds.frame()
                if panel.handle_frame() is not None or nds.keys_down() & nds.KEY_B:
                    return False
                payload = nds.camera_poll()
                if payload is None:
                    continue
                status = self.decoder.add_data(payload)
                if status in (DecodeQRStatus.COMPLETE, DecodeQRStatus.INVALID):
                    return None
                percent = self.decoder.get_percent_complete()
                if percent:
                    self._progress("%s %d%%" % (_("Progress:"), percent))
        finally:
            nds.camera_stop()
