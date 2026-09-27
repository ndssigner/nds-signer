# NDS-Signer - native replacements for SeedSigner's gui/screens/seed_screens.py
# (same class names and keyword arguments, see screen.py). Screens without a
# native version yet are generic stand-ins (define_generic_screens).
from gettext import gettext as _

from seedsigner.gui import nds_keyboard, nds_ui
from seedsigner.gui.hw import nds
from seedsigner.gui.screens.screen import (
    RET_CODE__BACK_BUTTON,
    BaseTopNavScreen,
    ButtonListScreen,
    LargeIconStatusScreen,
    define_generic_screens,
)

KEYBOARD_ROW = 10
CANDIDATE_ROWS = (3, 6)      # two rows of candidate word buttons
CANDIDATE_COLS = (1, 11, 21)
CANDIDATE_WIDTH = 10
MAX_CANDIDATES = len(CANDIDATE_ROWS) * len(CANDIDATE_COLS)


class SeedMnemonicEntryScreen(BaseTopNavScreen):
    """One BIP-39 word. Upstream returns the selected word, or
    RET_CODE__BACK_BUTTON. Only letters that continue a valid word are
    enabled; matching words appear as buttons once there are few enough."""

    def __post_init__(self):
        super().__post_init__()
        letters = self.initial_letters or []
        # Upstream passes ["a"] (the joystick cursor start) when there is no
        # word yet; a real previous word (re-editing) is at least 3 letters.
        self.prefix = "".join(letters) if len(letters) > 1 else ""
        self.keys = nds_keyboard.qwerty_keys(KEYBOARD_ROW)
        self.del_key = nds_keyboard.Key("Del", 0, 25, width=6, action="del")
        self.back_key = nds_keyboard.Key("< Back", 20, 1, width=10, action="back")

    def _candidates(self):
        return [w for w in self.wordlist if w.startswith(self.prefix)]

    def _render(self):
        pass  # drawn by _draw() on every change

    def _draw(self):
        candidates = self._candidates()
        enabled = set(w[len(self.prefix)] for w in candidates if len(w) > len(self.prefix))

        lines = ["%s %s_" % (_("Word:"), self.prefix), ""]
        if len(candidates) <= 24:
            row = ""
            for word in candidates:
                if len(row) + len(word) + 1 > nds_ui.COLS:
                    lines.append(row)
                    row = ""
                row += word + " "
            lines.append(row)
        else:
            lines.append("%d %s" % (len(candidates), _("matching words")))
        nds_ui.top_page(_(self.title), lines)

        nds.bottom_clear()
        nds_keyboard.draw_key(self.del_key, enabled=bool(self.prefix))
        self.candidate_keys = []
        if len(candidates) <= MAX_CANDIDATES:
            i = 0
            for row in CANDIDATE_ROWS:
                for col in CANDIDATE_COLS:
                    if i < len(candidates):
                        key = nds_keyboard.Key(candidates[i], row, col, CANDIDATE_WIDTH,
                                               action=("word", candidates[i]))
                        nds_keyboard.draw_key(key, highlighted=len(candidates) == 1)
                        self.candidate_keys.append(key)
                    i += 1
        for key in self.keys:
            nds_keyboard.draw_key(key, enabled=key.label in enabled)
        if self.show_back_button:
            nds_keyboard.draw_key(self.back_key)
        nds_keyboard.set_active(self.keys + [self.del_key, self.back_key] + self.candidate_keys)
        self.enabled = enabled
        self.candidates = candidates

    def _run(self):
        self._draw()
        taps = nds_ui.TapTracker()
        while True:
            nds.frame()
            tap = taps.update()
            down = nds.keys_down()
            if not down and tap is None:
                continue
            if down & nds.KEY_A and len(self.candidates) == 1:
                return self.candidates[0]
            if down & nds.KEY_B:
                if self.prefix:
                    self.prefix = self.prefix[:-1]
                    self._draw()
                    continue
                return RET_CODE__BACK_BUTTON
            if tap is None:
                continue
            key = nds_keyboard.key_at(self.candidate_keys + self.keys + [self.del_key, self.back_key],
                                      tap[0], tap[1])
            if key is None:
                continue
            action = key.action
            if isinstance(action, tuple):
                return action[1]
            if action == "back":
                if self.show_back_button:
                    return RET_CODE__BACK_BUTTON
            elif action == "del":
                if self.prefix:
                    self.prefix = self.prefix[:-1]
                    self._draw()
            elif action in self.enabled:
                self.prefix += action
                self._draw()


