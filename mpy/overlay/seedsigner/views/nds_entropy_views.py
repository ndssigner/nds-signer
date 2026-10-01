# NDS-Signer - its own way to make a new seed: scribbling on the touch screen
# while the microphone records noise. The same steps as upstream's camera
# tool (tools_views.ToolsImageEntropy*): collect, choose 12 or 24 words, the
# SHA-256 of everything collected becomes the mnemonic's entropy, then the
# words are shown. Added to Tools by tools/upy_transform.py (SOURCE_PATCHES).
from gettext import gettext as _

from seedsigner.gui.screens import RET_CODE__BACK_BUTTON, ButtonListScreen
from seedsigner.gui.screens.screen import ButtonOption
from seedsigner.helpers import mnemonic_generation
from seedsigner.models.seed import Seed
from seedsigner.models.settings_definition import SettingsConstants
from seedsigner.views.seed_views import SeedWordsWarningView
from seedsigner.views.view import BackStackView, Destination, View

SCRIBBLE_MIC = ButtonOption("New seed (scribble + mic)")


class ToolsScribbleMicEntropyView(View):
    TWELVE_WORDS = ButtonOption("12 words", return_data=12)
    TWENTYFOUR_WORDS = ButtonOption("24 words", return_data=24)

    def run(self):
        from seedsigner.gui.screens.tools_screens import ToolsScribbleMicEntropyScreen
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
