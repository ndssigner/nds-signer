# NDS-Signer overlay: seedsigner.gui is imported before the Settings singleton
# is created, so NDS-Signer's own settings are registered here.
from .renderer import Renderer  # noqa: F401  (upstream's gui/__init__.py)

SETTING__NDS_SOUND = "nds_sound_effects"
SETTING__NDS_SCAN_INTRO = "nds_scan_intro"
SETTING__NDS_CAMERA = "nds_scan_camera"
CAMERA__REAR, CAMERA__FRONT = "rear", "front"


def _register_settings():
    """Adds NDS-Signer's settings to SeedSigner's: "Sound effects" and "Scan
    preparation" (Enabled/Disabled) after "Denomination display" in the main
    Settings menu, "Scan camera" (rear/front) in Advanced."""
    from seedsigner.models.settings_definition import (SettingsConstants, SettingsDefinition,
                                                       SettingsEntry)
    entries = SettingsDefinition.settings_entries
    if any(e.attr_name == SETTING__NDS_SOUND for e in entries):
        return
    new = [SettingsEntry(category=SettingsConstants.CATEGORY__SYSTEM,
                         attr_name=SETTING__NDS_SOUND,
                         abbreviated_name="sound",
                         display_name="Sound effects",
                         default_value=SettingsConstants.OPTION__ENABLED),
           SettingsEntry(category=SettingsConstants.CATEGORY__SYSTEM,
                         attr_name=SETTING__NDS_SCAN_INTRO,
                         abbreviated_name="scan_intro",
                         display_name="Scan preparation",
                         help_text="Camera choice and tips before scanning",
                         default_value=SettingsConstants.OPTION__ENABLED),
           SettingsEntry(category=SettingsConstants.CATEGORY__SYSTEM,
                         attr_name=SETTING__NDS_CAMERA,
                         abbreviated_name="camera",
                         display_name="Scan camera",
                         type=SettingsConstants.TYPE__SELECT_1,
                         visibility=SettingsConstants.VISIBILITY__ADVANCED,
                         selection_options=[(CAMERA__REAR, "Rear camera"),
                                            (CAMERA__FRONT, "Front camera")],
                         default_value=CAMERA__REAR)]
    after = [i for i, e in enumerate(entries)
             if e.attr_name == SettingsConstants.SETTING__BTC_DENOMINATION]
    at = after[0] + 1 if after else len(entries)
    entries[at:at] = new


def _language_options():
    """Settings > Language offers English and the translations frozen into
    the ROM (tools/po_to_py.py), in SeedSigner's order and with its names.
    Upstream looks for .mo files on disk, which NDS-Signer does not have."""
    from seedsigner.models.settings_definition import SettingsConstants, SettingsDefinition
    try:
        from nds_l10n_index import LOCALES
    except ImportError:
        LOCALES = []
    options = [(SettingsConstants.LOCALE__ENGLISH,
                SettingsConstants.ALL_LOCALES[SettingsConstants.LOCALE__ENGLISH])]
    for locale, name in SettingsConstants.ALL_LOCALES.items():
        if locale in LOCALES:
            options.append((locale, name))
    for entry in SettingsDefinition.settings_entries:
        if entry.attr_name == SettingsConstants.SETTING__LOCALE:
            entry.selection_options = options
    # LocaleSelectionView asks for them directly
    SettingsConstants.get_detected_languages = classmethod(lambda cls: list(options))
    return [locale for locale, _name in options]


_register_settings()
AVAILABLE_LOCALES = _language_options()

# DS user settings language -> SeedSigner locale
_SYSTEM_LOCALES = {0: "ja", 1: "en", 2: "fr", 3: "de", 4: "it", 5: "es", 6: "zh_Hans_CN", 7: "ko"}


def apply_system_language():
    """Starts in the console's language when there is a translation for it
    (else English); Settings > Language changes it for the session."""
    from seedsigner.gui.hw import nds
    from seedsigner.models.settings import Settings, SettingsConstants
    locale = _SYSTEM_LOCALES.get(nds.system_language(), "en")
    if locale != "en" and locale in AVAILABLE_LOCALES:
        Settings.get_instance().set_value(SettingsConstants.SETTING__LOCALE, locale)
    return locale if locale in AVAILABLE_LOCALES else "en"