# Character sets as in upstream SeedAddPassphraseScreen.__post_init__; letters
# use a QWERTY layout here (upstream is alphabetical for its joystick UI).
PASSPHRASE_KEYBOARDS = (
    ("abc", ("qwertyuiop", "asdfghjkl", "zxcvbnm")),
    ("ABC", ("QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM")),
    ("123", ("1234567890",)),
    ("!@#", ("""!@#$%&();:""", """,.-+='"?""")),
    ("*[]", ("""^*[]{}_\\|<""", """>/`~""")),
)
PASSPHRASE_KEY_ROW = 4


class SeedAddPassphraseScreen(BaseTopNavScreen):
    """BIP-39 passphrase on the touch keyboard. Returns, like upstream,
    dict(passphrase=...) on save and dict(passphrase=..., is_back_button=True)
    on back."""

    def __post_init__(self):
        super().__post_init__()
        self.passphrase = self.passphrase or ""
        labels = [name for name, _rows in PASSPHRASE_KEYBOARDS]
        wanted = self.initial_keyboard or labels[0]
        self.mode = labels.index(wanted) if wanted in labels else 0
        self.tabs = [nds_keyboard.Key(label, 0, 1 + i * 6, width=6, action=("mode", i))
                     for i, label in enumerate(labels)]
        self.space_key = nds_keyboard.Key("space", 15, 1, width=17, action=" ")
        self.del_key = nds_keyboard.Key("Del", 15, 19, width=6, action="del")
        self.back_key = nds_keyboard.Key("< Back", 20, 1, width=10, action="back")
        self.save_key = nds_keyboard.Key("Save", 20, 21, width=10, action="save")

    def _render(self):
        pass

    def _keys(self):
        keys = []
        for r, row in enumerate(PASSPHRASE_KEYBOARDS[self.mode][1]):
            col = (nds_ui.COLS - len(row) * 3) // 2
            for i, ch in enumerate(row):
                keys.append(nds_keyboard.Key(ch, PASSPHRASE_KEY_ROW + r * 3, col + i * 3))
        return keys

    def _draw(self):
        shown = self.passphrase
        nds_ui.top_page(_(self.title), [_("Passphrase:"), ""] + nds_ui.wrap(shown or " ") +
                        ["", "%d %s" % (len(shown), _("characters"))])
        nds.bottom_clear()
        self.keys = self._keys()
        for i, tab in enumerate(self.tabs):
            nds_keyboard.draw_key(tab, highlighted=i == self.mode)
        for key in self.keys:
            nds_keyboard.draw_key(key)
        for key in (self.space_key, self.del_key, self.save_key):
            nds_keyboard.draw_key(key)
        if self.show_back_button:
            nds_keyboard.draw_key(self.back_key)
        nds_keyboard.set_active(self.tabs + self.keys + [self.space_key, self.del_key,
                                                         self.back_key, self.save_key])

    def _run(self):
        self._draw()
        taps = nds_ui.TapTracker()
        while True:
            nds.frame()
            tap = taps.update()
            down = nds.keys_down()
            if down & nds.KEY_B and self.show_back_button:
                return dict(passphrase=self.passphrase, is_back_button=True)
            if tap is None:
                continue
            key = nds_keyboard.key_at(nds_keyboard.ACTIVE_KEYS, tap[0], tap[1])
            if key is None:
                continue
            action = key.action
            if isinstance(action, tuple):
                self.mode = action[1]
            elif action == "back":
                if self.show_back_button:
                    return dict(passphrase=self.passphrase, is_back_button=True)
                continue
            elif action == "save":
                return dict(passphrase=self.passphrase)
            elif action == "del":
                self.passphrase = self.passphrase[:-1]
            else:
                self.passphrase += action
            self._draw()


