"""Sistema i18n per MangaReader con file JSON."""
import json
import os
from typing import Dict, List, Optional
from ..logger import get_logger

logger = get_logger(__name__)

class TranslationManager:
    """
    Gestore traduzioni con file JSON.

    Carica traduzioni da file JSON nella directory locales/
    Formato: i18n/locales/{lang_code}.json
    """

    def __init__(self):
        self.current_language = 'en'
        self.translations: Dict[str, Dict[str, str]] = {}
        self.locales_dir = os.path.join(os.path.dirname(__file__), 'locales')

        # Crea directory se non esiste
        os.makedirs(self.locales_dir, exist_ok=True)

        # Carica tutte le traduzioni disponibili
        self._load_all_translations()

        logger.info(f"TranslationManager inizializzato con {len(self.translations)} lingue")

    def _load_all_translations(self):
        """Carica tutti i file di traduzione disponibili."""
        if not os.path.exists(self.locales_dir):
            logger.warning(f"Directory locales non trovata: {self.locales_dir}")
            return

        for filename in os.listdir(self.locales_dir):
            if filename.endswith('.json'):
                lang_code = filename[:-5]  # Remove .json
                self._load_translation_file(lang_code)

    def _load_translation_file(self, lang_code: str) -> bool:
        """
        Carica un file di traduzione.

        Args:
            lang_code: Codice lingua (es. 'en', 'it', 'es')

        Returns:
            True se caricato, False altrimenti
        """
        filepath = os.path.join(self.locales_dir, f'{lang_code}.json')

        if not os.path.exists(filepath):
            logger.warning(f"File traduzione non trovato: {filepath}")
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.translations[lang_code] = json.load(f)
                logger.debug(f"Traduzione caricata: {lang_code} ({len(self.translations[lang_code])} stringhe)")
                return True
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Errore caricamento traduzione {lang_code}: {e}")
            return False

    def load_language(self, lang_code: str) -> bool:
        """
        Carica una lingua.

        Args:
            lang_code: Codice lingua (es. 'en', 'it', 'es')

        Returns:
            True se caricata, False altrimenti
        """
        if lang_code not in self.translations:
            # Prova a caricare il file
            if not self._load_translation_file(lang_code):
                logger.warning(f"Lingua non disponibile: {lang_code}")
                return False

        self.current_language = lang_code
        logger.info(f"Lingua caricata: {lang_code}")
        return True

    def translate(self, key: str, default: Optional[str] = None) -> str:
        """
        Traduce una stringa.

        Args:
            key: Chiave traduzione
            default: Valore di default se traduzione non trovata

        Returns:
            Stringa tradotta o default o key
        """
        if self.current_language not in self.translations:
            return default or key

        return self.translations[self.current_language].get(key, default or key)

    def t(self, key: str, default: Optional[str] = None) -> str:
        """
        Alias breve per translate().

        Args:
            key: Chiave traduzione
            default: Valore di default

        Returns:
            Stringa tradotta
        """
        return self.translate(key, default)

    def get_available_languages(self) -> List[str]:
        """
        Ritorna lingue disponibili.

        Returns:
            Lista di codici lingua
        """
        return list(self.translations.keys())

    def get_language_name(self, lang_code: str) -> str:
        """
        Ritorna il nome nativo di una lingua.

        Args:
            lang_code: Codice lingua

        Returns:
            Nome lingua nativo
        """
        names = {
            'en': 'English',
            'it': 'Italiano',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'ja': '日本語',
            'zh': '中文',
            'ko': '한국어'
        }
        return names.get(lang_code, lang_code.upper())
