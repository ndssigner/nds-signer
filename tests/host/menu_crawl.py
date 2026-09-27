# NDS-Signer - menu crawler. Drives SeedSigner's unmodified Controller and
# views through NDS-Signer's native screens on the host simulator, visiting
# every reachable menu option, and reports:
#   - views that raise (with the taps that reproduce it),
#   - upstream screens reached that only have a generic stand-in
#     (define_generic_screens: title and buttons, but upstream draws more),
#   - views reached.
#
#   micropython menu_crawl.py [scan payload name] [-v]
#
# The scan payload (a tests/vectors file name, or "none") is what the fake
# camera shows whenever a ScanScreen opens, to reach the flows behind it.
#
# Breadth-first over button lists: every run starts at Home with the same
# settings and seed, replays the taps of one path, and at the first button
# list past its end queues one path per option. A (view, buttons) screen is
# expanded once, however many paths reach it. Other screens that wait for
# input get B, then "Done", then "< Back".
import sys

import nds
from seedsigner.controller import Controller, StopFlowBasedTest
from seedsigner.gui import nds_ui
from seedsigner.gui.screens import screen as screen_mod
from seedsigner.views import view as view_mod

PAYLOAD = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "none"
VERBOSE = "-v" in sys.argv
# --path=Seeds>8b218e81>Export xpub: run only this path, tracing each view
ONLY_PATH = [a[7:].split(">") for a in sys.argv if a.startswith("--path=")]
MAX_DECISIONS = 20000

current_view = ["?"]
trail = []           # views run since Home
MAX_DEPTH = 14       # taps per path
views_seen = {}
generic_seen = {}
errors = {}          # (view, exception line) -> (taps, where)
expanded = set()     # (view, labels) screens whose options were queued
queue = ONLY_PATH or [[]]  # paths (lists of button labels) still to run
target = []          # path being run
cursor = [0]         # next step of `target`
taps = []            # what was actually done since Home (for reports)
decisions = [0]


# scan payloads that are not tests/vectors files
PAYLOADS = {
    "signmessage": "signmessage m/84h/1h/0h/0/0 ascii:hello",
    "settingsqr": "settings::v1 name=Foo",
    # first receive address of the test seed (testnet, native segwit)
    "own_address": "bitcoin:tb1qw2as76rh4jhykn9zvevdt5tawmqx7hhy7ydvvu",
}


def read_vector(name):
    if name in PAYLOADS:
        return PAYLOADS[name]
    import test_vectors
    return test_vectors.DATA[name].strip()


# --- which view is running, and which screens it shows ---
_orig_run = view_mod.Destination.run


def _run(self):
    name = self.View_cls.__name__ if self.View_cls else "None"
    current_view[0] = name
    if name == "MainMenuView":
        del trail[:]
    trail.append(name)
    if ONLY_PATH:
        print("view", name, self.view_args)
    views_seen[name] = views_seen.get(name, 0) + 1
    return _orig_run(self)


view_mod.Destination.run = _run

_orig_display = screen_mod.BaseScreen.display


def _display(self):
    name = type(self).__name__
    if name in screen_mod.GENERIC_SCREENS:
        generic_seen.setdefault(name, set()).add(current_view[0])
    if name == "ScanScreen" and PAYLOAD != "none":
        nds.sim_camera([read_vector(PAYLOAD).encode()])
    return _orig_display(self)


screen_mod.BaseScreen.display = _display


# --- choices on button lists ---
class _PathDone(Exception):
    """Ends the current path: back to Home for the next one."""


def _panel_run(self):
    self.draw()
    decisions[0] += 1
    if decisions[0] > MAX_DECISIONS:
        raise StopFlowBasedTest()
    if cursor[0] < len(target):
        label = target[cursor[0]]
        cursor[0] += 1
        if label == "<Back" and self.show_back:
            taps.append("%s:<Back" % current_view[0])
            return nds_ui.BACK
        if label in self.labels:
            taps.append("%s:%s" % (current_view[0], label))
            return self.labels.index(label)
        raise _PathDone()  # the replay went elsewhere (state changed)
    # the same view class can serve several flows (e.g. script type selection
    # for xpub export and for the address explorer): tell them apart by the
    # views that led to it
    key = (tuple(trail[-4:]), tuple(self.labels))
    if ONLY_PATH:
        print("end of path at", key)
        raise StopFlowBasedTest()
    if key not in expanded and len(target) < MAX_DEPTH:
        expanded.add(key)
        for label in self.labels:
            queue.append(target + [label])
    raise _PathDone()


