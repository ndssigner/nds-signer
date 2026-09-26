# NDS-Signer - `gettext` stub: English only for now. Translations will be
# generated from SeedSigner's catalogs at build time (docs/architecture.md).


def gettext(message):
    return message


def ngettext(singular, plural, n):
    return singular if n == 1 else plural


def bindtextdomain(domain, localedir=None):
    return localedir


def textdomain(domain=None):
    return "messages"
