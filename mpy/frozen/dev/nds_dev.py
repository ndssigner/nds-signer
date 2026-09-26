# NDS-Signer - DEVELOPER BUILD ONLY (make DEVBUILD=1): diagnostics for testing
# on real hardware. Press SELECT on any menu. The report can be shown as a QR
# code, so a phone photo of it can be decoded exactly (no retyping).
import gc
import sys

from seedsigner.gui.hw import nds
from seedsigner.gui import nds_ui

_benchmark = []


def report_lines():
    dsi, camera, cheap, uptime = nds.info()
    frames, decode_ms = nds.camera_stats()
    gc.collect()
    lines = [
        "NDS-Signer DEV " + nds.version(),
        "DSi mode: %s  camera: %s" % ("yes" if dsi else "NO", "ok" if camera else "NO"),
        "uptime %ds  C heap %dKB" % (uptime, cheap),
        "Py heap used %dKB free %dKB" % (gc.mem_alloc() // 1024, gc.mem_free() // 1024),
        "cam frames %d decode %dms" % (frames, decode_ms),
        "python " + sys.version.split(" ")[0],
    ]
    return lines + _benchmark


def _run_benchmark():
    from binascii import unhexlify

    from embit import bip32, bip39, ec

    t0 = nds.ticks_ms()
    seed = bip39.mnemonic_to_seed("abandon " * 11 + "about")
    t1 = nds.ticks_ms()
    root = bip32.HDKey.from_seed(seed)
    key = root.derive("m/84h/0h/0h/0/0")
    t2 = nds.ticks_ms()
    for _ in range(10):
        key.key.sign(unhexlify("11" * 32))
    t3 = nds.ticks_ms()
    del _benchmark[:]
    _benchmark.append("pbkdf2 %dms derive %dms sign %dms" % (t1 - t0, t2 - t1, (t3 - t2) // 10))


def diagnostics():
    """Blocking diagnostics screen; returns when the user leaves it."""
    panel = nds_ui.ButtonPanel(["Benchmark", "Show as QR", "Touch test"], show_back=True,
                               header="DIAGNOSTICS")
    while True:
        nds_ui.top_page("Diagnostics", report_lines())
        choice = panel.run()
        if choice == nds_ui.BACK:
            return
        if choice == 0:
            nds_ui.top_page("Diagnostics", ["Running benchmark..."])
            _run_benchmark()
        elif choice == 1:
            nds.top_clear()
            nds.qr_show("\n".join(report_lines()), 2, 255)
            nds_ui.ButtonPanel(["Back"], show_back=False).run()
        elif choice == 2:
            _touch_test()


def _touch_test():
    nds.bottom_clear()
    nds.bottom_print(0, -1, "Touch anywhere. B = exit")
    nds_ui.top_page("Touch test", ["Tap the bottom screen;", "the position is shown here."])
    while True:
        nds.frame()
        if nds.keys_down() & nds.KEY_B:
            return
        xy = nds.touch()
        if xy:
            nds.top_print(8, 0, nds_ui.pad("x=%d y=%d" % xy))
            nds.bottom_print(xy[1] // 8, xy[0] // 8, "+")
