# NDS-Signer - `threading` for a single-threaded MicroPython build.
#
# Thread.start() runs the thread body synchronously, to completion, and logs
# (instead of raising) an exception, like a real thread would. This fits
# SeedSigner's non-GUI threads (e.g. the controller's background importer);
# GUI threads with endless loops (spinners, live previews) are replaced by
# NDS-Signer's native screens and never reach this class.
#
# Worker threads that loop on `self.keep_running` (SeedSigner's BaseThread
# pattern, e.g. the address verification brute force) would block forever
# while their progress screen never gets to run. A native screen can register
# a poll hook for such a thread class: while the thread body runs, every read
# of keep_running calls hook(thread), which can draw progress, read input and
# return False to stop the loop (like the user leaving the screen would).
import sys

_poll_hooks = {}


def set_poll_hook(class_name, hook):
    """hook(thread) -> bool, called on every keep_running check while a
    thread of class `class_name` runs."""
    _poll_hooks[class_name] = hook


class Thread:
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, daemon=None):
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}
        self.daemon = daemon
        self._alive = False

    def run(self):
        if self._target is not None:
            self._target(*self._args, **self._kwargs)

    @property
    def keep_running(self):
        keep = getattr(self, "_keep_running", False)
        if keep and self._alive:
            hook = _poll_hooks.get(type(self).__name__)
            if hook is not None and not hook(self):
                self._keep_running = keep = False
        return keep

    @keep_running.setter
    def keep_running(self, value):
        self._keep_running = value

    def start(self):
        self._alive = True
        try:
            self.run()
        except Exception as e:
            sys.print_exception(e)
        finally:
            self._alive = False

    def is_alive(self):
        return self._alive

    def join(self, timeout=None):
        pass


class Lock:
    def acquire(self, blocking=True, timeout=-1):
        return True

    def release(self):
        pass

    def locked(self):
        return False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


RLock = Lock


class Event:
    def __init__(self):
        self._flag = False

    def set(self):
        self._flag = True

    def clear(self):
        self._flag = False

    def is_set(self):
        return self._flag

    def wait(self, timeout=None):
        return self._flag
