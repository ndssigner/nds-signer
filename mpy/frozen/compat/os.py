# NDS-Signer - `os` stub. There is deliberately no filesystem: the signer is
# stateless and never reads or writes the SD card. Path helpers work on
# strings; anything that would touch storage fails.
sep = "/"
environ = {}


class _Path:
    sep = "/"

    @staticmethod
    def join(*parts):
        return "/".join(str(p).rstrip("/") for p in parts if str(p))

    @staticmethod
    def exists(path):
        return False

    @staticmethod
    def dirname(path):
        return path.rsplit("/", 1)[0] if "/" in path else ""

    @staticmethod
    def basename(path):
        return path.rsplit("/", 1)[-1]


path = _Path()


def _refuse(*args, **kwargs):
    raise OSError("no filesystem on NDS-Signer")


remove = fsync = listdir = mkdir = stat = _refuse


def walk(top):
    return iter(())
