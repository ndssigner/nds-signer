# NDS-Signer - extends MicroPython's built-in `re` for SeedSigner.
#
# MicroPython's regex engine (re1.5) has no flags and no counted repetition:
# `\d{3}` does not raise, it silently never matches. SeedSigner's decode_qr.py
# relies on both, so patterns are translated before compiling:
#
#   * re.IGNORECASE: letters become classes, `u` -> `[uU]`, and letters and
#     ranges inside classes get their other case added.
#   * {m} / {m,} / {m,n} after a single atom (literal, escape or class) are
#     expanded into explicit repetitions: `x{2,4}` -> `xx(?:x(?:x)?)?`.
#     Optional copies are nested so the backtracking engine has one path per
#     length (flat `x?x?x?...` backtracks exponentially on a failed match).
#
# re1.5 encodes jumps in one byte, so large ranges ({25,62}) are "too
# complex" for it; those patterns (and any the translator cannot handle
# faithfully, e.g. a counted group) fall back to _pyre, a small pure-Python
# backtracking engine. Checked against CPython's `re`: make -C tests/host re-compat

from ure import *  # the built-in module; `ure` always names the built-in
from ure import compile as _compile

IGNORECASE = I = 2
_FLAG_MASK = IGNORECASE

_cache = {}


def _swap(ch):
    return ch.lower() if ch.isupper() else ch.upper()


def _translate_class(body, ignorecase):
    """body: text between '[' and ']' (may start with '^')."""
    if not ignorecase:
        return "[" + body + "]"
    extra = ""
    i = 1 if body.startswith("^") else 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            i += 2
            continue
        if i + 2 < len(body) and body[i + 1] == "-" and body[i + 2] != "]":
            lo, hi = ch, body[i + 2]
            if lo.isalpha() and hi.isalpha() and lo.islower() == hi.islower():
                extra += _swap(lo) + "-" + _swap(hi)
            i += 3
            continue
        if ch.isalpha():
            extra += _swap(ch)
        i += 1
    return "[" + body + extra + "]"


def _translate(pattern, flags):
    if flags & ~_FLAG_MASK:
        raise NotImplementedError("re flags %r not supported" % flags)
    ignorecase = bool(flags & IGNORECASE)
    out = []  # list of atoms (strings); quantifiers modify the last one
    i, n = 0, len(pattern)
    last_is_atom = False
    while i < n:
        ch = pattern[i]
        if ch == "\\":
            esc = pattern[i:i + 2]
            if ignorecase and len(esc) == 2 and esc[1].isalpha() and esc[1] not in "dDwWsSbB":
                raise NotImplementedError("escaped letter with IGNORECASE: " + esc)
            out.append(esc)
            i += 2
            last_is_atom = True
        elif ch == "[":
            j = i + 1
            if j < n and pattern[j] == "^":
                j += 1
            if j < n and pattern[j] == "]":
                j += 1
            while j < n and pattern[j] != "]":
                j += 2 if pattern[j] == "\\" else 1
            if j >= n:
                raise ValueError("unterminated character class")
            out.append(_translate_class(pattern[i + 1:j], ignorecase))
            i = j + 1
            last_is_atom = True
        elif ch == "{":
            j = pattern.find("}", i)
            spec = pattern[i + 1:j] if j > 0 else ""
            parts = spec.split(",")
            if j < 0 or len(parts) > 2 or not parts[0].isdigit() or (
                    len(parts) == 2 and parts[1] and not parts[1].isdigit()):
                # not a quantifier: a literal brace, as in CPython
                out.append("\\{")
                i += 1
                last_is_atom = True
                continue
            if not last_is_atom:
                raise NotImplementedError("counted repetition after a group: " + pattern)
            atom = out.pop()
            lo = int(parts[0])
            if len(parts) == 1:
                rep = atom * lo
            elif parts[1] == "":
                rep = atom * lo + atom + "*"
            else:
                hi = int(parts[1])
                optional = ""
                for _ in range(hi - lo):
                    optional = "(?:" + atom + optional + ")?"
                rep = atom * lo + optional
            lazy = j + 1 < n and pattern[j + 1] == "?"
            if lazy:
                raise NotImplementedError("lazy counted repetition")
            out.append(rep)
            i = j + 1
            last_is_atom = False
        elif ignorecase and ch.isalpha():
            out.append("[" + ch + _swap(ch) + "]")
            i += 1
            last_is_atom = True
        else:
            out.append(ch)
            i += 1
            # a quantifier can follow a literal, but not ( | ^ $ or another quantifier
            last_is_atom = ch not in "()|^$*+?"
    return "".join(out)


def compile(pattern, flags=0):
    key = (pattern, flags)
    regex = _cache.get(key)
    if regex is None:
        try:
            regex = _compile(_translate(pattern, flags))
        except (ValueError, NotImplementedError):
            import _pyre
            regex = _pyre.Pattern(pattern, flags)
        _cache[key] = regex
    return regex


def search(pattern, string, flags=0):
    return compile(pattern, flags).search(string)


def match(pattern, string, flags=0):
    return compile(pattern, flags).match(string)


def sub(pattern, repl, string, count=0, flags=0):
    return compile(pattern, flags).sub(repl, string, count)


def split(pattern, string, maxsplit=0, flags=0):
    return compile(pattern, flags).split(string, maxsplit)


def findall(pattern, string, flags=0):
    regex = compile(pattern, flags)
    out = []
    pos = 0
    while pos <= len(string):
        m = regex.search(string[pos:])
        if not m:
            break
        groups = m.groups()
        if not groups:
            out.append(m.group(0))
        elif len(groups) == 1:
            out.append(groups[0])
        else:
            out.append(groups)
        end = pos + m.end(0)
        pos = end + 1 if end == pos + m.start(0) else end
    return out
