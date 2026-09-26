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
        self.enabled = enabled
        self.candidates = candidates

    def _run(self):
        self._draw()
        while True:
            nds.frame()
            down = nds.keys_down()
            if not down:
                continue
            if down & nds.KEY_A and len(self.candidates) == 1:
                return self.candidates[0]
            if down & nds.KEY_B:
                if self.prefix:
                    self.prefix = self.prefix[:-1]
                    self._draw()
                    continue
                return RET_CODE__BACK_BUTTON
            if not down & nds.KEY_TOUCH:
                continue
            xy = nds.touch()
            if xy is None:
                continue
            key = nds_keyboard.key_at(self.candidate_keys + self.keys + [self.del_key, self.back_key],
                                      xy[0], xy[1])
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


class SeedFinalizeScreen(ButtonListScreen):
    def top_lines(self):
        return ["", nds_ui.center(_("Fingerprint")), "", nds_ui.center(self.fingerprint or "")]


class SeedOptionsScreen(ButtonListScreen):
    def top_lines(self):
        return ["", nds_ui.center(_("Fingerprint")), "", nds_ui.center(self.fingerprint or "")]


define_generic_screens(globals(), "seed_screens")
