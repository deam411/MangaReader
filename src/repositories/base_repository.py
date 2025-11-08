"""
Base Repository per pattern repository v0.2.0.

Fornisce funzionalità comuni condivise tra tutti i repository:
- Gestione connessione database
- Transazioni
- Error handling
- Logging
"""

from typing import Optional
from src.database import MangaDatabaseManager
from src.logger import get_logger

logger = get_logger(__name__)


class BaseRepository:
    """
    Classe base per tutti i repository.

    Fornisce accesso centralizzato al database manager e
    funzionalità comuni per operazioni CRUD.
    """

    def __init__(self, manga_file: str):
        """
        Inizializza il repository con un file manga.

        Args:
            manga_file: Percorso al file .manga
        """
        self.manga_file = manga_file
        self._db_manager: Optional[MangaDatabaseManager] = None

    @property
    def db(self) -> MangaDatabaseManager:
        """
        Lazy-load database manager.

        Returns:
            Instance del database manager
        """
        if self._db_manager is None:
            self._db_manager = MangaDatabaseManager(self.manga_file)
        return self._db_manager

    def close(self):
        """Chiude la connessione al database se aperta."""
        if self._db_manager is not None:
            # MangaDatabaseManager gestisce internamente la connessione
            self._db_manager = None

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()
        return False
