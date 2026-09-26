# NDS-Signer - `pathlib` stub: pure string paths, no filesystem access.


class Path:
    def __init__(self, *parts):
        self._p = "/".join(str(p).rstrip("/") for p in parts if str(p))

    def resolve(self):
        return self

    @property
    def parent(self):
        return Path(self._p.rsplit("/", 1)[0] if "/" in self._p else "")

    def __truediv__(self, other):
        return Path(self._p, other)

    def __str__(self):
        return self._p

    def exists(self):
        return False
