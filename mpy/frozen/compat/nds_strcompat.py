# NDS-Signer - str methods that MicroPython does not have, as functions.
# tools/upy_transform.py rewrites s.zfill(n) in upstream code to zfill(s, n).


def zfill(s, width):
    """str.zfill: pads with zeros on the left, after a leading sign."""
    if len(s) >= width:
        return s
    sign = s[:1] if s[:1] in ("+", "-") else ""
    return sign + "0" * (width - len(s)) + s[len(sign):]
