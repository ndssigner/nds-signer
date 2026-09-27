# NDS-Signer - native replacements for SeedSigner's gui/screens/settings_screens.py
# (same class names and keyword arguments, see screen.py). Screens without a
# native version yet are generic stand-ins (define_generic_screens).
from gettext import gettext as _

from seedsigner.gui import nds_ui
from seedsigner.gui.screens.screen import (
    BaseTopNavScreen,
    ButtonListScreen,
    define_generic_screens,
)


class _InfoScreen(BaseTopNavScreen):
    """Text on the top screen; Back (or B) returns."""

    def _run(self):
        return self._back_or(nds_ui.ButtonPanel([], show_back=True, redraw=self._render).run())


class SettingsEntryUpdateSelectionScreen(ButtonListScreen):
    """Like upstream: the setting's name and help text; its options with the
    current one(s) checked."""

    def top_lines(self):
        lines = [""] + [nds_ui.center(l) for l in nds_ui.wrap(_(self.display_name or ""))]
        if self.help_text:
            lines += [""] + nds_ui.wrap(_(self.help_text))
        return lines


class SettingsQRConfirmationScreen(ButtonListScreen):
    def top_lines(self):
        lines = [""]
        if self.config_name:
            # user-supplied string (from the SettingsQR): not translated
            lines += [nds_ui.center(l) for l in nds_ui.wrap('"%s"' % self.config_name)] + [""]
        return lines + [nds_ui.center(l) for l in nds_ui.wrap(_(self.status_message or ""))]


class VersionScreen(_InfoScreen):
    def top_lines(self):
        lines = ["", nds_ui.center("NDS-Signer")] + [
            nds_ui.center(l) for l in nds_ui.wrap(self.version_name or "")]
        if self.version_fork:
            lines += ["", nds_ui.center(_("Based on")), nds_ui.center(self.version_fork)]
        if self.short_commit_hash:
            lines.append(nds_ui.center(self.short_commit_hash))
        return lines


class DonateScreen(_InfoScreen):
    """Upstream's text for now. TODO (before publishing): NDS-Signer's own
    donation details, keeping a credit to SeedSigner."""

    def top_lines(self):
        text = _("SeedSigner is 100%% free & open source, funded solely by the Bitcoin "
                 "community.\n\nDonate onchain or LN at:").replace("%%", "%")
        return [""] + nds_ui.wrap(text) + ["", nds_ui.center("seedsigner.com")]


class IOTestScreen(_InfoScreen):
    """Upstream tests SeedSigner's joystick, keys and camera. On the DSi the
    diagnostics of the developer build do that (SELECT: touch test)."""

    def top_lines(self):
        return [""] + nds_ui.wrap(_("The I/O test is for SeedSigner's joystick and keys. "
                                    "The DSi's buttons and touch screen need no test."))


define_generic_screens(globals(), "settings_screens")
