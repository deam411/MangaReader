"""Sistema di internazionalizzazione per MangaReader."""
from PyQt5.QtCore import QTranslator, QLocale
from typing import Optional
from ..logger import get_logger

logger = get_logger(__name__)

class TranslationManager:
    """Gestore delle traduzioni."""

    def __init__(self):
        self.translator = QTranslator()
        self.current_language = "it"

    def load_language(self, lang_code: str) -> bool:
        """Carica una lingua."""
        logger.info(f"Caricamento lingua: {lang_code}")
        self.current_language = lang_code
        return True

    def get_available_languages(self):
        """Ritorna le lingue disponibili."""
        return ["it", "en", "es", "fr", "ja"]
