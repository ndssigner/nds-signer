# NDS-Signer overlay: seedsigner.gui is imported before the Settings singleton
# is created, so NDS-Signer's own settings are registered here.
from .renderer import Renderer  # noqa: F401  (upstream's gui/__init__.py)

SETTING__NDS_SOUND = "nds_sound_effects"


def _register_settings():
    """Adds "Sound effects" (Enabled/Disabled) to SeedSigner's settings,
    after "Denomination display" in the main Settings menu."""
    from seedsigner.models.settings_definition import (SettingsConstants, SettingsDefinition,
                                                       SettingsEntry)
    entries = SettingsDefinition.settings_entries
    if any(e.attr_name == SETTING__NDS_SOUND for e in entries):
        return
    entry = SettingsEntry(category=SettingsConstants.CATEGORY__SYSTEM,
                          attr_name=SETTING__NDS_SOUND,
                          abbreviated_name="sound",
                          display_name="Sound effects",
                          default_value=SettingsConstants.OPTION__ENABLED)
    after = [i for i, e in enumerate(entries)
             if e.attr_name == SettingsConstants.SETTING__BTC_DENOMINATION]
    entries.insert(after[0] + 1 if after else len(entries), entry)


_register_settings()
