# Checks that NDS-Signer's overlay provides everything upstream SeedSigner
# imports from seedsigner.gui / seedsigner.hardware (list from
# gui_imports_gen.py). Runs on MicroPython with the ROM's module path.
import json
import sys

missing = []
for module, name in json.load(open(sys.argv[1])):
    try:
        mod = __import__(module, None, None, [name])
        if not hasattr(mod, name):
            __import__(module + "." + name)  # a submodule, e.g. screens.seed_screens
    except Exception as e:
        missing.append("%s.%s (%s)" % (module, name, e))
for m in missing:
    print("  missing:", m)
print("ok  " if not missing else "FAIL", "overlay provides all upstream gui/hardware imports (%d missing)"
      % len(missing))
