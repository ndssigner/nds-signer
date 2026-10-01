# NDS-Signer - `gettext` for SeedSigner's translations.
#
# SeedSigner selects the language by setting os.environ["LANGUAGE"]
# (Settings.load_locale) and translates with gettext at display time. The
# catalogs are SeedSigner's .po files turned into frozen modules
# nds_l10n_<locale>.py by tools/po_to_py.py; only the current language's is
# kept in memory. English (or a missing message) returns the text as is.
import os
import sys

_state = {"lang": None, "messages": {}, "plurals": {}}


def _catalog():
    lang = os.environ.get("LANGUAGE", "en") or "en"
    if lang != _state["lang"]:
        old = _state["lang"]
        if old:
            sys.modules.pop("nds_l10n_" + old, None)  # let the old catalog go
        messages, plurals = {}, {}
        if lang != "en":
            try:
                module = __import__("nds_l10n_" + lang)
                messages, plurals = module.MESSAGES, module.PLURALS
            except ImportError:
                pass
        _state.update(lang=lang, messages=messages, plurals=plurals)
    return _state


def gettext(message):
    return _catalog()["messages"].get(message, message)


def ngettext(singular, plural, n):
    forms = _catalog()["plurals"].get(singular)
    if forms:
        return forms[0] if n == 1 else forms[1] if len(forms) > 1 else forms[0]
    return singular if n == 1 else plural


def bindtextdomain(domain, localedir=None):
    return localedir


def textdomain(domain=None):
    return "messages"
