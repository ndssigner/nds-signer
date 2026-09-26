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
    def top_lines(self):
        return []

    def _render(self):
        nds_ui.top_page(_(getattr(self, "title", "") or ""), self.top_lines())

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
        labels = [("* " if i in checked else "") + button_label(b)
                  for i, b in enumerate(self.button_data or [])]
        panel = nds_ui.ButtonPanel(labels, show_back=self.show_back_button,
                                   selected=self.selected_button or 0)
        return self._back_or(panel.run())


class LargeButtonScreen(ButtonListScreen):
    pass


class MainMenuScreen(LargeButtonScreen):
    def top_lines(self):
        return ["", "", "", "      NDS-Signer", "", "  Air-gapped Bitcoin signer"]


class LargeIconStatusScreen(ButtonListScreen):
    ICON = "[OK]"

    def top_lines(self):
        lines = ["", nds_ui.center(self.ICON), ""]
        if self.status_headline:
            lines += [nds_ui.center(line) for line in nds_ui.wrap(_(self.status_headline))]
            lines.append("")
        if self.text:
            lines += nds_ui.wrap(_(self.text))
        return lines


class WarningScreen(LargeIconStatusScreen):
    ICON = "/!\\"


class DireWarningScreen(WarningScreen):
    ICON = "/!!!\\"


class ErrorScreen(WarningScreen):
    ICON = "[X]"


class ResetScreen(BaseTopNavScreen):
    def top_lines(self):
        return ["", "Restarting..."]


class PowerOffNotRequiredScreen(BaseTopNavScreen):
    def top_lines(self):
        return ["", "It is safe to switch off", "the console at any time."]

    def _run(self):
        return self._back_or(nds_ui.ButtonPanel([], show_back=True).run())


class KeyboardScreen(BaseTopNavScreen):
    def _run(self):
        raise NotImplementedError("touch keyboard not implemented yet")


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
        nds.bottom_print(17, -1, _("Up/Down: QR brightness"))
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
            base = resolve(base_name)
            if base is not None:
                break
        if base is None:
            base = BaseScreen
        cls = type(name, (base,), {})
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
