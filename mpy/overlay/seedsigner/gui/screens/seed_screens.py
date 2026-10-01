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
    KeyboardScreen,
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
        self.back_key = nds_keyboard.Key(_("< Back"), 20, 1, width=10, action="back")

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
        self.back_key = nds_keyboard.Key(_("< Back"), 20, 1, width=10, action="back")
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

    def top_blocks(self):
        return [("label", _("Passphrase")), ("value", self.passphrase or ""), ("space", 10),
                ("label", _("Without -> with passphrase")),
                ("value", "%s -> %s" % (self.fingerprint_without or "", self.fingerprint_with or ""))]


class SeedExportXpubDetailsScreen(ButtonListScreen):
    """Like upstream: fingerprint, derivation path and the xpub itself, so the
    user can compare them with what the coordinator shows."""

    def top_lines(self):
        return ([_("Fingerprint") + ": " + (self.fingerprint or ""),
                 _("Derivation") + ": " + (self.derivation_path or ""), "", _("Xpub") + ":"]
                + nds_ui.wrap(self.xpub or ""))


def _fingerprint_blocks(fingerprint):
    from seedsigner.gui.components import GUIConstants as GC
    from seedsigner.gui.components import SeedSignerIconConstants as Icons
    return [("icon", Icons.FINGERPRINT, GC.INFO_COLOR), ("label", _("Fingerprint")),
            ("large", fingerprint or "")]


class SeedFinalizeScreen(ButtonListScreen):
    def top_blocks(self):
        return _fingerprint_blocks(self.fingerprint)


class SeedOptionsScreen(ButtonListScreen):
    def top_blocks(self):
        return _fingerprint_blocks(self.fingerprint)


class SeedWordsScreen(ButtonListScreen):
    """Like upstream: a page of numbered seed words (upstream's title already
    says "Seed Words: page/pages")."""

    def top_blocks(self):
        words = self.words or []
        first = self.page_index * len(words) + 1
        return [("large", "%d. %s" % (first + i, word)) for i, word in enumerate(words)]


class SeedWordsBackupTestPromptScreen(ButtonListScreen):
    def top_blocks(self):
        return [("text", _("Optionally verify that your mnemonic backup is correct."))]


