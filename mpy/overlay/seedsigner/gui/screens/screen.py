# NDS-Signer - native replacements for SeedSigner's gui/screens/screen.py.
#
# Class names and keyword arguments are upstream's: fields and default values
# come from gui/_upstream.py, generated from the pinned SeedSigner sources, so
# upstream views run unmodified. Rendering is a text layout for the DSi:
# information on the top screen, touch buttons on the bottom screen.
from gettext import gettext as _


from seedsigner.gui import nds_ui
from seedsigner.gui.hw import nds
from seedsigner.gui._upstream import CLASS_ATTRS, POST_INIT, SCREEN_FIELDS, SCREEN_INFO

RET_CODE__BACK_BUTTON = 1000
RET_CODE__POWER_BUTTON = 1001

_MISSING = object()


def _fields_for(cls):
    """Upstream field list for cls or its nearest upstream-named ancestor."""
    klass = cls
    while klass is not None:
        fields = SCREEN_FIELDS.get(klass.__name__)
        if fields is not None:
            return fields
        bases = getattr(klass, "__bases__", ())
        klass = bases[0] if bases else None
    return ()


class _UpstreamFields:
    """Accepts exactly the keyword arguments of the upstream dataclass with
    the same class name, with upstream defaults, then calls __post_init__."""

    def __init__(self, *args, **kwargs):
        fields = _fields_for(type(self))
        names = [name for name, _default in fields]
        if len(args) > len(names):
            raise TypeError("%s: too many positional arguments" % type(self).__name__)
        for i, (name, default) in enumerate(fields):
            if i < len(args):
                value = args[i]
            elif name in kwargs:
                value = kwargs.pop(name)
            elif default is None:
                raise TypeError("%s: missing argument %r" % (type(self).__name__, name))
            else:
                value = default()
            setattr(self, name, value)
        if kwargs:
            raise TypeError("%s: unexpected arguments %s" % (type(self).__name__, sorted(kwargs)))
        self._apply_upstream_post_init()
        self.__post_init__()

    def _apply_upstream_post_init(self):
        """Titles/buttons upstream screens set in __post_init__ (generated),
        applied base class first like upstream's super().__post_init__()."""
        chain = []
        klass = type(self)
        while klass is not None:
            chain.append(klass)
            bases = getattr(klass, "__bases__", ())
            klass = bases[0] if bases else None
        for klass in reversed(chain):
            for attr, only_if_falsy, value in POST_INIT.get(klass.__name__, ()):
                if not only_if_falsy or not getattr(self, attr, None):
                    setattr(self, attr, value(self))

    def __post_init__(self):
        pass


class ButtonOption(_UpstreamFields):
    def __eq__(self, other):
        if not isinstance(other, ButtonOption):
            return False
        return all(getattr(self, n) == getattr(other, n, _MISSING) for n, _d in _fields_for(type(self)))

    def __repr__(self):
        return "ButtonOption(%r)" % (self.button_label,)


class ButtonOptionWithoutTranslation(ButtonOption):
    pass


def _icon_hints():
    """Words for the icons that tell otherwise identical upstream buttons
    apart (Tools: "New seed" with a camera or a dice icon)."""
    from seedsigner.gui.components import FontAwesomeIconConstants as FA
    return {FA.CAMERA: _("camera"), FA.DICE: _("dice")}


def button_labels(buttons):
    """Labels of a button list. Buttons that upstream distinguishes only by
    their icon get the icon's meaning appended, e.g. "New seed (dice)"."""
    original = [button_label(b) for b in buttons]
    labels = list(original)
    hints = None
    for i, label in enumerate(original):
        if original.count(label) > 1:
            hints = hints or _icon_hints()
            icon = getattr(buttons[i], "icon_name", None)
            if icon in hints:
                labels[i] = "%s (%s)" % (label, hints[icon])
    return labels


def button_label(button):
    if isinstance(button, ButtonOption):
        label = button.button_label
        return label if isinstance(button, ButtonOptionWithoutTranslation) else _(label)
    if isinstance(button, tuple):  # legacy (label, icon, ...) tuples
        return str(button[0])
    return str(button)


