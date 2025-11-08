"""
Metadata manager per gestione metadati manga.

Gestisce:
- Inserimento metadata (title, author, description, cover, year, tags)
- Aggiornamento metadata
- Recupero metadata
"""
import sqlite3
from typing import Optional, Dict, Any
from .base_manager import BaseManager
from ..logger import get_logger
from ..exceptions import ValidationError
from ..utils.validation import (
    validate_title,
    validate_author,
    validate_description,
    validate_language,
    validate_year,
    validate_tags
)

logger = get_logger(__name__)


class MetadataManager(BaseManager):
    """
    Manager per operazioni CRUD su metadata manga.

    Responsabile di:
    - Inserimento metadata con validazione
    - Aggiornamento metadata
    - Recupero metadata
    """

    def insert_metadata(
        self,
        title: str,
        author: Optional[str] = None,
        description: Optional[str] = None,
        language: Optional[str] = None,
        cover: Optional[bytes] = None,
        year: Optional[int] = None,
        tags: Optional[str] = None
    ) -> bool:
        """
        Inserisce i metadati per il manga con validazione input completa.

        Args:
            title: Titolo manga (required)
            author: Autore manga (optional)
            description: Descrizione/sinossi (optional)
            language: Lingua originale (optional)
            cover: Cover image come BLOB (optional)
            year: Anno pubblicazione (optional)
            tags: Tags comma-separated (optional)

        Returns:
            True in caso di successo, False altrimenti

        Raises:
            ValidationError: Se i metadata non passano la validazione

        Example:
            success = metadata_mgr.insert_metadata(
                title="One Piece",
                author="Eiichiro Oda",
                description="A pirate adventure",
                year=1997,
                tags="Azione, Avventura, Fantasy"
            )
        """
        try:
            # Valida e sanitizza tutti gli input
            title = validate_title(title)
            author = validate_author(author)
            description = validate_description(description)
            language = validate_language(language)
            year = validate_year(year)
            tags = validate_tags(tags)

            logger.debug(f"Inserting metadata for: {title}")

            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO metadata (title, author, description, language, cover, year, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (title, author, description, language, cover, year, tags))

            logger.info(f"Metadata inserted successfully for: {title}")
            return True

        except ValidationError:
            # Re-raise validation errors per gestione upstream
            raise
        except sqlite3.Error as e:
            logger.error(f"Error inserting metadata: {e}")
            return False

    def update_metadata(
        self,
        title: str,
        author: Optional[str] = None,
        description: Optional[str] = None,
        language: Optional[str] = None,
        cover: Optional[bytes] = None,
        year: Optional[int] = None,
        tags: Optional[str] = None
    ) -> bool:
        """
        Aggiorna i metadati per un manga esistente.

        Note: Il title è usato come chiave per identificare il manga.

        Args:
            title: Titolo manga (chiave di ricerca)
            author: Nuovo autore (optional)
            description: Nuova descrizione (optional)
            language: Nuova lingua (optional)
            cover: Nuova cover BLOB (optional)
            year: Nuovo anno (optional)
            tags: Nuovi tags (optional)

        Returns:
            True in caso di successo, False altrimenti

        Example:
            success = metadata_mgr.update_metadata(
                title="One Piece",
                year=1997,
                tags="Azione, Avventura, Fantasy, Shounen"
            )
        """
        try:
            logger.debug(f"Updating metadata for: {title}")

            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    UPDATE metadata SET
                        author = ?,
                        description = ?,
                        language = ?,
                        cover = ?,
                        year = ?,
                        tags = ?
                    WHERE title = ?
                ''', (author, description, language, cover, year, tags, title))

            logger.info(f"Metadata updated successfully for: {title}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error updating metadata for {title}: {e}")
            return False

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Recupera i metadati del manga.

        Note: Ogni file .manga ha solo un record metadata.

        Returns:
            Dizionario con metadata o None se non trovato

        Example:
            metadata = metadata_mgr.get_metadata()
            if metadata:
                print(f"Title: {metadata['title']}")
                print(f"Author: {metadata['author']}")
        """
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    SELECT title, author, description, language, cover, year, tags
                    FROM metadata
                ''')
                metadata = c.fetchone()

                if metadata:
                    # Converti Row in dizionario
                    return dict(metadata)

                return None

        except sqlite3.Error as e:
            logger.error(f"Error retrieving metadata: {e}")
            return None