class SeedTranscribeSeedQRFormatScreen(ButtonListScreen):
    def top_blocks(self):
        return [("headline", _("Standard")), ("label", _("BIP-39 wordlist indices")), ("space", 12),
                ("headline", _("Compact")), ("label", _("Raw entropy bits"))]


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
    the SeedQR templates (shown as labels over the code). D-pad or the
    touch arrows move; Done (or A/B) ends."""

    ZONE_ROWS = "ABCDEF"
    # touch arrows (x, y, w, h, label, dx, dy) around the centre of the screen
    ARROW_W, ARROW_H = 60, 40
    ARROWS = ((98, 44, "^", 0, -1), (98, 136, "v", 0, 1), (30, 90, "<", -1, 0),
              (166, 90, ">", 1, 0))

    def __post_init__(self):
        super().__post_init__()
        self.zone = 7 if self.num_modules == 21 else 5
        self.zones = (self.num_modules + self.zone - 1) // self.zone
        self.zx = self.initial_zone_x or 0
        self.zy = self.initial_zone_y or 0

    def _render(self):
        t = nds_ui.theme()
        nds.top_clear()
        nds.qr_transcribe(self.qr_data, self.zone, self.zx, self.zy)
        # zone labels on accent tabs, like upstream's rulers
        nds.gfx_rect(nds_ui.TOP, 108, 0, 40, 22, t["accent"], 6)
        nds_ui.text_centered(nds_ui.TOP, 0, str(self.zx + 1), nds.FONT_TITLE, t["bg"], 108, 40)
        nds.gfx_rect(nds_ui.TOP, 0, 76, 26, 40, t["accent"], 6)
        nds_ui.text_centered(nds_ui.TOP, 84, self.ZONE_ROWS[self.zy], nds.FONT_TITLE, t["bg"], 0, 26)
        nds.gfx_present(nds_ui.TOP)

    def _draw_panel(self):
        t = nds_ui.theme()
        nds.bottom_clear()
        nds.gfx_clear(nds_ui.BOTTOM, t["bg"])
        nds_ui.button(nds_ui.BOTTOM, 8, 4, 240, 28, _("Done"), selected=True)
        for x, y, label, _dx, _dy in self.ARROWS:
            nds_ui.button(nds_ui.BOTTOM, x, y, self.ARROW_W, self.ARROW_H, label)
        nds_ui.text_centered(nds_ui.BOTTOM, 100, "%s-%d" % (self.ZONE_ROWS[self.zy], self.zx + 1),
                             nds.FONT_TITLE, t["accent"], 98, self.ARROW_W)
        nds_ui.text_centered(nds_ui.BOTTOM, 172, "%s %d x %d" % (_("Zones"), self.zones, self.zones),
                             nds.FONT_BODY, t["label"])
        nds.gfx_present(nds_ui.BOTTOM)

    def _tap(self, x, y):
        if 8 <= x < 248 and 4 <= y < 32:
            return "done"
        for ax, ay, _label, dx, dy in self.ARROWS:
            if ax <= x < ax + self.ARROW_W and ay <= y < ay + self.ARROW_H:
                return (dx, dy)
        return None

    def _run(self):
        self._draw_panel()
        taps = nds_ui.TapTracker()
        keys = ((nds.KEY_UP, (0, -1)), (nds.KEY_DOWN, (0, 1)), (nds.KEY_LEFT, (-1, 0)),
                (nds.KEY_RIGHT, (1, 0)))
        while True:
            nds.frame()
            down = nds.keys_down()
            if down & (nds.KEY_A | nds.KEY_B):
                return None
            step = None
            for key, move in keys:
                if down & key:
                    step = move
            tap = taps.update()
            if tap is not None:
                hit = self._tap(tap[0], tap[1])
                if hit == "done":
                    return None
                step = hit or step
            if step is not None:
                self.zx = min(max(self.zx + step[0], 0), self.zones - 1)
                self.zy = min(max(self.zy + step[1], 0), self.zones - 1)
                self._render()
                self._draw_panel()


class SeedTranscribeSeedQRConfirmQRPromptScreen(ButtonListScreen):
    def top_blocks(self):
        return [("text", _("Optionally scan your transcribed SeedQR to confirm "
                           "that it reads back correctly."))]


class SeedSelectSeedScreen(ButtonListScreen):
    """Like upstream: a text above the list of seeds (e.g. which seed to
    verify an address with)."""

    def top_blocks(self):
        return [("text", _(self.text))] if self.text else None


class SeedBIP85SelectChildIndexScreen(KeyboardScreen):
    KEYS = "0123456789"
    COLS = 5

    def __post_init__(self):
        self.show_save_button = True
        super().__post_init__()


class SeedExportXpubCustomDerivationScreen(KeyboardScreen):
    KEYS = "/'0123456789"
    COLS = 6

    def __post_init__(self):
        self.show_save_button = True
        super().__post_init__()
        self.user_input = self.user_input or "m/"


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
        nds_ui.top_blocks(_("Verify Address"), [("value", thread.address or ""), ("space", 4),
                                                 ("label", thread.derivation_path or "")])
        ui.draw()
    nds_ui.top_note(150, _("Checking address {}").format(thread.threadsafe_counter.cur_count),
                    nds_ui.theme()["accent"])
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

    def top_blocks(self):
        address_type = _("change address") if self.verified_index_is_change else _("receive address")
        return super().top_blocks() + [("space", 6), ("value", self.address or ""), ("space", 4),
                                       ("label", "%s \u00b7 %s" % (address_type,
                                                                   _("index {}").format(self.verified_index)))]


define_generic_screens(globals(), "seed_screens")
