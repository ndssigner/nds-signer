# NDS-Signer - its own Home menu: upstream's, plus Donate at the end (a
# donation is not a setting). tools/upy_transform.py (UI_OVERRIDES) rebinds
# upstream's view.MainMenuView to the one here.
from gettext import gettext as _

from seedsigner.gui.components import SeedSignerIconConstants
from seedsigner.gui.screens.screen import RET_CODE__POWER_BUTTON, ButtonOption
from seedsigner.views.view import BackStackView, Destination, PowerOptionsView, View


class MainMenuView(View):
    SCAN = ButtonOption("Scan", SeedSignerIconConstants.SCAN)
    SEEDS = ButtonOption("Seeds", SeedSignerIconConstants.SEEDS)
    TOOLS = ButtonOption("Tools", SeedSignerIconConstants.TOOLS)
    SETTINGS = ButtonOption("Settings", SeedSignerIconConstants.SETTINGS)
    DONATE = ButtonOption("Donate")

    def run(self):
        from seedsigner.gui.screens.screen import MainMenuScreen
        button_data = [self.SCAN, self.SEEDS, self.TOOLS, self.SETTINGS, self.DONATE]
        selected_menu_num = self.run_screen(MainMenuScreen, title=_("Home"),
                                            button_data=button_data)
        if selected_menu_num == RET_CODE__POWER_BUTTON:
            return Destination(PowerOptionsView)
        choice = button_data[selected_menu_num]
        if choice == self.SCAN:
            from seedsigner.views.scan_views import ScanView
            return Destination(ScanView)
        if choice == self.SEEDS:
            from seedsigner.views.seed_views import SeedsMenuView
            return Destination(SeedsMenuView)
        if choice == self.TOOLS:
            from seedsigner.views.tools_views import ToolsMenuView
            return Destination(ToolsMenuView)
        if choice == self.SETTINGS:
            from seedsigner.views.settings_views import SettingsMenuView
            return Destination(SettingsMenuView)
        return Destination(DonateView)


class DonateView(View):
    """NDS-Signer's donation addresses (settings_screens.DonateScreen); Back
    returns to Home."""

    def run(self):
        from seedsigner.gui.screens.settings_screens import DonateScreen
        self.run_screen(DonateScreen)
        return Destination(BackStackView)
