# NDS-Signer - its own Tools menu and new seed tools. tools/upy_transform.py
# (UI_OVERRIDES) rebinds upstream's tools_views.ToolsMenuView to the one
# here; the tools themselves (camera and dice entropy, final word, address
# explorer) stay upstream's views.
from gettext import gettext as _

from seedsigner.gui.components import FontAwesomeIconConstants
from seedsigner.gui.screens import RET_CODE__BACK_BUTTON, ButtonListScreen
from seedsigner.gui.screens.screen import ButtonOption
from seedsigner.helpers import mnemonic_generation
from seedsigner.models.seed import Seed
from seedsigner.models.settings_definition import SettingsConstants
from seedsigner.views.view import BackStackView, Destination, View


class ToolsMenuView(View):
    """Upstream's Tools menu with the new seed tools grouped behind one
    button (ToolsNewSeedView)."""

    NEW_SEED = ButtonOption("New seed")
    KEYBOARD = ButtonOption("Calc 12th/24th word", FontAwesomeIconConstants.KEYBOARD)
    ADDRESS_EXPLORER = ButtonOption("Address explorer")
    VERIFY_ADDRESS = ButtonOption("Verify address")

    def run(self):
        from seedsigner.views import tools_views
        button_data = [self.NEW_SEED, self.KEYBOARD, self.ADDRESS_EXPLORER, self.VERIFY_ADDRESS]
        selected_menu_num = self.run_screen(ButtonListScreen, title=_("Tools"),
                                            is_button_text_centered=False, button_data=button_data)
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        choice = button_data[selected_menu_num]
        if choice == self.NEW_SEED:
            return Destination(ToolsNewSeedView)
        if choice == self.KEYBOARD:
            return Destination(tools_views.ToolsCalcFinalWordNumWordsView)
        if choice == self.ADDRESS_EXPLORER:
            return Destination(tools_views.ToolsAddressExplorerSelectSourceView)
        if choice == self.VERIFY_ADDRESS:
            from seedsigner.views.scan_views import ScanAddressView
            return Destination(ScanAddressView)


class ToolsNewSeedView(View):
    """The ways to make a new seed: upstream's camera and dice tools, and
    NDS-Signer's scribble + microphone."""

    CAMERA = ButtonOption("Camera", FontAwesomeIconConstants.CAMERA)
    DICE = ButtonOption("Dice", FontAwesomeIconConstants.DICE)
    SCRIBBLE_MIC = ButtonOption("Scribble + microphone")

    def run(self):
        from seedsigner.views import tools_views
        button_data = [self.CAMERA, self.DICE, self.SCRIBBLE_MIC]
        selected_menu_num = self.run_screen(ButtonListScreen, title=_("New seed"),
                                            is_button_text_centered=False, button_data=button_data)
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        choice = button_data[selected_menu_num]
        if choice == self.CAMERA:
            return Destination(tools_views.ToolsImageEntropyLivePreviewView)
        if choice == self.DICE:
            return Destination(tools_views.ToolsDiceEntropyMnemonicLengthView)
        return Destination(ToolsScribbleMicEntropyView)


class ToolsScribbleMicEntropyView(View):
    """NDS-Signer's own: scribbling on the touch screen while the microphone
    records noise. The same steps as upstream's camera tool
    (tools_views.ToolsImageEntropy*): collect, choose 12 or 24 words, the
    SHA-256 of everything collected becomes the mnemonic's entropy, then
    the words are shown."""

    TWELVE_WORDS = ButtonOption("12 words", return_data=12)
    TWENTYFOUR_WORDS = ButtonOption("24 words", return_data=24)

    def run(self):
        from seedsigner.gui.screens.tools_screens import ToolsScribbleMicEntropyScreen
        from seedsigner.views.seed_views import SeedWordsWarningView
        digest = self.run_screen(ToolsScribbleMicEntropyScreen)
        if digest == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        button_data = [self.TWELVE_WORDS, self.TWENTYFOUR_WORDS]
        selected_menu_num = self.run_screen(ButtonListScreen, title=_("Mnemonic Length"),
                                            button_data=button_data)
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        # like upstream: 12 words use the first 128 bits
        entropy = digest if button_data[selected_menu_num].return_data == 24 else digest[:16]
        mnemonic = mnemonic_generation.generate_mnemonic_from_bytes(entropy)
        digest = entropy = None
        seed = Seed(mnemonic, wordlist_language_code=self.settings.get_value(
            SettingsConstants.SETTING__WORDLIST_LANGUAGE))
        self.controller.storage.set_pending_seed(seed)
        # Cannot return BACK to this View
        return Destination(SeedWordsWarningView, view_args={"seed": None}, clear_history=True)
