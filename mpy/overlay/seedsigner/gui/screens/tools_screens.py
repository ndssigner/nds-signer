# NDS-Signer - native replacements for SeedSigner's gui/screens/tools_screens.py
# (same class names and keyword arguments, see screen.py). Screens without a
# native version yet are generic stand-ins (define_generic_screens).
from gettext import gettext as _

from seedsigner.gui import nds_ui
from seedsigner.gui.hw import nds
from seedsigner.gui.screens.screen import ButtonListScreen, KeyboardScreen, define_generic_screens
from seedsigner.models.settings_definition import SettingsConstants, SettingsDefinition


class ToolsAddressExplorerAddressTypeScreen(ButtonListScreen):
    """Like upstream: fingerprint and derivation, or the wallet descriptor."""

    def top_blocks(self):
        if not self.fingerprint:
            return [("label", _("Wallet descriptor")),
                    ("text", str(self.wallet_descriptor_display_name or ""))]
        if self.script_type != SettingsConstants.CUSTOM_DERIVATION:
            derivation = SettingsDefinition.get_settings_entry(
                attr_name=SettingsConstants.SETTING__SCRIPT_TYPES
            ).get_selection_option_display_name_by_value(value=self.script_type)
        else:
            derivation = self.custom_derivation_path
        return [("label", _("Fingerprint")), ("value", self.fingerprint), ("space", 8),
                ("label", _("Derivation")), ("value", str(derivation or ""))]


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

    def top_blocks(self):
        """The full addresses of the button page shown below."""
        panel = getattr(self, "_panel", None)
        first = panel.page() * panel.per_page if panel is not None else 0
        blocks = []
        per_line = (nds_ui.GFX_W - 2 * nds_ui.MARGIN) // nds.gfx_text_width("0", nds.FONT_MONO_SMALL)
        for i, address in enumerate((self.addresses or [])[first:first + nds_ui.BUTTONS_PER_PAGE]):
            prefix = "%d:" % (self.start_index + first + i)
            prefix += " " * (4 - len(prefix)) if len(prefix) < 4 else " "
            head = per_line - len(prefix)
            blocks.append(("mono_small", prefix + address[:head]))
            rest = address[head:]
            while rest:  # continuation lines, indented under the address
                blocks.append(("mono_small", " " * len(prefix) + rest[:head]))
                rest = rest[head:]
        return blocks


class ToolsDiceEntropyEntryScreen(KeyboardScreen):
    """Like upstream: keys 1-6, one per roll; returns after all the rolls."""

    KEYS = "123456"
    COLS = 3

    def update_title(self):
        n = min(len(self.user_input) + 1, self.return_after_n_chars)
        self.title = _("Dice Roll {}/{}").format(n, self.return_after_n_chars)
        return True

    def top_lines(self):
        rolls = self.user_input
        groups = " ".join(rolls[i:i + 5] for i in range(0, len(rolls), 5))
        return ["", "%d / %d" % (len(rolls), self.return_after_n_chars), ""] + nds_ui.wrap(groups or " ")


class ToolsCoinFlipEntryScreen(KeyboardScreen):
    """Like upstream: 1 = heads, 0 = tails; returns after all the flips."""

    KEYS = "10"
    COLS = 2

    def update_title(self):
        n = min(len(self.user_input) + 1, self.return_after_n_chars)
        self.title = _("Coin Flip {}/{}").format(n, self.return_after_n_chars)
        return True

    def extra_lines(self):
        return [_("Heads = 1"), _("Tails = 0")]


class ToolsCalcFinalWordFinalizePromptScreen(ButtonListScreen):
    def top_blocks(self):
        return [("text", _("The {mnemonic_length}th word is built from {num_bits} more "
                           "entropy bits plus auto-calculated checksum.").format(
            mnemonic_length=self.mnemonic_length, num_bits=self.num_entropy_bits))]


class ToolsCalcFinalWordScreen(ButtonListScreen):
    """Like upstream: the user's input, the entropy bits kept from it, the
    checksum bits appended, and the resulting final word."""

    def top_lines(self):
        checksum = self.checksum_bits or ""
        if self.selected_final_word:
            selection = self.selected_final_word
            keep = self.selected_final_bits[:11 - len(checksum)]
            discard = self.selected_final_bits[-len(checksum):] if checksum else ""
        else:
            selection = self.selected_final_bits
            keep = self.selected_final_bits
            discard = "_" * len(checksum)
        pad = " " * ((nds_ui.COLS - 11) // 2)
        return ["", _('Your input: "{}"').format(selection), "",
                pad + keep + discard,
                pad + " " * len(keep) + "^" * len(discard), "",
                nds_ui.center(_("Checksum")),
                pad + " " * (11 - len(checksum)) + checksum, "",
                nds_ui.center(_('Final Word: "{}"').format(self.actual_final_word))]


class ToolsCalcFinalWordDoneScreen(ButtonListScreen):
    """Like upstream: the final word and the seed's fingerprint; the title
    depends on the mnemonic length (set in upstream's __post_init__)."""

    def __post_init__(self):
        super().__post_init__()
        self.title = _("12th Word") if self.mnemonic_word_length == 12 else _("24th Word")

    def top_blocks(self):
        from seedsigner.gui.components import GUIConstants as GC
        return [("large", '"%s"' % self.final_word, GC.ACCENT_COLOR), ("space", 8),
                ("label", _("fingerprint")), ("value", self.fingerprint or "")]


define_generic_screens(globals(), "tools_screens")