nds_ui.ButtonPanel.run = _panel_run


# --- screens with their own input loop: B, then Done, then < Back ---
_orig_frame = nds.frame
_idle = [0]


def _frame():
    if not nds._events and not nds._touch_queue:
        _idle[0] += 1
        if _idle[0] % 40 == 0:
            step = (_idle[0] // 40) % 3
            if step == 1:
                nds.sim_script([("key", nds.KEY_B)])
            else:
                label = "Done" if step == 2 else "< Back"
                try:
                    nds._find_label(label)
                    nds.sim_script([("tap_label", label)])
                except AssertionError:
                    nds.sim_script([("key", nds.KEY_B)])
            taps.append("%s:<idle %d>" % (current_view[0], step))
        if _idle[0] > 4000:
            raise StopFlowBasedTest()
    else:
        _idle[0] = 0
    return _orig_frame()


nds.frame = _frame


# --- errors: record and go Home instead of the error screen ---
def _handle_exception(self, e):
    from seedsigner.views.view import MainMenuView, Destination
    if isinstance(e, _PathDone):
        return _next_path()
    import io
    buf = io.StringIO()
    sys.print_exception(e, buf)
    lines = [l for l in buf.getvalue().splitlines() if l.strip()]
    where = [l.strip() for l in lines if l.strip().startswith("File")]
    key = (current_view[0], lines[-1] if lines else repr(e))
    if key not in errors:
        errors[key] = (list(taps), where[-3:])
    return _next_path()


def _next_path():
    """Resets settings and seeds, and starts the next queued path at Home."""
    from seedsigner.models.settings import Settings
    from seedsigner.views.view import Destination, MainMenuView
    if not queue:
        raise StopFlowBasedTest()
    target[:] = queue.pop(0)
    cursor[0] = 0
    del taps[:]
    settings = Settings.get_instance()
    settings._data.clear()
    settings._data.update(_copy(_settings0))
    storage = Controller.get_instance().storage
    storage.seeds[:] = list(_seeds0)
    storage.clear_pending_seed()
    return Destination(MainMenuView, clear_history=True)


def _copy(value):
    """Deep copy of settings data (list values are changed in place)."""
    if isinstance(value, dict):
        return {k: _copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_copy(v) for v in value]
    return value


_settings0 = {}
_seeds0 = []


Controller.handle_exception = _handle_exception


def main():
    from seedsigner.models.seed import Seed
    from seedsigner.models.settings import Settings, SettingsConstants
    from seedsigner.views.view import Destination, MainMenuView

    controller = Controller.get_instance()
    Settings.get_instance().set_value(SettingsConstants.SETTING__NETWORK, SettingsConstants.TESTNET)
    controller.storage.set_pending_seed(Seed(read_vector("psbt_base64_singlesig.mnemonic.txt").split()))
    controller.storage.finalize_pending_seed()
    _settings0.update(_copy(Settings.get_instance()._data))
    _seeds0.extend(controller.storage.seeds)
    try:
        controller.start(initial_destination=_next_path())
    except StopFlowBasedTest:
        pass

    print("crawl (scan payload: %s): %d decisions, %d screens expanded, %d paths left, "
          "%d views, %d errors, %d generic screens" % (
              PAYLOAD, decisions[0], len(expanded), len(queue), len(views_seen), len(errors),
              len(generic_seen)))
    for (view, exc), (steps, where) in sorted(errors.items()):
        print("ERROR  %s: %s" % (view, exc))
        for w in where:
            print("         " + w)
        print("         taps: " + " > ".join(steps[-10:]))
    for name in sorted(generic_seen):
        print("GENERIC %s (from %s)" % (name, ", ".join(sorted(generic_seen[name]))))
    if VERBOSE:
        for name in sorted(views_seen):
            print("VIEW   %s x%d" % (name, views_seen[name]))
        for views, labels in sorted(expanded):
            print("SCREEN %s: %s" % (" > ".join(views), " | ".join(labels)))


main()
