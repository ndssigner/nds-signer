# NDS-Signer - `unicodedata` for MicroPython.
#
# SeedSigner normalizes mnemonics and BIP-39 passphrases (NFKD / NFC). For
# ASCII text every normalization form is the identity. Non-ASCII input is
# REFUSED instead of passed through, because a wrong normalization would
# silently derive a different seed. Full NFKD support is a TODO.


def normalize(form, text):
    for ch in text:
        if ord(ch) > 0x7F:
            raise ValueError("non-ASCII text is not supported yet (Unicode normalization)")
    return text
