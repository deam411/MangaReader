"""
Manga Repository v0.2.0.

Gestisce operazioni CRUD per metadata manga:
- Metadata (titolo, autore, descrizione, anno, lingua, tags)
- Cover image
- Query e filtri
"""

from typing import Optional, Dict, Any
from .base_repository import BaseRepository
from src.logger import get_logger
from src.utils.security import (
    validate_title, validate_author, validate_description,
    validate_language, validate_year, validate_tags
)

logger = get_logger(__name__)


class MangaRepository(BaseRepository):
    """
    Repository per operazioni su metadata manga.

    Fornisce API pulita per CRUD metadata senza esporre
    dettagli implementativi del database.
    """

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Recupera i metadata del manga.

        Returns:
            Dict con metadata o None se non trovato

        Example:
            with MangaRepository(manga_file) as repo:
                metadata = repo.get_metadata()
                if metadata:
                    print(f"Title: {metadata['title']}")
        """
        try:
            metadata = self.db.metadata.get_metadata()
            logger.debug(f"Retrieved metadata for: {self.manga_file}")
            return metadata
        except Exception as e:
            logger.error(f"Error retrieving metadata: {e}")
            return None

    def update_metadata(
        self,
        title: Optional[str] = None,
        author: Optional[str] = None,
        description: Optional[str] = None,
        language: Optional[str] = None,
        year: Optional[int] = None,
        tags: Optional[str] = None
    ) -> bool:
        """
        Aggiorna i metadata del manga.

        Solo i campi specificati vengono aggiornati (partial update).
        Applica validazione security prima dell'update.

        Args:
            title: Nuovo titolo (opzionale)
            author: Nuovo autore (opzionale)
            description: Nuova descrizione (opzionale)
            language: Nuova lingua (opzionale)
            year: Nuovo anno (opzionale)
            tags: Nuovi tags (opzionale)

        Returns:
            True se update riuscito, False altrimenti

        Example:
            with MangaRepository(manga_file) as repo:
                success = repo.update_metadata(
                    title="New Title",
                    author="New Author"
                )
        """
        try:
            # Validazione security
            if title is not None:
                title = validate_title(title)
            if author is not None:
                author = validate_author(author)
            if description is not None:
                description = validate_description(description)
            if language is not None:
                language = validate_language(language)
            if year is not None:
                year = validate_year(year)
            if tags is not None:
                tags = validate_tags(tags)

            # Update database
            success = self.db.metadata.update_metadata(
                title=title,
                author=author,
                description=description,
                language=language,
                year=year,
                tags=tags
            )

            if success:
                logger.info(f"Updated metadata for: {self.manga_file}")
            return success

        except Exception as e:
            logger.error(f"Error updating metadata: {e}")
            return False

    def get_cover_image(self) -> Optional[bytes]:
        """
        Recupera l'immagine di copertina del manga.

        Returns:
            Bytes dell'immagine o None se non presente

        Example:
            with MangaRepository(manga_file) as repo:
                cover = repo.get_cover_image()
                if cover:
                    # Mostra cover...
        """
        try:
            cover = self.db.metadata.get_cover_image()
            if cover:
                logger.debug(f"Retrieved cover image for: {self.manga_file}")
            return cover
        except Exception as e:
            logger.error(f"Error retrieving cover: {e}")
            return None

    def set_cover_image(self, image_data: bytes) -> bool:
        """
        Imposta l'immagine di copertina del manga.

        Args:
            image_data: Bytes dell'immagine

        Returns:
            True se impostazione riuscita, False altrimenti

        Example:
            with MangaRepository(manga_file) as repo:
                with open("cover.jpg", "rb") as f:
                    image_data = f.read()
                repo.set_cover_image(image_data)
        """
        try:
            success = self.db.metadata.set_cover_image(image_data)
            if success:
                logger.info(f"Updated cover image for: {self.manga_file}")
            return success
        except Exception as e:
            logger.error(f"Error setting cover: {e}")
            return False

    def get_tags_list(self) -> list[str]:
        """
        Recupera la lista di tags come array.

        Returns:
            Lista di tags (vuota se nessun tag)

        Example:
            with MangaRepository(manga_file) as repo:
                tags = repo.get_tags_list()
                # ['Action', 'Adventure', 'Fantasy']
        """
        try:
            metadata = self.get_metadata()
            if metadata and metadata.get('tags'):
                tags = [t.strip() for t in metadata['tags'].split(',') if t.strip()]
                return tags
            return []
        except Exception as e:
            logger.error(f"Error parsing tags: {e}")
            return []