class BaseScreen(_UpstreamFields):
    def __post_init__(self):
        self.threads = []
        self.components = []
        self.paste_images = []
        self.scroll_y = 0

    def get_threads(self):
        return list(self.threads)

    def display(self):
        self._render()
        return self._run()

    # --- NDS rendering ---
    # A screen describes its top screen either as top_blocks() (graphical
    # layout, see nds_ui.top_blocks) or as top_lines() (32-column text).
    def top_lines(self):
        return []

    def top_blocks(self):
        return None

    def _render(self):
        title = _(getattr(self, "title", "") or "")
        blocks = self.top_blocks()
        if blocks is not None:
            nds_ui.top_blocks(title, blocks)
        else:
            nds_ui.top_page(title, self.top_lines())

    def _run(self):
        return None


class BaseTopNavScreen(BaseScreen):
    def _back_or(self, result):
        if result == nds_ui.BACK:
            return RET_CODE__BACK_BUTTON
        return result


class _ButtonState:
    """Upstream views read screen.buttons[i].scroll_y to restore the list
    position; native lists are paged, so there is no scroll offset."""
    scroll_y = 0


class ButtonListScreen(BaseTopNavScreen):
    def __post_init__(self):
        super().__post_init__()
        self.buttons = [_ButtonState() for _b in (self.button_data or [])]

    def top_lines(self):
        return []

    def _run(self):
        checked = getattr(self, "checked_buttons", None) or []
        labels = button_labels(self.button_data or [])
        panel = nds_ui.ButtonPanel(labels, show_back=self.show_back_button,
                                   selected=self.selected_button or 0, redraw=self._render,
                                   checked=checked, on_page=self._render)
        self._panel = panel  # lets top_blocks() follow the page shown
        return self._back_or(panel.run())


    # Menus with nothing else on the top screen show their section's icon
    SECTION_ICONS = (("seed", "SEEDS"), ("passphrase", "PASSPHRASE"), ("xpub", "QRCODE"),
                     ("setting", "SETTINGS"), ("tool", "TOOLS"), ("explorer", "TOOLS"),
                     ("address", "TOOLS"), ("sign", "SIGN"), ("scan", "SCAN"),
                     ("transaction", "SIGN"), ("language", "SETTINGS"), ("qr", "QRCODE"),
                     ("word", "SEEDS"))

    def top_blocks(self):
        if type(self).top_lines is not ButtonListScreen.top_lines:
            return None  # the screen shows its own content
        from seedsigner.gui.components import SeedSignerIconConstants as Icons
        title = (getattr(self, "title", "") or "").lower()
        for keyword, icon in self.SECTION_ICONS:
            if keyword in title:
                return [("icon", getattr(Icons, icon))]
        return None


class LargeButtonScreen(ButtonListScreen):
    pass


class MainMenuScreen(LargeButtonScreen):
    """NDS-Signer's name and version, and the network when it is not
    mainnet (as a coloured badge, like SeedSigner's top nav)."""

    def top_blocks(self):
        from seedsigner.gui.components import GUIConstants as GC
        from seedsigner.gui.components import SeedSignerIconConstants as Icons
        from seedsigner.models.settings import Settings, SettingsConstants
        blocks = [("icon", Icons.BITCOIN_ALT), ("large", "NDS-Signer"),
                  ("label", _("Air-gapped Bitcoin signer")), ("space", 10)]
        network = Settings.get_instance().get_value(SettingsConstants.SETTING__NETWORK)
        if network == SettingsConstants.TESTNET:
            blocks.append(("value", "Testnet", GC.TESTNET_COLOR))
        elif network == SettingsConstants.REGTEST:
            blocks.append(("value", "Regtest", GC.REGTEST_COLOR))
        blocks += [("space", 6), ("label", nds.version())]
        if nds_ui.nds_dev is not None:
            blocks.append(("label", "DEV build - SELECT: diagnostics"))
        return blocks


def _gc():
    from seedsigner.gui.components import GUIConstants, SeedSignerIconConstants
    return GUIConstants, SeedSignerIconConstants


