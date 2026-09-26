# NDS-Signer - small backtracking regex engine in pure Python.
#
# Fallback for patterns MicroPython's built-in engine cannot compile ("regex
# too complex": re1.5 encodes jumps in one byte, so ranges such as {25,62}
# never fit). Supports the subset SeedSigner uses: literals, escapes
# (\d \D \w \W \s \S and escaped punctuation), character classes with ranges
# and negation, ".", "^", "$", capturing and (?:...) groups, alternation, and
# the quantifiers * + ? {m} {m,} {m,n} (greedy and lazy), plus IGNORECASE.
# Anything else raises NotImplementedError.
#
# Single-character atoms under a quantifier are matched with a loop instead of
# recursion, so long runs (e.g. \d{48,96}) do not exhaust the C stack.

IGNORECASE = 2

_DIGITS = "0123456789"
_SPACE = " \t\n\r\f\v"


def _is_word(ch):
    return ch.isalpha() or ch in _DIGITS or ch == "_"


_ESCAPE_CLASSES = {
    "d": lambda c: c in _DIGITS,
    "D": lambda c: c not in _DIGITS,
    "s": lambda c: c in _SPACE,
    "S": lambda c: c not in _SPACE,
    "w": _is_word,
    "W": lambda c: not _is_word(c),
}

# Node kinds
_CHAR, _ANY, _BOL, _EOL, _GROUP, _ALT, _REPEAT, _SEQ = range(8)


class _Parser:
    def __init__(self, pattern, ignorecase):
        self.p = pattern
        self.i = 0
        self.ic = ignorecase
        self.ngroups = 0

    def error(self, msg):
        raise NotImplementedError("regex %r: %s" % (self.p, msg))

    def peek(self):
        return self.p[self.i] if self.i < len(self.p) else None

    def parse(self):
        node = self.alternation()
        if self.i != len(self.p):
            self.error("unexpected ')'")
        return node

    def alternation(self):
        branches = [self.sequence()]
        while self.peek() == "|":
            self.i += 1
            branches.append(self.sequence())
        return branches[0] if len(branches) == 1 else (_ALT, branches)

    def sequence(self):
        items = []
        while self.peek() is not None and self.peek() not in "|)":
            atom = self.atom()
            items.append(self.quantifier(atom))
        return (_SEQ, items)

    def charpred(self, pred):
        if self.ic:
            return (_CHAR, lambda c: pred(c) or pred(c.lower()) or pred(c.upper()))
        return (_CHAR, pred)

    def atom(self):
        ch = self.p[self.i]
        self.i += 1
        if ch == "(":
            capture = True
            if self.p.startswith("?:", self.i):
                capture = False
                self.i += 2
            elif self.peek() == "?":
                self.error("unsupported group extension")
            index = None
            if capture:
                self.ngroups += 1
                index = self.ngroups
            node = self.alternation()
            if self.peek() != ")":
                self.error("missing ')'")
            self.i += 1
            return (_GROUP, index, node)
        if ch == "[":
            return self.charclass()
        if ch == ".":
            return (_ANY,)
        if ch == "^":
            return (_BOL,)
        if ch == "$":
            return (_EOL,)
        if ch == "\\":
            return self.charpred(self.escape())
        if ch in "*+?{":
            if ch == "{" and not self.looks_like_count():
                return self.charpred(lambda c, l=ch: c == l)
            self.error("nothing to repeat")
        return self.charpred(lambda c, l=ch: c == l)

    def escape(self):
        if self.i >= len(self.p):
            self.error("trailing backslash")
        ch = self.p[self.i]
        self.i += 1
        if ch in _ESCAPE_CLASSES:
            return _ESCAPE_CLASSES[ch]
        if ch.isalnum():
            self.error("unsupported escape \\" + ch)
        return lambda c, l=ch: c == l

    def charclass(self):
        negate = False
        if self.peek() == "^":
            negate = True
            self.i += 1
        preds = []
        first = True
        while True:
            ch = self.peek()
            if ch is None:
                self.error("unterminated class")
            if ch == "]" and not first:
                self.i += 1
                break
            first = False
            self.i += 1
            if ch == "\\":
                preds.append(self.escape())
                continue
            if self.peek() == "-" and self.i + 1 < len(self.p) and self.p[self.i + 1] != "]":
                hi = self.p[self.i + 1]
                self.i += 2
                preds.append(lambda c, lo=ch, hi=hi: lo <= c <= hi)
            else:
                preds.append(lambda c, l=ch: c == l)

        def member(c):
            for pred in preds:
                if pred(c):
                    return True
            return False

        if self.ic:
            base = member
            member = lambda c: base(c) or base(c.lower()) or base(c.upper())
        if negate:
            inner = member
            return (_CHAR, lambda c: not inner(c))
        return (_CHAR, member)

    def looks_like_count(self):
        end = self.p.find("}", self.i)
        if end < 0:
            return False
        parts = self.p[self.i:end].split(",")
        return 1 <= len(parts) <= 2 and parts[0].isdigit() and (
            len(parts) == 1 or parts[1] == "" or parts[1].isdigit())

    def quantifier(self, atom):
        ch = self.peek()
        if ch is None:
            return atom
        if ch in "*+?":
            self.i += 1
            lo, hi = {"*": (0, None), "+": (1, None), "?": (0, 1)}[ch]
        elif ch == "{" and (self.i + 1 < len(self.p)) and self.looks_like_count_at(self.i + 1):
            end = self.p.find("}", self.i)
            parts = self.p[self.i + 1:end].split(",")
            lo = int(parts[0])
            hi = lo if len(parts) == 1 else (None if parts[1] == "" else int(parts[1]))
            self.i = end + 1
        else:
            return atom
        lazy = False
        if self.peek() == "?":
            lazy = True
            self.i += 1
        if atom[0] in (_BOL, _EOL):
            self.error("quantified anchor")
        return (_REPEAT, atom, lo, hi, lazy)

    def looks_like_count_at(self, pos):
        saved = self.i
        self.i = pos
        ok = self.looks_like_count()
        self.i = saved
        return ok


