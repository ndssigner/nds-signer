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

    def top_blocks(self):
        return [("headline", _(self.display_name or "")), ("space", 6),
                ("label", _(self.help_text) if self.help_text else "")]


class SettingsQRConfirmationScreen(ButtonListScreen):
    def top_blocks(self):
        # config_name is user-supplied (from the SettingsQR): not translated
        return [("value", '"%s"' % self.config_name if self.config_name else ""), ("space", 8),
                ("text", _(self.status_message or ""))]


class VersionScreen(_InfoScreen):
    def top_blocks(self):
        from seedsigner.gui.components import SeedSignerIconConstants as Icons
        return [("icon", Icons.BITCOIN_ALT), ("large", "NDS-Signer"),
                ("value", self.version_name or ""), ("space", 10),
                ("label", _("Based on") if self.version_fork else ""),
                ("text", self.version_fork or ""), ("label", self.short_commit_hash or "")]


class DonateScreen(_InfoScreen):
    """Upstream's text for now. TODO (before publishing): NDS-Signer's own
    donation details, keeping a credit to SeedSigner."""

    def top_blocks(self):
        text = _("SeedSigner is 100%% free & open source, funded solely by the Bitcoin "
                 "community.\n\nDonate onchain or LN at:").replace("%%", "%")
        return [("text", text), ("space", 6), ("large", "seedsigner.com")]


class IOTestScreen(_InfoScreen):
    """Upstream tests SeedSigner's joystick, keys and camera. On the DSi the
    diagnostics of the developer build do that (SELECT: touch test)."""

    def top_blocks(self):
        return [("text", _("The I/O test is for SeedSigner's joystick and keys. "
                           "The DSi's buttons and touch screen need no test."))]


define_generic_screens(globals(), "settings_screens")
