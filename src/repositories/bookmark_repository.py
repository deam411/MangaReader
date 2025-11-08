"""
Bookmark Repository v0.2.0.

Gestisce operazioni per:
- Bookmarks utente
- Reading history
- Reading progress tracking
"""

from typing import Optional, List, Dict, Any
from .base_repository import BaseRepository
from src.logger import get_logger

logger = get_logger(__name__)


class BookmarkRepository(BaseRepository):
    """
    Repository per bookmarks e reading history.

    Fornisce API pulita per gestire segnalibri e tracciare
    il progresso di lettura senza esporre dettagli del database.
    """

    # ============================================================================
    # BOOKMARKS
    # ============================================================================

    def add_bookmark(
        self,
        chapter_id: int,
        page_number: int,
        name: str,
        user: str = "default"
    ) -> int:
        """
        Aggiunge un bookmark.

        Args:
            chapter_id: ID del capitolo
            page_number: Numero pagina
            name: Nome descrittivo del bookmark
            user: Nome utente (default: "default")

        Returns:
            ID del bookmark creato, -1 se errore

        Example:
            with BookmarkRepository(manga_file) as repo:
                bookmark_id = repo.add_bookmark(
                    chapter_id=1,
                    page_number=15,
                    name="Scena epica"
                )
        """
        try:
            bookmark_id = self.db.bookmarks.add_bookmark(
                chapter_id=chapter_id,
                page_number=page_number,
                name=name,
                user=user
            )
            if bookmark_id > 0:
                logger.info(f"Bookmark created: {name} (ID: {bookmark_id})")
            return bookmark_id
        except Exception as e:
            logger.error(f"Error creating bookmark: {e}")
            return -1

    def get_all_bookmarks(self, user: str = "default") -> List[Dict[str, Any]]:
        """
        Recupera tutti i bookmarks dell'utente.

        Args:
            user: Nome utente (default: "default")

        Returns:
            Lista di dict con info bookmarks (con chapter e volume info)

        Example:
            with BookmarkRepository(manga_file) as repo:
                bookmarks = repo.get_all_bookmarks()
                for bm in bookmarks:
                    print(f"{bm['name']} - {bm['volume_name']}/{bm['chapter_name']} p.{bm['page_number']}")
        """
        try:
            bookmarks = self.db.bookmarks.get_bookmarks(user=user)
            logger.debug(f"Retrieved {len(bookmarks)} bookmarks for user: {user}")
            return bookmarks
        except Exception as e:
            logger.error(f"Error retrieving bookmarks: {e}")
            return []

    def delete_bookmark(self, bookmark_id: int) -> bool:
        """
        Elimina un bookmark.

        Args:
            bookmark_id: ID del bookmark da eliminare

        Returns:
            True se eliminazione riuscita, False altrimenti

        Example:
            with BookmarkRepository(manga_file) as repo:
                success = repo.delete_bookmark(5)
        """
        try:
            success = self.db.bookmarks.delete_bookmark(bookmark_id)
            if success:
                logger.info(f"Bookmark deleted (ID: {bookmark_id})")
            return success
        except Exception as e:
            logger.error(f"Error deleting bookmark: {e}")
            return False

    def update_bookmark_name(self, bookmark_id: int, new_name: str) -> bool:
        """
        Rinomina un bookmark.

        Args:
            bookmark_id: ID del bookmark
            new_name: Nuovo nome

        Returns:
            True se rinominazione riuscita, False altrimenti

        Example:
            with BookmarkRepository(manga_file) as repo:
                success = repo.update_bookmark_name(5, "Nuovo nome")
        """
        try:
            success = self.db.bookmarks.update_bookmark_name(bookmark_id, new_name)
            if success:
                logger.info(f"Bookmark renamed (ID: {bookmark_id}) -> {new_name}")
            return success
        except Exception as e:
            logger.error(f"Error renaming bookmark: {e}")
            return False

    # ============================================================================
    # READING HISTORY
    # ============================================================================

    def save_reading_position(
        self,
        chapter_id: int,
        page_number: int,
        user: str = "default"
    ) -> bool:
        """
        Salva la posizione di lettura corrente.

        Args:
            chapter_id: ID del capitolo
            page_number: Numero della pagina
            user: Nome utente (default: "default")

        Returns:
            True se salvataggio riuscito, False altrimenti

        Example:
            with BookmarkRepository(manga_file) as repo:
                repo.save_reading_position(
                    chapter_id=1,
                    page_number=15
                )
        """
        try:
            success = self.db.history.save_reading_position(
                chapter_id=chapter_id,
                page_number=page_number,
                user=user
            )
            if success:
                logger.debug(f"Saved reading position: chapter {chapter_id}, page {page_number}")
            return success
        except Exception as e:
            logger.error(f"Error saving reading position: {e}")
            return False

    def get_last_reading_position(self, user: str = "default") -> Optional[Dict[str, Any]]:
        """
        Recupera l'ultima posizione di lettura.

        Args:
            user: Nome utente (default: "default")

        Returns:
            Dict con chapter_id, page_number, timestamp, chapter_name, volume_name
            None se non ci sono posizioni salvate

        Example:
            with BookmarkRepository(manga_file) as repo:
                position = repo.get_last_reading_position()
                if position:
                    print(f"Last read: {position['volume_name']}/{position['chapter_name']} p.{position['page_number']}")
        """
        try:
            position = self.db.history.get_last_reading_position(user=user)
            if position:
                logger.debug(f"Retrieved last position: chapter {position['chapter_id']}, page {position['page_number']}")
            return position
        except Exception as e:
            logger.error(f"Error retrieving last position: {e}")
            return None

    def get_reading_progress(self, user: str = "default") -> Optional[Dict[str, Any]]:
        """
        Calcola il progresso di lettura (percentuale).

        Args:
            user: Nome utente (default: "default")

        Returns:
            Dict con total_pages, read_pages, percentage
            None se non ci sono dati

        Example:
            with BookmarkRepository(manga_file) as repo:
                progress = repo.get_reading_progress()
                if progress:
                    print(f"Progress: {progress['read_pages']}/{progress['total_pages']} ({progress['percentage']:.1f}%)")
        """
        try:
            progress = self.db.history.get_reading_progress(user=user)
            if progress:
                logger.debug(f"Reading progress: {progress['percentage']:.1f}%")
            return progress
        except Exception as e:
            logger.error(f"Error calculating progress: {e}")
            return None

    def clear_reading_history(self, user: str = "default") -> bool:
        """
        Cancella la cronologia di lettura.

        Args:
            user: Nome utente (default: "default")

        Returns:
            True se cancellazione riuscita, False altrimenti

        Example:
            with BookmarkRepository(manga_file) as repo:
                success = repo.clear_reading_history()
        """
        try:
            success = self.db.history.clear_reading_history(user=user)
            if success:
                logger.info(f"Reading history cleared for user: {user}")
            return success
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            return False

    # ============================================================================
    # CONVENIENCE METHODS
    # ============================================================================

    def is_reading_in_progress(self, user: str = "default") -> bool:
        """
        Verifica se c'è una lettura in corso (0% < progress < 100%).

        Args:
            user: Nome utente (default: "default")

        Returns:
            True se c'è una lettura in corso, False altrimenti

        Example:
            with BookmarkRepository(manga_file) as repo:
                if repo.is_reading_in_progress():
                    print("Reading in progress...")
        """
        try:
            progress = self.get_reading_progress(user=user)
            if progress:
                percentage = progress['percentage']
                return 0 < percentage < 100
            return False
        except Exception as e:
            logger.error(f"Error checking reading status: {e}")
            return False

    def mark_as_completed(self, user: str = "default") -> bool:
        """
        Marca il manga come completato (salta all'ultima pagina).

        Args:
            user: Nome utente (default: "default")

        Returns:
            True se marcatura riuscita, False altrimenti

        Example:
            with BookmarkRepository(manga_file) as repo:
                repo.mark_as_completed()
        """
        try:
            # Trova l'ultimo capitolo e l'ultima pagina
            from .chapter_repository import ChapterRepository
            chapter_repo = ChapterRepository(self.manga_file)

            volumes = chapter_repo.get_all_volumes()
            if not volumes:
                return False

            last_volume = volumes[-1]
            chapters = chapter_repo.get_chapters_for_volume(last_volume['id'])
            if not chapters:
                return False

            last_chapter = chapters[-1]
            pages = chapter_repo.get_pages_for_chapter(last_chapter['id'])
            if not pages:
                return False

            last_page = pages[-1]

            # Salva posizione sull'ultima pagina
            return self.save_reading_position(
                chapter_id=last_chapter['id'],
                page_number=last_page['page_number'],
                user=user
            )
        except Exception as e:
            logger.error(f"Error marking as completed: {e}")
            return False
