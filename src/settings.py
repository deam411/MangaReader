"""
Modulo per gestire le impostazioni dell'applicazione.
Le impostazioni vengono salvate in formato JSON nella directory dei dati dell'app.
"""
import json
import os
from .paths import get_data_dir
from .constants import (
    APP_VERSION,
    DEFAULT_CACHE_SIZE,
    DEFAULT_PRELOAD_PAGES,
    DEFAULT_THEME
)
from .logger import get_logger
from .exceptions import SettingsLoadError, SettingsSaveError

logger = get_logger(__name__)


class Settings:
    """
    Classe singleton per gestire le impostazioni dell'applicazione.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.settings_file = os.path.join(get_data_dir(), "settings.json")
        self.settings = self._load_settings()

    def _get_default_settings(self):
        """Restituisce le impostazioni di default."""
        return {
            "version": APP_VERSION,
            "library_path": None,  # None = usa percorso di default
            "theme": DEFAULT_THEME,  # system, dark o light
            "language": "it",
            "last_opened_manga": None,
            "window_geometry": None,
            "shortcuts": {
                "quit": "Esc",
                "back": "Backspace",
                "next_page": "Right",
                "prev_page": "Left",
                "fullscreen": "F11",
                "search": "Ctrl+F",
                "import": "Ctrl+I",
                "export": "Ctrl+E",
                "new_manga": "Ctrl+N",
                "refresh": "F5"
            },
            "performance": {
                "image_cache_size": DEFAULT_CACHE_SIZE,  # Numero di immagini in cache
                "lazy_loading": True,
                "preload_pages": DEFAULT_PRELOAD_PAGES  # Numero di pagine da precaricare
            },
            "reader": {
                "reading_direction": "ltr",  # "ltr" (left-to-right) o "rtl" (right-to-left)
                "view_mode": "single",  # "single" o "double" (doppia pagina)
                "zoom_level": 1.0  # Livello zoom di default
            }
        }

    def _load_settings(self):
        """
        Carica le impostazioni dal file JSON.

        Returns:
            Dict con le impostazioni caricate o default

        Raises:
            SettingsLoadError: Se il caricamento fallisce criticamente
        """
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Merge con default per aggiungere nuove chiavi
                    default = self._get_default_settings()
                    for key, value in default.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
            except json.JSONDecodeError as e:
                logger.error(f"Settings file corrupted, using defaults: {e}")
                # File corrotto, usa default invece di errore
                return self._get_default_settings()
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                # Errore critico lettura file
                raise SettingsLoadError(f"Impossibile caricare impostazioni da {self.settings_file}") from e
        else:
            return self._get_default_settings()

    def save(self):
        """
        Salva le impostazioni nel file JSON.

        Returns:
            True se salvato con successo

        Raises:
            SettingsSaveError: Se il salvataggio fallisce
        """
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            raise SettingsSaveError(f"Impossibile salvare impostazioni in {self.settings_file}") from e

    def get(self, key, default=None):
        """Ottiene un valore dalle impostazioni."""
        keys = key.split('.')
        value = self.settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value if value is not None else default

    def set(self, key, value):
        """Imposta un valore nelle impostazioni."""
        keys = key.split('.')
        settings = self.settings
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        settings[keys[-1]] = value
        self.save()

    def get_library_path(self):
        """
        Restituisce il percorso della libreria custom dall'utente.
        Restituisce None se non è stato impostato un percorso custom.
        """
        path = self.get("library_path")
        # Se path è None o stringa vuota, significa usa il default
        if not path:
            return None
        return path

    def set_library_path(self, path):
        """Imposta il percorso della libreria."""
        if os.path.exists(path) or path == "":
            self.set("library_path", path)
            return True
        return False

    def get_theme(self):
        """Restituisce il tema corrente."""
        return self.get("theme", "system")

    def set_theme(self, theme):
        """Imposta il tema."""
        if theme in ["system", "dark", "light"]:
            self.set("theme", theme)
            return True
        return False

    def reset_to_default(self):
        """Resetta tutte le impostazioni ai valori di default."""
        self.settings = self._get_default_settings()
        self.save()
