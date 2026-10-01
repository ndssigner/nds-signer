# NDS-Signer - native replacements for SeedSigner's gui/screens/tools_screens.py
# (same class names and keyword arguments, see screen.py). Screens without a
# native version yet are generic stand-ins (define_generic_screens).
from gettext import gettext as _

from seedsigner.gui import nds_ui
from seedsigner.gui.hw import nds
from seedsigner.gui.screens.screen import (RET_CODE__BACK_BUTTON, BaseScreen, ButtonListScreen,
                                           KeyboardScreen, define_generic_screens)
from seedsigner.models.settings_definition import SettingsConstants, SettingsDefinition


class ToolsImageEntropyLivePreviewScreen(BaseScreen):
    """Like upstream: the camera's live image (top screen) while
    PREVIEW_POOL_SIZE distinct frames are collected as extra entropy, flat
    frames (a covered or saturated sensor) and repeats skipped; once the
    pool is full (collecting stops: the screen stays responsive), "Take
    photo" (or A) ends. Returns the frames, as NdsFrame
    objects holding each frame's SHA-256 (see hardware/camera.py), or
    RET_CODE__BACK_BUTTON. The camera keeps running for the final image
    (Camera.capture_frame, ToolsImageEntropyFinalImageView)."""

    PREVIEW_POOL_SIZE = 50
    BAR_Y, BUTTON_Y = 70, 104

    def _render(self):
        nds.top_clear()
        nds.gfx_present(nds_ui.TOP)

    def _draw_panel(self, count):
        t = nds_ui.theme()
        nds.bottom_clear()
        nds.gfx_clear(nds_ui.BOTTOM, t["bg"])
        full = count >= self.PREVIEW_POOL_SIZE
        nds_ui.text_centered(nds_ui.BOTTOM, 24, _("Collecting entropy frames"), nds.FONT_BODY_BOLD,
                             t["body"])
        width = nds_ui.GFX_W - 2 * 24 - 50
        nds.gfx_rect(nds_ui.BOTTOM, 24, self.BAR_Y, width, 6, t["inactive"], 3)
        if count:
            from seedsigner.gui.components import GUIConstants as GC
            nds.gfx_rect(nds_ui.BOTTOM, 24, self.BAR_Y, max(6, width * count // self.PREVIEW_POOL_SIZE),
                         6, nds_ui.color_value(GC.GREEN_INDICATOR_COLOR, t["accent"]), 3)
        nds.gfx_text(nds_ui.BOTTOM, 24 + width + 8, self.BAR_Y - 6,
                     _("{}/{}").format(count, self.PREVIEW_POOL_SIZE), nds.FONT_BODY, t["label"])
        nds_ui.button(nds_ui.BOTTOM, nds_ui.MARGIN, self.BUTTON_Y, nds_ui.GFX_W - 2 * nds_ui.MARGIN,
                      nds_ui.BUTTON_H, _("Take photo"), selected=full, enabled=full)
        nds_ui.button(nds_ui.BOTTOM, nds_ui.MARGIN, nds_ui.NAV_Y, 80, nds_ui.NAV_H, _("< Back"),
                      font=nds.FONT_BODY_BOLD)
        nds.gfx_present(nds_ui.BOTTOM)

    def _run(self):
        import hashlib
        from seedsigner.hardware.camera import NdsFrame, use_front_camera

        if not nds.camera_start(use_front_camera()):
            return RET_CODE__BACK_BUTTON
        nds.camera_decode(False)
        pool, seen, shown = [], set(), -1
        buf = bytearray(nds.CAMERA_FRAME_BYTES)
        taps = nds_ui.TapTracker()
        try:
            while True:
                nds.frame()
                down = nds.keys_down()
                tap = taps.update()
                if down & nds.KEY_B or (tap and tap[1] >= nds_ui.NAV_Y and tap[0] < 96):
                    nds_ui.sound("back")
                    nds.camera_stop()
                    return RET_CODE__BACK_BUTTON
                nds.camera_poll()  # live image on the top screen
                # Upstream keeps replacing the oldest frame once the pool is
                # full; here collecting stops then: hashing a 600 KB frame
                # takes long enough to miss quick taps on "Take photo"
                full = len(pool) == self.PREVIEW_POOL_SIZE
                if not full and nds.camera_grab(buf) == 1:
                    digest = hashlib.sha256(buf).digest()
                    if digest not in seen:
                        seen.add(digest)
                        pool.append(NdsFrame(digest))
                if len(pool) != shown:
                    shown = len(pool)
                    self._draw_panel(shown)
                take = down & nds.KEY_A or (
                    tap and self.BUTTON_Y <= tap[1] < self.BUTTON_Y + nds_ui.BUTTON_H)
                if take and len(pool) == self.PREVIEW_POOL_SIZE:
                    nds_ui.sound("click")
                    nds_ui.bottom_note(self.BUTTON_Y + nds_ui.BUTTON_H + 12, _("Capturing image..."),
                                       color=nds_ui.theme()["accent"])
                    return pool
        except BaseException:
            nds.camera_stop()
            raise


class ToolsImageEntropyFinalImageScreen(BaseScreen):
    """Like upstream: the final picture, to accept or reshoot (Back)."""

    def _render(self):
        nds.top_clear()
        nds.frame_show(nds_ui.TOP, self.final_image.data)

    def _run(self):
        def cap(text):
            return text[:1].upper() + text[1:]
        choice = nds_ui.ButtonPanel([cap(_("accept")), cap(_("reshoot"))], show_back=False).run()
        return RET_CODE__BACK_BUTTON if choice == 1 else None


class ToolsScribbleMicEntropyScreen(BaseScreen):
    """NDS-Signer's own new seed tool (views/nds_entropy_views.py): scribble
    on the bottom screen while the microphone records. Every stylus reading
    (position and time) and every microphone buffer goes into one SHA-256.
    Done is enabled once there are TOUCH_POINTS distinct stylus positions
    and MIC_BUFFERS microphone buffers that are not flat (a dead microphone
    gives identical samples). Returns the 32-byte digest, or
    RET_CODE__BACK_BUTTON. The microphone is on only on this screen."""

    TOUCH_POINTS = 256
    MIC_BUFFERS = 16       # 1/4 s each
    LEVEL_FULL = 4000      # sample magnitude shown as a full level bar
    BUTTON_W = 80

    def _top(self, points, buffers, level):
        """One progress bar for both sources (each counts half), a line
        saying what is missing, and the sound level in colour."""
        from seedsigner.gui.components import GUIConstants as GC
        touch = min(points / self.TOUCH_POINTS, 1)
        mic = min(buffers / self.MIC_BUFFERS, 1)
        if touch >= 1 and mic >= 1:
            hint = _("Done: enough entropy collected")
        elif touch < 1 and mic < 1:
            hint = _("Keep scribbling and making noise")
        elif touch < 1:
            hint = _("Keep scribbling")
        else:
            hint = _("Make some noise")
        loud = level / self.LEVEL_FULL
        color = (GC.SUCCESS_COLOR if loud < 0.4 else GC.WARNING_COLOR if loud < 0.75
                 else GC.ERROR_COLOR)
        nds_ui.top_blocks(_("New seed"), [
            ("text", _("Scribble on the bottom screen and make some noise: talk, whistle or "
                       "tap the console.")), ("space", 10),
            ("bar", _("Progress"), (touch + mic) / 2),
            ("label", hint), ("space", 6),
            ("bar", _("Sound level"), loud, color)])

    def _buttons(self, complete):
        t = nds_ui.theme()
        nds.gfx_rect(nds_ui.BOTTOM, 0, nds_ui.NAV_Y - 2, nds_ui.GFX_W, nds_ui.GFX_H - nds_ui.NAV_Y + 2,
                     t["bg"])
        nds_ui.button(nds_ui.BOTTOM, nds_ui.MARGIN, nds_ui.NAV_Y, self.BUTTON_W, nds_ui.NAV_H,
                      _("< Back"), font=nds.FONT_BODY_BOLD)
        nds_ui.button(nds_ui.BOTTOM, nds_ui.GFX_W - nds_ui.MARGIN - self.BUTTON_W, nds_ui.NAV_Y,
                      self.BUTTON_W, nds_ui.NAV_H, _("Done"), selected=complete, enabled=complete,
                      font=nds.FONT_BODY_BOLD)

    def _render(self):
        self._top(0, 0, 0)

    def _run(self):
        import hashlib
        import struct

        t = nds_ui.theme()
        nds.bottom_clear()
        nds.gfx_clear(nds_ui.BOTTOM, t["bg"])
        canvas_h = nds_ui.NAV_Y - 4
        nds.gfx_frame(nds_ui.BOTTOM, 0, 0, nds_ui.GFX_W, canvas_h, t["inactive"], 6, 1)
        self._buttons(False)
        nds.gfx_present(nds_ui.BOTTOM)
        if not nds.mic_start():
            raise Exception(_("Microphone not available"))
        h = hashlib.sha256(b"NDS-Signer scribble + mic entropy v1")
        buf = bytearray(nds.MIC_BUFFER_BYTES)
        points, buffers, level, last = set(), 0, 0, None
        shown = (0, 0, 0)
        complete = False
        taps = nds_ui.TapTracker()
        try:
            while True:
                nds.frame()
                down = nds.keys_down()
                xy = nds.touch()
                if xy is not None and (xy[0] or xy[1]) and xy != last:
                    last = xy
                    h.update(struct.pack("<HHI", xy[0], xy[1], nds.ticks_ms()))
                    if xy[1] < canvas_h - 2 and xy not in points:
                        points.add(xy)
                        nds.gfx_rect(nds_ui.BOTTOM, max(1, xy[0] - 1), max(1, xy[1] - 1), 3, 3,
                                     t["accent"], 0)
                        nds.gfx_present(nds_ui.BOTTOM)
                n, peak = nds.mic_take(buf)
                if n:
                    h.update(buf)
                    if peak:
                        buffers += 1
                    level = peak
                progress = (min(len(points), self.TOUCH_POINTS), min(buffers, self.MIC_BUFFERS),
                            level)
                if progress != shown:
                    shown = progress
                    self._top(*progress)
                if not complete and len(points) >= self.TOUCH_POINTS and buffers >= self.MIC_BUFFERS:
                    complete = True
                    nds_ui.sound("success")
                    self._buttons(True)
                    nds.gfx_present(nds_ui.BOTTOM)
                tap = taps.update()
                on_nav = tap is not None and tap[1] >= nds_ui.NAV_Y
                if down & nds.KEY_B or (on_nav and tap[0] < nds_ui.MARGIN + self.BUTTON_W):
                    nds_ui.sound("back")
                    return RET_CODE__BACK_BUTTON
                done = down & nds.KEY_A or (on_nav and tap[0] >= nds_ui.GFX_W - nds_ui.MARGIN
                                            - self.BUTTON_W)
                if done and complete:
                    nds_ui.sound("click")
                    h.update(struct.pack("<I", nds.ticks_ms()))
                    return h.digest()
        finally:
            nds.mic_stop()


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
    """Upstream: one button per address ("index:start...end"), then "Next N";
    choosing one shows its QR code. Here the top screen shows the selected
    address in full, with its QR code; a tap selects an address (or the
    D-pad), a tap on the selected one (or A) opens upstream's QR view."""

    QR_PX = 92
    HEAD = TAIL = 11  # characters shown on the buttons, as upstream

    def __post_init__(self):
        addresses = self.addresses or []
        self.button_data = ["%d:%s...%s" % (self.start_index + i, a[:self.HEAD], a[-self.TAIL:])
                            for i, a in enumerate(addresses)]
        self.button_data.append(_("Next {}").format(len(addresses)))
        super().__post_init__()

    def panel_options(self):
        return dict(on_select=self._render, tap_selects=True, content=self._button_content)

    def _selected(self):
        panel = getattr(self, "_panel", None)
        return panel.selected if panel is not None else (self.selected_button or 0)

    def _button_content(self, i, x, y, w, h, selected):
        """Index on the left, then the address' start and end in the
        fixed-width font (the top screen shows it in full)."""
        t = nds_ui.theme()
        addresses = self.addresses or []
        if i >= len(addresses):  # "Next N"
            line_h = nds.gfx_font_metrics(nds.FONT_BUTTON)[1]
            color = t["bg"] if selected else t["button_fg"]
            nds_ui.text_centered(nds_ui.BOTTOM, y + (h - line_h) // 2, self.button_data[i],
                                 nds.FONT_BUTTON, color, x, w)
            return
        address = addresses[i]
        font, mono = nds.FONT_BODY_BOLD, nds.FONT_MONO
        index_color = t["bg"] if selected else t["label"]
        text_color = t["bg"] if selected else t["button_fg"]
        dots_color = t["bg"] if selected else t["label"]
        line_h = nds.gfx_font_metrics(font)[1]
        index = str(self.start_index + i)
        nds.gfx_text(nds_ui.BOTTOM, x + 36 - nds.gfx_text_width(index, font), y + (h - line_h) // 2,
                     index, font, index_color)
        char_w = nds.gfx_text_width("0", mono)
        mono_h = nds.gfx_font_metrics(mono)[1]
        my = y + (h - mono_h) // 2
        parts = ((address[:self.HEAD], text_color), ("\u2026", dots_color),
                 (address[-self.TAIL:], text_color))
        mx = x + 48
        for text, color in parts:
            nds.gfx_text(nds_ui.BOTTOM, mx, my, text, mono, color)
            mx += len(text) * char_w

    def top_blocks(self):
        addresses = self.addresses or []
        sel = self._selected()
        if sel >= len(addresses):
            return [("headline", self.button_data[-1] if self.button_data else "")]
        address = addresses[sel]
        # bech32 in capitals: a smaller QR code (alphanumeric mode, BIP-173)
        qr = address.upper() if address.lower().startswith(("bc1", "tb1", "bcrt1")) else address
        return [("qr", qr, self.QR_PX, "#%d" % (self.start_index + sel)), ("space", 6),
                ("address", address)]


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
