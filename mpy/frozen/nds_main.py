# NDS-Signer - Python entry point (run by arm9/src/main.c).
# Starts SeedSigner's own Controller on NDS-Signer's native screens.
from seedsigner.gui.hw import nds

nds.camera_init()

from seedsigner.controller import Controller  # noqa: E402

Controller.get_instance().start()
