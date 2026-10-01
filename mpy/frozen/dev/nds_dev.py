# NDS-Signer - DEVELOPER BUILD ONLY (make DEVBUILD=1): diagnostics for testing
# on real hardware. Press SELECT on any menu. The report can be shown as a QR
# code, so a phone photo of it can be decoded exactly (no retyping).
import gc
import sys

from seedsigner.gui.hw import nds
from seedsigner.gui import nds_ui

_benchmark = []
_last_scan = []


def report_lines():
    dsi, camera, cheap, uptime = nds.info()
    frames, decode_ms = nds.camera_stats()[:2]
    gc.collect()
    lines = [
        "NDS-Signer DEV " + nds.version(),
        "DSi mode: %s  camera: %s" % ("yes" if dsi else "NO", "ok" if camera else "NO"),
        "uptime %ds  C heap %dKB" % (uptime, cheap),
        "Py heap used %dKB free %dKB" % (gc.mem_alloc() // 1024, gc.mem_free() // 1024),
        "cam frames %d decode %dms" % (frames, decode_ms),
        "python " + sys.version.split(" ")[0],
    ]
    return lines + _last_scan + _benchmark


def _scan_summary(parts, py_ms):
    """Two lines: camera/quirc rates and averages, Python per decoded part."""
    (frames, _last, grids, decoded, copy_us, ident_us, dec_us, elapsed, refines,
     restarts) = nds.camera_stats()
    n = max(frames, 1)
    fps10 = frames * 10000 // max(elapsed, 1)
    return [
        "fps %d.%d qr %d/%d ok %d rf %d rs %d" % (fps10 // 10, fps10 % 10, grids, frames,
                                                decoded, refines, restarts),
        "ms cp%d id%d dc%d py%d" % (copy_us // n // 1000, ident_us // n // 1000,
                                   dec_us // n // 1000, py_ms // max(parts, 1)),
    ]


def scan_frame(parts, py_ms, show_stats):
    """Called by ScanScreen every frame: live statistics."""
    if show_stats:
        for i, line in enumerate(_scan_summary(parts, py_ms)):
            nds.bottom_print(8 + i, 1, nds_ui.pad(line, nds_ui.COLS - 2))


def record_scan(parts, py_ms):
    frames, elapsed = nds.camera_stats()[0], nds.camera_stats()[7]
    _last_scan[:] = ["last scan %d.%ds, %d parts" % (elapsed // 1000, elapsed % 1000 // 100, parts)]
    _last_scan.extend(_scan_summary(parts, py_ms))


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
    _benchmark.extend(_scan_benchmark())


def _scan_benchmark():
    """quirc on synthetic 640x480 frames of UR parts at SeedSigner's three
    densities, and SeedSigner's DecodeQR cost per part (Python). One line per
    density: "<density><chars> <copy>+<identify>+<decode>ms (QR ~400 px wide)
    id <otsu>/<binarize>/<finder>/<grouping> py <ms per part>"."""
    from binascii import a2b_base64

    from seedsigner.helpers.ur2.ur import UR
    from seedsigner.helpers.ur2.ur_encoder import UREncoder
    from seedsigner.models.decode_qr import DecodeQR
    from urtypes.crypto import PSBT as UR_PSBT
    from test_vectors import DATA

    psbt = a2b_base64(DATA["psbt_base64_10in.txt"].strip())
    lines = []
    for name, fragment in (("L", 10), ("M", 30), ("H", 120)):
        encoder = UREncoder(ur=UR("crypto-psbt", UR_PSBT(psbt).to_cbor()), max_fragment_len=fragment)
        part = encoder.next_part().upper()
        r = nds.scan_benchmark(part, 400)
        if r is None:
            line = "%s%d n/a" % (name, len(part))
        else:
            line = "%s%d %s%d+%d+%d id%s" % (
                name, len(part), "" if r[0] else "FAIL ", r[1] // 1000, r[2] // 1000, r[3] // 1000,
                "/".join(str(us // 1000) for us in r[4:]))
        parts = [part] + [encoder.next_part().upper() for _ in range(15)]
        decoder = DecodeQR()
        t0 = nds.ticks_ms()
        for p in parts:
            decoder.add_data(p)
        line += " py%d" % ((nds.ticks_ms() - t0) // len(parts))
        print("bench:", line)
        lines.append(line)
    return lines


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
    nds.gfx_present(nds_ui.BOTTOM)
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
