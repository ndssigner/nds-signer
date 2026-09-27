# NDS-Signer - native replacements for SeedSigner's gui/screens/tools_screens.py
# (same class names and keyword arguments, see screen.py). Screens without a
# native version yet are generic stand-ins (define_generic_screens).
from gettext import gettext as _

from seedsigner.gui import nds_ui
from seedsigner.gui.screens.screen import ButtonListScreen, define_generic_screens
from seedsigner.models.settings_definition import SettingsConstants, SettingsDefinition


class ToolsAddressExplorerAddressTypeScreen(ButtonListScreen):
    """Like upstream: fingerprint and derivation, or the wallet descriptor."""

    def top_lines(self):
        if not self.fingerprint:
            return ["", _("Wallet descriptor") + ":"] + nds_ui.wrap(str(self.wallet_descriptor_display_name or ""))
        if self.script_type != SettingsConstants.CUSTOM_DERIVATION:
            derivation = SettingsDefinition.get_settings_entry(
                attr_name=SettingsConstants.SETTING__SCRIPT_TYPES
            ).get_selection_option_display_name_by_value(value=self.script_type)
        else:
            derivation = self.custom_derivation_path
        return ["", _("Fingerprint") + ": " + self.fingerprint, "",
                _("Derivation") + ": " + str(derivation or "")]


class ToolsAddressExplorerAddressListScreen(ButtonListScreen):
    """Upstream: one button per address ("index:start...end"), then "Next N".
    The buttons here are abbreviated too, and the top screen lists this
    page's addresses in full, to compare them character by character."""

    def __post_init__(self):
        addresses = self.addresses or []
        last = self.start_index + len(addresses) - 1
        prefix_len = len(str(last)) + 1
        half = (nds_ui.COLS - 4 - prefix_len - 3) // 2
        self.button_data = ["%d:%s...%s" % (self.start_index + i, a[:half], a[-half:])
                            for i, a in enumerate(addresses)]
        self.button_data.append(_("Next {}").format(len(addresses)))
        super().__post_init__()

    def top_lines(self):
        lines = []
        for i, address in enumerate(self.addresses or []):
            label = "%d:" % (self.start_index + i)
            wrapped = nds_ui.wrap(address, nds_ui.COLS - 4)
            lines.append(nds_ui.pad(label, 4) + wrapped[0])
            lines += ["    " + part for part in wrapped[1:]]
        return lines


define_generic_screens(globals(), "tools_screens")
