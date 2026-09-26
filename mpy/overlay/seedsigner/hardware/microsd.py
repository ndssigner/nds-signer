# NDS-Signer: there is deliberately no storage access. The signer never reads
# or writes the SD card, so it is always reported as not inserted.
from seedsigner.models.singleton import Singleton


class MicroSD(Singleton):
    ACTION__INSERTED = "add"
    ACTION__REMOVED = "remove"

    @property
    def is_inserted(self):
        return False

    def start_detection(self):
        pass
