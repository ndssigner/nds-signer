# NDS-Signer: replaces SeedSigner's helpers/version.py, which works out the
# version from git, CI environment variables or SeedSigner OS's version.json.
# None of these exist on the DSi. Same public API (Version); the version is
# NDS-Signer's, set at build time (git describe), and the SeedSigner release
# it is built on is shown as the "fork".
from seedsigner.gui.hw import nds

# third_party/seedsigner (git describe): update with the submodule
SEEDSIGNER_BASE = "0.8.7-149-gcfaf443"


class Version:
    @classmethod
    def get_version_name(cls) -> str:
        return nds.version()

    @classmethod
    def get_version_fork(cls) -> str:
        return "SeedSigner " + SEEDSIGNER_BASE

    @classmethod
    def get_short_commit_hash(cls) -> str:
        return None

    @classmethod
    def get_version_timestamp(cls):
        return None

    @classmethod
    def is_release_image(cls) -> bool:
        return False
