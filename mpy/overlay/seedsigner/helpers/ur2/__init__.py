# NDS-Signer overlay. Upstream's helpers/ur2/__init__.py is empty (mpy/Makefile
# fails the build if that changes, so nothing upstream is hidden here).
#
# Installs the native inner loop of Bytewords "minimal" decoding
# (lib/mpy-usermods/bytewords) in SeedSigner's helpers/ur2/bytewords.py:
# decode_word() in Python costs ~0.4 ms per byte on the DSi, ~100 ms per
# animated QR part. Everything else is upstream's code: other Bytewords
# styles, and the length and checksum checks below (copied from decode()).
# tests/host/bytewords_check.py compares both versions.
try:
    import _bytewords
except ImportError:  # CPython: upstream code only
    _bytewords = None

if _bytewords is not None:
    from . import bytewords as _bw

    _upstream_decode = _bw.decode

    def _decode(s, separator, word_len):
        if word_len != 2:
            return _upstream_decode(s, separator, word_len)

        buf = _bytewords.decode_minimal(s, _bw.BYTEWORDS)

        # upstream decode() from here on
        if len(buf) < 5:
            raise ValueError('Invalid Bytewords.')

        # Validate checksum
        body = buf[0:-4]
        body_checksum = buf[-4:]
        checksum = _bw.crc32_bytes(body)
        if checksum != body_checksum:
            raise ValueError('Invalid Bytewords.')

        return body

    _bw.decode = _decode