class LargeIconStatusScreen(ButtonListScreen):
    """Like upstream: a large coloured status icon, a headline in that
    colour and the text (success by default)."""

    def default_status(self):
        GC, Icons = _gc()
        return Icons.SUCCESS, GC.SUCCESS_COLOR

    def top_blocks(self):
        icon, color = self.default_status()
        icon = getattr(self, "status_icon_name", None) or icon
        color = getattr(self, "status_color", None) or color
        return [("icon", icon, color),
                ("headline", _(self.status_headline) if self.status_headline else "", color),
                ("space", 6),
                ("text", _(self.text) if self.text else "")]


class WarningScreen(LargeIconStatusScreen):
    def default_status(self):
        GC, Icons = _gc()
        return Icons.WARNING, GC.WARNING_COLOR


class DireWarningScreen(WarningScreen):
    def default_status(self):
        GC, Icons = _gc()
        return Icons.WARNING, GC.DIRE_WARNING_COLOR


class ErrorScreen(WarningScreen):
    def default_status(self):
        GC, Icons = _gc()
        return Icons.ERROR, GC.ERROR_COLOR


class ResetScreen(BaseTopNavScreen):
    def top_lines(self):
        return ["", "Restarting..."]


class PowerOffNotRequiredScreen(BaseTopNavScreen):
    def top_lines(self):
        return ["", "It is safe to switch off", "the console at any time."]

    def _run(self):
        return self._back_or(nds_ui.ButtonPanel([], show_back=True).run())