class SeedReviewPassphraseScreen(ButtonListScreen):
    """Like upstream: the passphrase and how it changes the fingerprint."""

    def top_lines(self):
        lines = [_("Passphrase:")] + nds_ui.wrap(self.passphrase or "") + [""]
        lines.append("%s -> %s" % (self.fingerprint_without or "", self.fingerprint_with or ""))
        lines += ["", _("Without -> with passphrase")]
        return lines


class SeedExportXpubDetailsScreen(ButtonListScreen):
    """Like upstream: fingerprint, derivation path and the xpub itself, so the
    user can compare them with what the coordinator shows."""

    def top_lines(self):
        return ([_("Fingerprint") + ": " + (self.fingerprint or ""),
                 _("Derivation") + ": " + (self.derivation_path or ""), "", _("Xpub") + ":"]
                + nds_ui.wrap(self.xpub or ""))


class SeedFinalizeScreen(ButtonListScreen):
    def top_lines(self):
        return ["", nds_ui.center(_("Fingerprint")), "", nds_ui.center(self.fingerprint or "")]


class SeedOptionsScreen(ButtonListScreen):
    def top_lines(self):
        return ["", nds_ui.center(_("Fingerprint")), "", nds_ui.center(self.fingerprint or "")]


class SeedWordsScreen(ButtonListScreen):
    """Like upstream: a page of numbered seed words (upstream's title already
    says "Seed Words: page/pages")."""

    def top_lines(self):
        words = self.words or []
        first = self.page_index * len(words) + 1
        lines = [""]
        for i, word in enumerate(words):
            lines += ["      %2d.  %s" % (first + i, word), ""]
        return lines


class SeedWordsBackupTestPromptScreen(ButtonListScreen):
    def top_lines(self):
        return [""] + nds_ui.wrap(_("Optionally verify that your mnemonic backup is correct."))


class SeedTranscribeSeedQRFormatScreen(ButtonListScreen):
    def top_lines(self):
        return ["", _("Standard"), "  " + _("BIP-39 wordlist indices"), "",
                _("Compact"), "  " + _("Raw entropy bits")]


class SeedTranscribeSeedQRWholeQRScreen(ButtonListScreen):
    """The whole SeedQR on the top screen, ECC level L exactly so it has the
    size of the SeedQR template (checked: a mismatch is shown, not hidden)."""

    def __post_init__(self):
        self.button_data = [_("Begin {}x{}").format(self.num_modules, self.num_modules)]
        super().__post_init__()

    def _render(self):
        nds.top_clear()
        size = nds.qr_transcribe(self.qr_data)
        if size != self.num_modules:
            nds_ui.top_page(_("Transcribe SeedQR"), nds_ui.wrap(
                "QR size %dx%d, expected %dx%d" % (size, size, self.num_modules, self.num_modules)))


