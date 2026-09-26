# NDS-Signer - `traceback` for MicroPython. SeedSigner's Controller parses
# format_exc() to build its error screen; MicroPython's tracebacks have the
# same "File ..., line N, in f" / "Type: message" shape.
import io
import sys


def _current():
    info = sys.exc_info() if hasattr(sys, "exc_info") else (None, None, None)
    return info[1]


def format_exc(limit=None, chain=True):
    exc = _current()
    if exc is None:
        return "NoneType: None\n"
    buf = io.StringIO()
    sys.print_exception(exc, buf)
    return buf.getvalue()


def print_exc(limit=None, file=None, chain=True):
    exc = _current()
    if exc is not None:
        sys.print_exception(exc, file or sys.stdout)


def format_exception(etype, value=None, tb=None, limit=None, chain=True):
    exc = value if value is not None else etype
    buf = io.StringIO()
    sys.print_exception(exc, buf)
    return buf.getvalue().splitlines(True)


def print_exception(etype, value=None, tb=None, limit=None, file=None, chain=True):
    exc = value if value is not None else etype
    sys.print_exception(exc, file or sys.stdout)