class KeyboardScreen(BaseTopNavScreen):
    """Upstream's generic keyboard for short inputs (dice rolls, coin flips,
    BIP-85 index, derivation path): the keys of `keys_charset` on the bottom
    screen, Del, Back and optionally Save. Like upstream it returns the input
    once `return_after_n_chars` characters are entered, the stripped input
    on Save, or RET_CODE__BACK_BUTTON. Upstream subclasses set their keys in
    __post_init__ code that is not replicated here: native subclasses set
    KEYS and COLS instead."""

    KEYS = None     # used when keys_charset is not given
    COLS = None
    FIRST_ROW = 3

    def __post_init__(self):
        super().__post_init__()
        self.user_input = getattr(self, "user_input", None) or self.initial_value or ""

    def update_title(self):
        return False

    def extra_lines(self):
        return []

    def top_lines(self):
        return ["", _("Input:"), ""] + nds_ui.wrap(self.user_input or " ") + [""] + self.extra_lines()

    def _render(self):
        self.update_title()
        nds_ui.top_page(_(getattr(self, "title", "") or ""), self.top_lines())

    def _keys(self):
        from seedsigner.gui import nds_keyboard
        charset = self.keys_charset or self.KEYS or ""
        cols = self.cols or self.COLS or len(charset)
        width = min(9, (nds_ui.COLS - 2) // cols)
        keys = []
        for i, ch in enumerate(charset):
            row, col = divmod(i, cols)
            left = (nds_ui.COLS - cols * width) // 2
            keys.append(nds_keyboard.Key(ch, self.FIRST_ROW + row * 3, left + col * width, width=width))
        last_row = self.FIRST_ROW + ((len(charset) + cols - 1) // cols) * 3
        keys.append(nds_keyboard.Key(_("Del"), last_row + 1, (nds_ui.COLS - 10) // 2, width=10,
                                     action="del"))
        if self.show_back_button:
            keys.append(nds_keyboard.Key(_("< Back"), 20, 1, width=10, action="back"))
        if self.show_save_button:
            keys.append(nds_keyboard.Key(_("Save"), 20, 21, width=10, action="save"))
        return keys

    def _draw(self):
        from seedsigner.gui import nds_keyboard
        self._render()
        nds.bottom_clear()
        keys = self._keys()
        for key in keys:
            nds_keyboard.draw_key(key)
        nds_keyboard.set_active(keys)

    def _run(self):
        from seedsigner.gui import nds_keyboard
        self._draw()
        taps = nds_ui.TapTracker()
        while True:
            nds.frame()
            if nds.keys_down() & nds.KEY_B and self.show_back_button:
                return RET_CODE__BACK_BUTTON
            tap = taps.update()
            if tap is None:
                continue
            key = nds_keyboard.key_at(nds_keyboard.ACTIVE_KEYS, tap[0], tap[1])
            if key is None:
                continue
            if key.action == "back":
                return RET_CODE__BACK_BUTTON
            if key.action == "save":
                if self.user_input:
                    return self.user_input.strip()
                continue
            if key.action == "del":
                self.user_input = self.user_input[:-1]
            else:
                values = self.keys_to_values or {}
                self.user_input += values.get(key.action, key.action)
                if self.return_after_n_chars and len(self.user_input) >= self.return_after_n_chars:
                    return self.user_input
            self._draw()


class QRDisplayScreen(BaseScreen):
    """Animated QR display, as upstream: a new part every 5/30 s, UP/DOWN
    change the QR background brightness (saved to Settings on exit)."""

    FRAME_MS = 167  # upstream: time.sleep(5 / 30.0) between parts
    BORDER = 2      # upstream: next_part_image(..., border=2)

    def _render(self):
        nds.top_clear()

    def _run(self):
        from seedsigner.models.settings import Settings, SettingsConstants

        settings = Settings.get_instance()
        brightness = int(settings.get_value(SettingsConstants.SETTING__QR_BRIGHTNESS))
        panel = nds_ui.ButtonPanel([_("Done")], show_back=False)
        panel.draw()
        nds_ui.bottom_note(120, _("Up/Down: QR brightness"))
        psbt = getattr(self.qr_encoder, "psbt", None)
        if nds_ui.nds_dev is not None and psbt is not None:
            import hashlib
            from binascii import hexlify
            digest = hexlify(hashlib.sha256(psbt.serialize()).digest()).decode()[:8]
            nds_ui.bottom_note(140, "check: " + digest, font=nds.FONT_MONO)
        next_part_at = 0
        try:
            while True:
                nds.frame()
                now = nds.ticks_ms()
                if now >= next_part_at:
                    nds.qr_show(self.qr_encoder.next_part(), self.BORDER, brightness)
                    next_part_at = now + self.FRAME_MS
                down = nds.keys_down()
                if down & nds.KEY_UP:
                    brightness = min(brightness + 31, 255)
                    next_part_at = 0
                elif down & nds.KEY_DOWN:
                    brightness = max(31, brightness - 31)
                    next_part_at = 0
                elif down & nds.KEY_B or panel.handle_frame() is not None:
                    return None
        finally:
            settings.set_value(SettingsConstants.SETTING__QR_BRIGHTNESS, brightness)
            nds.top_clear()


class LoadingScreenThread:
    """Upstream animates a spinner in a thread; here the work runs in the
    foreground, so the text is just shown until the next screen draws."""

    def __init__(self, text=None, *args, **kwargs):
        self.text = text

    def start(self):
        nds_ui.top_page(self.text or _("Loading..."), [])

    def stop(self):
        pass

    def is_alive(self):
        return False


# Names of the upstream screen classes created by define_generic_screens()
# (no native implementation yet): tests/host/menu_crawl.py reports them.
GENERIC_SCREENS = set()


def define_generic_screens(namespace, module):
    """Creates stand-ins for upstream screen classes of `module` that have no
    native implementation yet (generic title/text/buttons rendering), so every
    upstream view module can be imported."""
    native = globals()  # screens implemented natively in this module

    def resolve(name):
        if name in namespace:
            return namespace[name]
        if name in native and isinstance(native[name], type):
            return native[name]
        info = SCREEN_INFO.get(name)
        if info is None:
            return None
        base = None
        for base_name in info[1]:
            if base_name.endswith("Mixin"):
                continue  # drawing-only mixins (e.g. WarningEdgesMixin)
            base = resolve(base_name)
            if base is not None:
                break
        if base is None:
            base = BaseScreen
        cls = type(name, (base,), {})
        GENERIC_SCREENS.add(name)
        if info[0] == module:
            namespace[name] = cls
        return cls

    for name, info in SCREEN_INFO.items():
        if info[0] == module and name.endswith(("Screen", "Option")):
            resolve(name)

    # upstream class-level constants, unless the native class defines them
    for name, attrs in CLASS_ATTRS.items():
        cls = namespace.get(name)
        if cls is None or SCREEN_INFO.get(name, (None,))[0] != module:
            continue
        for attr, value in attrs.items():
            if attr not in cls.__dict__:
                setattr(cls, attr, value)


define_generic_screens(globals(), "screen")