class SeedTranscribeSeedQRZoomedInScreen(BaseTopNavScreen):
    """One zone of the SeedQR at a time, 24 px per module, like upstream:
    7x7-module zones for 21x21, 5x5 otherwise; columns 1-6, rows A-F as on
    the SeedQR templates. D-pad or the touch arrows move; Done (or A/B) ends."""

    ZONE_ROWS = "ABCDEF"

    def __post_init__(self):
        super().__post_init__()
        self.zone = 7 if self.num_modules == 21 else 5
        self.zones = (self.num_modules + self.zone - 1) // self.zone
        self.zx = self.initial_zone_x or 0
        self.zy = self.initial_zone_y or 0

    def _render(self):
        nds.top_clear()
        nds.qr_transcribe(self.qr_data, self.zone, self.zx, self.zy)
        nds.top_print(0, -1, str(self.zx + 1))
        nds.top_print(nds_ui.ROWS // 2, 0, self.ZONE_ROWS[self.zy])

    def _draw_panel(self, panel):
        panel.draw()
        nds.bottom_print(18, -1, "%s %s-%d   (%d x %d)" % (
            _("Zone"), self.ZONE_ROWS[self.zy], self.zx + 1, self.zones, self.zones))

    def _run(self):
        moves = [("^", 0, -1), ("v", 0, 1), ("<", -1, 0), (">", 1, 0)]
        panel = nds_ui.ButtonPanel([_("Done")] + [m[0] for m in moves], show_back=False)
        self._draw_panel(panel)
        while True:
            nds.frame()
            down = nds.keys_down()
            step = None
            for key, move in ((nds.KEY_UP, 1), (nds.KEY_DOWN, 2), (nds.KEY_LEFT, 3),
                              (nds.KEY_RIGHT, 4)):
                if down & key:
                    step = moves[move - 1]
            if step is None:
                if down & (nds.KEY_A | nds.KEY_B):
                    return None
                choice = panel.handle_frame()
                if choice == 0:
                    return None
                if choice is not None and choice != nds_ui.BACK:
                    step = moves[choice - 1]
            if step is not None:
                self.zx = min(max(self.zx + step[1], 0), self.zones - 1)
                self.zy = min(max(self.zy + step[2], 0), self.zones - 1)
                self._render()
                self._draw_panel(panel)


class SeedTranscribeSeedQRConfirmQRPromptScreen(ButtonListScreen):
    def top_lines(self):
        return [""] + nds_ui.wrap(_("Optionally scan your transcribed SeedQR to confirm "
                                    "that it reads back correctly."))


class SeedAddressVerificationScreen(ButtonListScreen):
    """Upstream shows this while BruteForceAddressVerificationThread searches
    in the background. Threads run synchronously here, so the search and its
    progress screen run inside the thread (_address_search_poll below); by
    the time the view shows this screen the search has ended: found, or the
    user cancelled."""

    def _run(self):
        if self.verified_index is not None and self.verified_index.cur_count is not None:
            return 1  # upstream _run_callback: success
        return RET_CODE__BACK_BUTTON


def _address_search_poll(thread):
    """Poll hook of BruteForceAddressVerificationThread (compat threading):
    called once per address index. Shows the progress and the Skip 10 /
    Cancel buttons of upstream's SeedAddressVerificationScreen."""
    ui = getattr(thread, "_nds_panel", None)
    if ui is None:
        ui = thread._nds_panel = nds_ui.ButtonPanel([_("Skip 10"), _("Cancel")], show_back=False)
        nds_ui.top_page(_("Verify Address"),
                        nds_ui.wrap(thread.address or "") + ["", thread.derivation_path or ""])
        ui.draw()
    nds.top_print(12, 0, nds_ui.pad(_("Checking address {}").format(
        thread.threadsafe_counter.cur_count)))
    nds.frame()
    choice = ui.handle_frame()
    if choice == 0:
        thread.threadsafe_counter.increment(10)
    elif choice == 1 or nds.keys_down() & nds.KEY_B:
        return False
    return True


import threading as _threading  # noqa: E402  (compat module, see its poll hooks)

_threading.set_poll_hook("BruteForceAddressVerificationThread", _address_search_poll)


class SeedAddressVerificationSuccessScreen(LargeIconStatusScreen):
    """Like upstream: the address, receive or change, and its index."""

    def top_lines(self):
        lines = super().top_lines()
        address_type = _("change address") if self.verified_index_is_change else _("receive address")
        return lines + nds_ui.wrap(self.address or "") + [
            "", nds_ui.center(address_type), nds_ui.center(_("index {}").format(self.verified_index))]


define_generic_screens(globals(), "seed_screens")
