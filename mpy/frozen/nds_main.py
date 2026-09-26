# NDS-Signer - Python entry point (run by arm9/src/main.c).
# Starts SeedSigner's own Controller on NDS-Signer's native screens.
# If anything escapes the Controller (it handles view errors itself), show the
# traceback instead of leaving a frozen screen.
import io
import sys

from seedsigner.gui.hw import nds


def _fatal(exc):
    buf = io.StringIO()
    sys.print_exception(exc, buf)
    text = buf.getvalue()
    print(text)  # also to the debug channel (melonDS log)
    nds.top_clear()
    nds.top_print(0, -1, "NDS-Signer stopped")
    row = 2
    for line in text.split("\n"):
        while line and row < nds.ROWS:
            nds.top_print(row, 0, line[:nds.COLS])
            line = line[nds.COLS:]
            row += 1
    # The same report as a QR code: a phone photo of it can be decoded exactly
    report = "NDS-Signer " + nds.version() + "\n" + text
    nds.bottom_clear()
    nds.bottom_print(9, -1, "A: show error as QR code")
    nds.bottom_print(11, -1, "Switch the console off")
    while True:
        nds.frame()
        if nds.keys_down() & nds.KEY_A:
            nds.top_clear()
            if not nds.qr_show(report[:1500], 2, 255):
                nds.top_print(0, 0, "report too long for a QR")


try:
    print("nds_main: starting")
    nds.camera_init()
    from seedsigner.controller import Controller

    Controller.get_instance().start()
except BaseException as e:  # noqa: B902 - last line of defence
    _fatal(e)
