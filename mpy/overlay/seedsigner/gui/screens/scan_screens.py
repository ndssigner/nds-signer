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
        nds.gfx_present(nds_ui.TOP)
        nds.top_print(22, -1, _(self.instructions_text or "Scan a QR code"))

    # below the Cancel button
    PROGRESS_Y = 44

    def _progress(self, status_text):
        nds_ui.bottom_note(self.PROGRESS_Y, status_text or _("Scanning..."))

    COUNTDOWN_MS = 3000

    def _intro(self, settings):
        """"Scan preparation" (if enabled in Settings), before the camera
        starts: tips, the camera to use (rear by default) and Start; or
        tones instead of the camera (experimental, nds_tones).
        Returns False for Back, "tones" for tones."""
        from seedsigner.gui import CAMERA__FRONT, CAMERA__REAR, SETTING__NDS_CAMERA
        from seedsigner.gui.components import SeedSignerIconConstants as Icons
        while True:
            front = settings.get_value(SETTING__NDS_CAMERA) == CAMERA__FRONT
            nds_ui.top_blocks(_("Scan"), [
                ("icon", Icons.SCAN), ("space", 2),
                ("text", _(self.instructions_text or "Scan a QR code")), ("space", 8),
                ("label", _("Hold it 15-25 cm away, in good light.")),
                ("label", _("The DSi camera is slow: hold still, a scan can take several "
                            "seconds."))])
            camera = _("Front camera") if front else _("Rear camera")
            choice = nds_ui.ButtonPanel([_("Start scanning"), "%s: %s" % (_("Camera"), camera),
                                         _("Listen to tones (experimental)")]).run()
            if choice == nds_ui.BACK:
                return False
            if choice == 0:
                return True
            if choice == 2:
                return "tones"
            settings.set_value(SETTING__NDS_CAMERA, CAMERA__REAR if front else CAMERA__FRONT)

    def _countdown(self, panel):
        """Preview without decoding for a moment: time to aim, and for the
        sensor's automatic exposure to settle. Returns False on Cancel."""
        nds.camera_decode(False)
        end = nds.ticks_ms() + self.COUNTDOWN_MS
        shown = None
        try:
            while True:
                left = end - nds.ticks_ms()
                if left <= 0:
                    return True
                if (left + 999) // 1000 != shown:
                    shown = (left + 999) // 1000
                    self._progress(_("Starting in {}...").format(shown))
                nds.frame()
                if panel.handle_frame() is not None or nds.keys_down() & nds.KEY_B:
                    return False
                nds.camera_poll()  # preview only
        finally:
            nds.camera_decode(True)

    def _run(self):
        from seedsigner.gui import CAMERA__FRONT, SETTING__NDS_CAMERA, SETTING__NDS_SCAN_INTRO
        from seedsigner.models.decode_qr import DecodeQRStatus
        from seedsigner.models.settings import Settings, SettingsConstants

        settings = Settings.get_instance()
        intro = settings.get_value(SETTING__NDS_SCAN_INTRO) == SettingsConstants.OPTION__ENABLED
        if intro:
            how = self._intro(settings)
            while how == "tones":
                from seedsigner.gui import nds_tones
                chosen = nds_tones.intro()
                if chosen is None:          # Back: the scan preparation again
                    how = self._intro(settings)
                    continue
                return None if nds_tones.listen(self.decoder, chosen[0], chosen[1]) else False
            if not how:
                return RET_CODE__BACK_BUTTON
            self._render()
        panel = nds_ui.ButtonPanel([_("Cancel")], show_back=False)
        panel.draw()
        self._progress("")
        if not nds.camera_start(settings.get_value(SETTING__NDS_CAMERA) == CAMERA__FRONT):
            return RET_CODE__BACK_BUTTON
        if intro and not self._countdown(panel):
            nds.camera_stop()
            return False
        self._progress("")
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
