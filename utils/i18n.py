"""
Internationalization (i18n) Language Manager for Project KISAN.
Supports English (en), Hindi (hi), and Marathi (mr) with 100% offline local resolution.
Emits real-time PyQt signals on language toggle and syncs preference to SQLite database.
"""

import os
import json
from PyQt5.QtCore import QObject, pyqtSignal
from database.db import db_session
from database.models import AppSetting

TRANSLATIONS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "database", "data", "translations.json")
)


class LanguageManager(QObject):
    """
    Singleton Language Manager for reactive multi-language UI translation.
    """
    language_changed = pyqtSignal(str)
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LanguageManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, parent=None):
        if self._initialized:
            return
        super().__init__(parent)
        self._initialized = True
        self._current_language = "en"
        self._translations = {}
        self._load_translations()
        self._load_saved_language()

    def _load_translations(self):
        """Load local offline translations JSON dictionary."""
        if not os.path.exists(TRANSLATIONS_PATH):
            print(f"[i18n] Warning: Translation file not found at {TRANSLATIONS_PATH}")
            self._translations = {"en": {}, "hi": {}, "mr": {}}
            return

        try:
            with open(TRANSLATIONS_PATH, "r", encoding="utf-8") as f:
                self._translations = json.load(f)
            print(f"[i18n] Loaded offline translations for languages: {list(self._translations.keys())}")
        except Exception as e:
            print(f"[i18n] Error loading translations: {e}")
            self._translations = {"en": {}, "hi": {}, "mr": {}}

    def _load_saved_language(self):
        """Retrieve farmer's language preference from SQLite database."""
        try:
            setting = db_session.query(AppSetting).filter_by(setting_key="app_language").first()
            if setting and setting.setting_value in ["en", "hi", "mr"]:
                self._current_language = setting.setting_value
                print(f"[i18n] Restored saved language setting: '{self._current_language}'")
        except Exception as e:
            print(f"[i18n] DB load notice (defaulting to 'en'): {e}")

    def set_language(self, lang_code: str):
        """
        Set active language ('en', 'hi', 'mr'), update SQLite DB, and emit signal.
        """
        if lang_code not in ["en", "hi", "mr"]:
            print(f"[i18n] Unsupported language code: {lang_code}")
            return

        if self._current_language != lang_code:
            self._current_language = lang_code
            self._save_language_setting(lang_code)
            self.language_changed.emit(lang_code)
            print(f"[i18n] Language switched to: '{lang_code}'")

    def _save_language_setting(self, lang_code: str):
        """Save selected language preference to SQLite DB."""
        try:
            setting = db_session.query(AppSetting).filter_by(setting_key="app_language").first()
            if not setting:
                setting = AppSetting(setting_key="app_language", setting_value=lang_code)
                db_session.add(setting)
            else:
                setting.setting_value = lang_code
            db_session.commit()
        except Exception as e:
            print(f"[i18n] Failed to persist language to DB: {e}")

    def get_language(self) -> str:
        """Return currently active language code ('en', 'hi', or 'mr')."""
        return self._current_language

    def tr(self, key: str, default: str = "") -> str:
        """
        Lookup translated string for given key in active language.
        Falls back to English or key itself if missing.
        """
        lang_dict = self._translations.get(self._current_language, {})
        if key in lang_dict:
            return lang_dict[key]

        # Fallback to English
        en_dict = self._translations.get("en", {})
        if key in en_dict:
            return en_dict[key]

        return default if default else key


# Global singleton instance helper function
def get_language_manager() -> LanguageManager:
    return LanguageManager()
