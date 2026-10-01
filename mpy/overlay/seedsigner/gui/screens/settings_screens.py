# NDS-Signer - native replacements for SeedSigner's gui/screens/settings_screens.py
# (same class names and keyword arguments, see screen.py). Screens without a
# native version yet are generic stand-ins (define_generic_screens).
from gettext import gettext as _

from seedsigner.gui import nds_ui
from seedsigner.gui.hw import nds
from seedsigner.gui.screens.screen import (
    RET_CODE__BACK_BUTTON,
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


# NDS-Signer's donation addresses (also in README.md and docs/es/LEEME.md)
DONATE_ONCHAIN = "bc1pejkndc4ler9an5tgavxtrcz2r0c6uvhet0tzvjp4apqmzch0cv9qlvlrgj"
DONATE_LIGHTNING = "ndssigner@coinos.io"


class DonateScreen(BaseTopNavScreen):
    """NDS-Signer's donation addresses: Bitcoin (on-chain) or Lightning, as a
    QR code and in full on the top screen; a tap on the other button switches.
    And a credit to SeedSigner, which NDS-Signer is built on."""

    QR_PX = 96

    def _method(self):
        panel = getattr(self, "_panel", None)
        return panel.selected if panel is not None else 0

    def top_blocks(self):
        if self._method() == 0:
            # BIP-21 URI in capitals: alphanumeric mode, a smaller QR code
            return [("qr", "bitcoin:" + DONATE_ONCHAIN.upper(), self.QR_PX), ("space", 4),
                    ("address", DONATE_ONCHAIN)]
        return [("qr", "lightning:" + DONATE_LIGHTNING, self.QR_PX), ("space", 8),
                ("value", DONATE_LIGHTNING)]

    def _credit(self):
        t = nds_ui.theme()
        nds_ui.text_centered(nds_ui.BOTTOM, 104, _("NDS-Signer is built on SeedSigner."),
                             nds.FONT_BODY, t["label"])
        nds_ui.text_centered(nds_ui.BOTTOM, 122, _("Support it too: seedsigner.com"),
                             nds.FONT_BODY, t["label"])
        nds.gfx_present(nds_ui.BOTTOM)

    def _switched(self):
        self._render()
        self._credit()

    def _run(self):
        panel = nds_ui.ButtonPanel(["Bitcoin", "Lightning"], show_back=True, tap_selects=True,
                                   on_select=self._switched, redraw=self._render)
        self._panel = panel
        self._render()
        panel.draw()
        self._credit()
        while True:
            nds.frame()
            if panel.handle_frame() == nds_ui.BACK:
                return RET_CODE__BACK_BUTTON


class IOTestScreen(_InfoScreen):
    """Upstream tests SeedSigner's joystick, keys and camera. On the DSi the
    diagnostics of the developer build do that (SELECT: touch test)."""

    def top_blocks(self):
        return [("text", _("The I/O test is for SeedSigner's joystick and keys. "
                           "The DSi's buttons and touch screen need no test."))]


define_generic_screens(globals(), "settings_screens")
