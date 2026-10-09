# NDS-Signer - its own Backup Seed menu: upstream's, plus Export as tones
# (experimental, github.com/ndssigner/ur-tones). tools/upy_transform.py
# (UI_OVERRIDES) rebinds upstream's seed_views.SeedBackupView to the one here.
from gettext import gettext as _

from seedsigner.gui.screens.screen import RET_CODE__BACK_BUTTON, ButtonListScreen, ButtonOption
from seedsigner.views.view import BackStackView, Destination, View


class SeedBackupView(View):
    VIEW_WORDS = ButtonOption("View seed words")
    EXPORT_SEEDQR = ButtonOption("Export as SeedQR")
    EXPORT_TONES = ButtonOption("Export as tones (experimental)")

    def __init__(self, seed):
        super().__init__()
        self.seed = seed

    def run(self):
        from seedsigner.views import seed_views
        button_data = [self.VIEW_WORDS]
        if self.seed.seedqr_supported:
            button_data.append(self.EXPORT_SEEDQR)
        button_data.append(self.EXPORT_TONES)
        selected_menu_num = self.run_screen(ButtonListScreen, title=_("Backup Seed"),
                                            button_data=button_data, is_bottom_list=True)
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        choice = button_data[selected_menu_num]
        if choice == self.VIEW_WORDS:
            return Destination(seed_views.SeedWordsWarningView, view_args={"seed": self.seed})
        if choice == self.EXPORT_SEEDQR:
            return Destination(seed_views.SeedTranscribeSeedQRFormatView, view_args={"seed": self.seed})
        return Destination(SeedTonesExportView, view_args={"seed": self.seed})


class SeedTonesExportView(View):
    """The seed's words (no passphrase) as tones, with an optional PIN
    (seedsigner.gui.nds_tones.send_seed); back to the Backup menu after."""

    def __init__(self, seed):
        super().__init__()
        self.seed = seed

    def run(self):
        from embit import bip32, bip39
        from binascii import hexlify
        from seedsigner.gui import nds_tones
        mnemonic = " ".join(self.seed.mnemonic_list)
        entropy = bip39.mnemonic_to_bytes(mnemonic)
        # the fingerprint without a passphrase, as the receiver will show it
        root = bip32.HDKey.from_seed(bip39.mnemonic_to_seed(mnemonic))
        nds_tones.send_seed(entropy, hexlify(root.my_fingerprint).decode())
        return Destination(BackStackView)
