# NDS-Signer: the developer build's scan hooks (mpy/frozen/dev/nds_dev.py)
# against the simulator's `nds` API, including a real ScanScreen run: a
# mismatch between nds_dev and the native/simulated camera API crashed the
# dev build on every scan once.
import sys

sys.path.append("/source/mpy/frozen/dev")
import nds
import nds_dev
from seedsigner.gui import nds_ui

nds_ui.nds_dev = nds_dev  # as on a developer build
from seedsigner.gui.screens.scan_screens import ScanScreen
from seedsigner.models.decode_qr import DecodeQR
from test_vectors import DATA

native_len = [int(line.split()[2]) for line in open("/source/arm9/include/nds_bridge.h")
              if line.startswith("#define NDSB_CAMERA_STATS")][0]
assert len(nds.camera_stats()) == native_len, "sim camera_stats() differs from the native API"

parts = DATA["psbt_base64_singlesig.ur.txt"].split()
events = [("key", nds.KEY_R), ("key", nds.KEY_R), ("key", nds.KEY_L)]
for p in parts:
    events += [("camera", p.encode()), ("wait", 2)]
nds.sim_script(events)
decoder = DecodeQR()
ScanScreen(decoder=decoder).display()
lines = nds_dev.report_lines()
ok = decoder.is_complete and any(l.startswith("last scan") and "AE 2/" in l for l in lines)
print("ok  " if ok else "FAIL", "dev build scan hooks: %s" % [l for l in lines if l.startswith("last scan")])
