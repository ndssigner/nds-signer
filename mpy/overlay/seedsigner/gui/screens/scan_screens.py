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

    # below the Cancel button
    PROGRESS_Y = 44

    def _progress(self, status_text):
        nds_ui.bottom_note(self.PROGRESS_Y, status_text or _("Scanning..."))

    def _run(self):
        from seedsigner.models.decode_qr import DecodeQRStatus

        panel = nds_ui.ButtonPanel([_("Cancel")], show_back=False)
        panel.draw()
        self._progress("")
        if not nds.camera_start():
            return RET_CODE__BACK_BUTTON
        dev = nds_ui.nds_dev
        py_ms = parts = 0
        try:
            while True:
                nds.frame()
                if panel.handle_frame() is not None or nds.keys_down() & nds.KEY_B:
                    return False
                payload = nds.camera_poll()
                if dev is not None:
                    dev.scan_frame(parts, py_ms, nds.camera_stats()[0] % 8 == 1)
                if payload is None:
                    continue
                t0 = nds.ticks_ms()
                status = self.decoder.add_data(payload)
                py_ms += nds.ticks_ms() - t0
                parts += 1
                if status == DecodeQRStatus.COMPLETE:
                    nds_ui.sound("success")
                    return None
                if status == DecodeQRStatus.INVALID:
                    nds_ui.sound("error")
                    return None
                nds_ui.sound("scan")
                percent = self.decoder.get_percent_complete()
                if percent:
                    self._progress("%s %d%%" % (_("Progress:"), percent))
        finally:
            nds.camera_stop()
            if dev is not None:
                dev.record_scan(parts, py_ms)