def _single_char(node):
    return node[0] in (_CHAR, _ANY)


def _char_ok(node, c):
    return True if node[0] == _ANY else node[1](c)


class _Matcher:
    def __init__(self, text, ngroups):
        self.t = text
        self.groups = [None] * (ngroups + 1)

    # m(node, pos, k): try to match node at pos, then call continuation k(pos).
    # Returns the final position or None.
    def m(self, node, pos, k):
        kind = node[0]
        t = self.t
        if kind == _CHAR or kind == _ANY:
            if pos < len(t) and (kind == _ANY or node[1](t[pos])):
                return k(pos + 1)
            return None
        if kind == _BOL:
            return k(pos) if pos == 0 else None
        if kind == _EOL:
            return k(pos) if pos == len(t) or (pos == len(t) - 1 and t[pos] == "\n") else None
        if kind == _SEQ:
            return self.seq(node[1], 0, pos, k)
        if kind == _ALT:
            for branch in node[1]:
                r = self.m(branch, pos, k)
                if r is not None:
                    return r
            return None
        if kind == _GROUP:
            index = node[1]
            if index is None:
                return self.m(node[2], pos, k)
            saved = self.groups[index]

            def close(end, start=pos):
                prev = self.groups[index]
                self.groups[index] = (start, end)
                r = k(end)
                if r is None:
                    self.groups[index] = prev
                return r

            r = self.m(node[2], pos, close)
            if r is None:
                self.groups[index] = saved
            return r
        if kind == _REPEAT:
            return self.repeat(node, pos, k)
        raise NotImplementedError(kind)

    def seq(self, items, idx, pos, k):
        if idx == len(items):
            return k(pos)
        return self.m(items[idx], pos, lambda p: self.seq(items, idx + 1, p, k))

    def repeat(self, node, pos, k):
        _, atom, lo, hi, lazy = node
        t = self.t
        if _single_char(atom):
            # iterative: count how far the atom can run, then try lengths
            limit = len(t) - pos if hi is None else min(hi, len(t) - pos)
            n = 0
            while n < limit and _char_ok(atom, t[pos + n]):
                n += 1
            if n < lo:
                return None
            lengths = range(lo, n + 1) if lazy else range(n, lo - 1, -1)
            for length in lengths:
                r = k(pos + length)
                if r is not None:
                    return r
            return None

        # general atoms: recursive, guarding against empty iterations
        def attempt(count, p):
            if hi is not None and count == hi:
                return k(p) if count >= lo else None
            if lazy and count >= lo:
                r = k(p)
                if r is not None:
                    return r

            def more(p2):
                if p2 == p:
                    return None  # empty match: stop looping
                return attempt(count + 1, p2)

            r = self.m(atom, p, more)
            if r is not None:
                return r
            if not lazy and count >= lo:
                return k(p)
            return None

        return attempt(0, pos)


class Match:
    def __init__(self, text, spans):
        self._t = text
        self._spans = spans

    def group(self, *indices):
        if not indices:
            indices = (0,)
        out = []
        for i in indices:
            span = self._spans[i]
            out.append(None if span is None else self._t[span[0]:span[1]])
        return out[0] if len(out) == 1 else tuple(out)

    def groups(self, default=None):
        return tuple(default if s is None else self._t[s[0]:s[1]] for s in self._spans[1:])

    def start(self, i=0):
        s = self._spans[i]
        return -1 if s is None else s[0]

    def end(self, i=0):
        s = self._spans[i]
        return -1 if s is None else s[1]

    def span(self, i=0):
        return (self.start(i), self.end(i))


class Pattern:
    def __init__(self, pattern, flags=0):
        parser = _Parser(pattern, bool(flags & IGNORECASE))
        self._node = parser.parse()
        self._ngroups = parser.ngroups
        self.pattern = pattern

    def _match_at(self, text, pos):
        matcher = _Matcher(text, self._ngroups)
        end = matcher.m(self._node, pos, lambda p: p)
        if end is None:
            return None
        spans = [(pos, end)] + matcher.groups[1:]
        return Match(text, spans)

    def match(self, text):
        return self._match_at(text, 0)

    def search(self, text):
        for pos in range(len(text) + 1):
            m = self._match_at(text, pos)
            if m is not None:
                return m
        return None
