"""
Chapter Repository v0.2.0.

Gestisce operazioni CRUD per struttura manga:
- Volumes
- Chapters
- Pages
- Navigazione e query
"""

from typing import Optional, List, Dict, Any
from .base_repository import BaseRepository
from src.logger import get_logger
from src.utils.security import validate_volume_name, validate_chapter_name, validate_order

logger = get_logger(__name__)


class ChapterRepository(BaseRepository):
    """
    Repository per operazioni su volumes, chapters e pages.

    Fornisce API pulita per navigare e manipolare la struttura
    del manga senza esporre dettagli del database.
    """

    # ============================================================================
    # VOLUMES
    # ============================================================================

    def get_all_volumes(self) -> List[Dict[str, Any]]:
        """
        Recupera tutti i volumi ordinati per order.

        Returns:
            Lista di dict con info volumi

        Example:
            with ChapterRepository(manga_file) as repo:
                volumes = repo.get_all_volumes()
                for vol in volumes:
                    print(f"Volume {vol['order']}: {vol['name']}")
        """
        try:
            volumes = self.db.chapters.get_volumes()
            logger.debug(f"Retrieved {len(volumes)} volumes")
            return volumes
        except Exception as e:
            logger.error(f"Error retrieving volumes: {e}")
            return []

    def get_volume_by_id(self, volume_id: int) -> Optional[Dict[str, Any]]:
        """
        Recupera un volume specifico per ID.

        Args:
            volume_id: ID del volume

        Returns:
            Dict con info volume o None

        Example:
            with ChapterRepository(manga_file) as repo:
                volume = repo.get_volume_by_id(1)
        """
        try:
            volumes = self.get_all_volumes()
            for vol in volumes:
                if vol['id'] == volume_id:
                    return vol
            return None
        except Exception as e:
            logger.error(f"Error retrieving volume {volume_id}: {e}")
            return None

    # ============================================================================
    # CHAPTERS
    # ============================================================================

    def get_chapters_for_volume(self, volume_id: int) -> List[Dict[str, Any]]:
        """
        Recupera tutti i capitoli di un volume.

        Args:
            volume_id: ID del volume

        Returns:
            Lista di dict con info capitoli

        Example:
            with ChapterRepository(manga_file) as repo:
                chapters = repo.get_chapters_for_volume(1)
                for ch in chapters:
                    print(f"Chapter {ch['order']}: {ch['name']}")
        """
        try:
            chapters = self.db.chapters.get_chapters_for_volume(volume_id)
            logger.debug(f"Retrieved {len(chapters)} chapters for volume {volume_id}")
            return chapters
        except Exception as e:
            logger.error(f"Error retrieving chapters for volume {volume_id}: {e}")
            return []

    def get_chapter_by_id(self, chapter_id: int) -> Optional[Dict[str, Any]]:
        """
        Recupera un capitolo specifico per ID.

        Args:
            chapter_id: ID del capitolo

        Returns:
            Dict con info capitolo o None

        Example:
            with ChapterRepository(manga_file) as repo:
                chapter = repo.get_chapter_by_id(1)
                if chapter:
                    print(f"Chapter: {chapter['name']}")
        """
        try:
            # Itera su tutti i volumi e cerca il capitolo
            volumes = self.get_all_volumes()
            for vol in volumes:
                chapters = self.get_chapters_for_volume(vol['id'])
                for ch in chapters:
                    if ch['id'] == chapter_id:
                        return ch
            return None
        except Exception as e:
            logger.error(f"Error retrieving chapter {chapter_id}: {e}")
            return None

    # ============================================================================
    # PAGES
    # ============================================================================

    def get_pages_for_chapter(self, chapter_id: int) -> List[Dict[str, Any]]:
        """
        Recupera tutte le pagine di un capitolo.

        Args:
            chapter_id: ID del capitolo

        Returns:
            Lista di dict con info pagine (ordinate per page_number)

        Example:
            with ChapterRepository(manga_file) as repo:
                pages = repo.get_pages_for_chapter(1)
                print(f"Total pages: {len(pages)}")
        """
        try:
            pages = self.db.chapters.get_pages_for_chapter(chapter_id)
            logger.debug(f"Retrieved {len(pages)} pages for chapter {chapter_id}")
            return pages
        except Exception as e:
            logger.error(f"Error retrieving pages for chapter {chapter_id}: {e}")
            return []

    def get_page_image(self, page_id: int) -> Optional[bytes]:
        """
        Recupera l'immagine di una pagina.

        Args:
            page_id: ID della pagina

        Returns:
            Bytes dell'immagine o None

        Example:
            with ChapterRepository(manga_file) as repo:
                image = repo.get_page_image(1)
                if image:
                    # Mostra immagine...
        """
        try:
            image = self.db.chapters.get_page_image(page_id)
            if image:
                logger.debug(f"Retrieved image for page {page_id}")
            return image
        except Exception as e:
            logger.error(f"Error retrieving page image {page_id}: {e}")
            return None

    def get_total_pages_count(self) -> int:
        """
        Conta il numero totale di pagine nel manga.

        Returns:
            Numero totale di pagine

        Example:
            with ChapterRepository(manga_file) as repo:
                total = repo.get_total_pages_count()
                print(f"This manga has {total} pages")
        """
        try:
            volumes = self.get_all_volumes()
            total = 0
            for vol in volumes:
                chapters = self.get_chapters_for_volume(vol['id'])
                for ch in chapters:
                    pages = self.get_pages_for_chapter(ch['id'])
                    total += len(pages)
            logger.debug(f"Total pages count: {total}")
            return total
        except Exception as e:
            logger.error(f"Error counting total pages: {e}")
            return 0

    # ============================================================================
    # NAVIGATION HELPERS
    # ============================================================================

    def get_next_chapter(self, current_chapter_id: int) -> Optional[Dict[str, Any]]:
        """
        Trova il capitolo successivo nella sequenza.

        Args:
            current_chapter_id: ID del capitolo corrente

        Returns:
            Dict con info capitolo successivo o None se è l'ultimo

        Example:
            with ChapterRepository(manga_file) as repo:
                next_ch = repo.get_next_chapter(current_id)
                if next_ch:
                    # Vai al capitolo successivo...
        """
        try:
            current = self.get_chapter_by_id(current_chapter_id)
            if not current:
                return None

            # Cerca capitolo successivo nello stesso volume
            chapters_in_volume = self.get_chapters_for_volume(current['volume_id'])
            for i, ch in enumerate(chapters_in_volume):
                if ch['id'] == current_chapter_id and i + 1 < len(chapters_in_volume):
                    return chapters_in_volume[i + 1]

            # Se non c'è nel volume corrente, cerca nel prossimo volume
            volumes = self.get_all_volumes()
            for i, vol in enumerate(volumes):
                if vol['id'] == current['volume_id'] and i + 1 < len(volumes):
                    next_volume_chapters = self.get_chapters_for_volume(volumes[i + 1]['id'])
                    if next_volume_chapters:
                        return next_volume_chapters[0]

            return None
        except Exception as e:
            logger.error(f"Error finding next chapter: {e}")
            return None

    def get_previous_chapter(self, current_chapter_id: int) -> Optional[Dict[str, Any]]:
        """
        Trova il capitolo precedente nella sequenza.

        Args:
            current_chapter_id: ID del capitolo corrente

        Returns:
            Dict con info capitolo precedente o None se è il primo

        Example:
            with ChapterRepository(manga_file) as repo:
                prev_ch = repo.get_previous_chapter(current_id)
                if prev_ch:
                    # Vai al capitolo precedente...
        """
        try:
            current = self.get_chapter_by_id(current_chapter_id)
            if not current:
                return None

            # Cerca capitolo precedente nello stesso volume
            chapters_in_volume = self.get_chapters_for_volume(current['volume_id'])
            for i, ch in enumerate(chapters_in_volume):
                if ch['id'] == current_chapter_id and i > 0:
                    return chapters_in_volume[i - 1]

            # Se non c'è nel volume corrente, cerca nel volume precedente
            volumes = self.get_all_volumes()
            for i, vol in enumerate(volumes):
                if vol['id'] == current['volume_id'] and i > 0:
                    prev_volume_chapters = self.get_chapters_for_volume(volumes[i - 1]['id'])
                    if prev_volume_chapters:
                        return prev_volume_chapters[-1]

            return None
        except Exception as e:
            logger.error(f"Error finding previous chapter: {e}")
            return None
