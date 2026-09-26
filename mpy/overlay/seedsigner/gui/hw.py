# NDS-Signer: the hardware module used by the native GUI. Normally the native
# `nds` module; in AUTOTEST builds a scripted proxy (autopilot.py) that taps
# buttons by label, so the emulator can run the whole flow unattended.
import nds as _native

try:
    import autopilot
    nds = autopilot.Autopilot(_native)
except ImportError:
    nds = _native
