# NDS-Signer: keys and touch are read by the native screens through `nds`.
from seedsigner.models.singleton import Singleton


class HardwareButtonsConstants:
    KEY_UP = "up"
    KEY_DOWN = "down"
    KEY_LEFT = "left"
    KEY_RIGHT = "right"
    KEY_PRESS = "press"
    KEY1 = "key1"
    KEY2 = "key2"
    KEY3 = "key3"


class HardwareButtons(Singleton):
    def check_for_low(self, *args, **kwargs):
        return False

    def wait_for(self, *args, **kwargs):
        return None

    def update_last_input_time(self):
        pass
