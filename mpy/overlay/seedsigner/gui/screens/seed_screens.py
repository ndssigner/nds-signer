# NDS-Signer: generic stand-ins for upstream gui/screens/seed_screens.py until native
# versions are written (see screen.define_generic_screens).
from seedsigner.gui.screens.screen import define_generic_screens

define_generic_screens(globals(), "seed_screens")
