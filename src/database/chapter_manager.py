"""
Chapter manager per gestione volumi, capitoli e pagine.

Gestisce:
- Volumes CRUD (insert, update, delete, get)
- Chapters CRUD (insert, update, delete, get, reorder)
- Pages CRUD (insert, delete, update, swap)
"""
import sqlite3
import os
from io import BytesIO
from typing import Optional, List, Any
from PIL import Image
from .base_manager import BaseManager
from ..logger import get_logger
from ..exceptions import ValidationError
from ..utils.validation import (
    validate_volume_name,
    validate_chapter_name,
    validate_description,
    validate_order
)

logger = get_logger(__name__)


class ChapterManager(BaseManager):
    """
    Manager per operazioni CRUD su volumi, capitoli e pagine.

    Responsabile di:
    - Gestione volumes (CRUD completo)
    - Gestione chapters (CRUD + riordinamento)
    - Gestione pages (CRUD + conversione formati)
    """

    # ============================================================================
    # VOLUME OPERATIONS
    # ============================================================================

    def insert_volume(
        self,
        name: str,
        order: int,
        cover: Optional[bytes] = None
    ) -> Optional[int]:
        """
        Inserisce un nuovo volume con validazione input.

        Args:
            name: Nome del volume
            order: Ordine di visualizzazione
            cover: Cover image come BLOB (optional)

        Returns:
            ID del volume inserito, None in caso di errore

        Raises:
            ValidationError: Se input non validi

        Example:
            volume_id = chapter_mgr.insert_volume(
                name="Volume 1",
                order=1,
                cover=cover_blob
            )
        """
        try:
            # Valida input
            name = validate_volume_name(name)
            order = validate_order(order)

            logger.debug(f"Inserting volume: {name} (order: {order})")

            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO volumes (name, "order", cover)
                    VALUES (?, ?, ?)
                ''', (name, order, cover))
                volume_id = c.lastrowid

            logger.info(f"Volume inserted successfully: {name} (ID: {volume_id})")
            return volume_id

        except ValidationError:
            raise
        except sqlite3.Error as e:
            logger.error(f"Error inserting volume: {e}")
            return None

    def update_volume(
        self,
        volume_id: int,
        name: str,
        order: int,
        cover: Optional[bytes] = None
    ) -> bool:
        """
        Aggiorna un volume esistente.

        Args:
            volume_id: ID del volume da aggiornare
            name: Nuovo nome
            order: Nuovo ordine
            cover: Nuova cover (optional)

        Returns:
            True in caso di successo, False altrimenti
        """
        try:
            logger.debug(f"Updating volume {volume_id}")

            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    UPDATE volumes SET
                        name = ?,
                        "order" = ?,
                        cover = ?
                    WHERE id = ?
                ''', (name, order, cover, volume_id))

            logger.info(f"Volume {volume_id} updated successfully")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error updating volume {volume_id}: {e}")
            return False

    def delete_volume(self, volume_id: int) -> bool:
        """
        Elimina un volume e tutti i suoi capitoli/pagine (cascade delete).

        Args:
            volume_id: ID del volume da eliminare

        Returns:
            True in caso di successo, False altrimenti

        Note:
            Questa operazione elimina anche tutti i capitoli e pagine associate!
        """
        try:
            logger.debug(f"Deleting volume {volume_id} with cascade")

            with self.get_connection() as conn:
                c = conn.cursor()

                # Trova tutti i capitoli nel volume
                c.execute('SELECT id FROM chapters WHERE volume_id = ?', (volume_id,))
                chapter_ids = [row[0] for row in c.fetchall()]

                # Elimina le pagine di ogni capitolo
                for chapter_id in chapter_ids:
                    c.execute('DELETE FROM pages WHERE chapter_id = ?', (chapter_id,))

                # Elimina i capitoli
                c.execute('DELETE FROM chapters WHERE volume_id = ?', (volume_id,))

                # Elimina il volume
                c.execute('DELETE FROM volumes WHERE id = ?', (volume_id,))

            logger.info(f"Volume {volume_id} deleted successfully (cascade)")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error deleting volume {volume_id}: {e}")
            return False

    def get_volumes(self) -> List[Any]:
        """
        Recupera tutti i volumi, ordinati per 'order'.

        Returns:
            Lista di Row objects con i volumi, lista vuota in caso di errore

        Example:
            volumes = chapter_mgr.get_volumes()
            for vol in volumes:
                print(f"{vol['name']} - Order: {vol['order']}")
        """
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('SELECT id, name, "order", cover FROM volumes ORDER BY "order"')
                return c.fetchall()

        except sqlite3.Error as e:
            logger.error(f"Error retrieving volumes: {e}")
            return []

    # ============================================================================
    # CHAPTER OPERATIONS
    # ============================================================================

    def insert_chapter(
        self,
        name: str,
        order: int,
        volume_id: int,
        description: Optional[str] = None
    ) -> Optional[int]:
        """
        Inserisce un nuovo capitolo con validazione input.

        Args:
            name: Nome del capitolo
            order: Ordine di visualizzazione
            volume_id: ID del volume parent
            description: Descrizione/note (optional)

        Returns:
            ID del capitolo inserito, None in caso di errore

        Raises:
            ValidationError: Se input non validi

        Example:
            chapter_id = chapter_mgr.insert_chapter(
                name="Capitolo 1",
                order=1,
                volume_id=volume_id,
                description="Il primo capitolo"
            )
        """
        try:
            # Valida input
            name = validate_chapter_name(name)
            order = validate_order(order)
            description = validate_description(description)

            logger.debug(f"Inserting chapter: {name} (order: {order}) in volume {volume_id}")

            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO chapters (name, "order", description, volume_id)
                    VALUES (?, ?, ?, ?)
                ''', (name, order, description, volume_id))
                chapter_id = c.lastrowid

            logger.info(f"Chapter inserted successfully: {name} (ID: {chapter_id})")
            return chapter_id

        except ValidationError:
            raise
        except sqlite3.Error as e:
            logger.error(f"Error inserting chapter: {e}")
            return None

    def get_chapters_for_volume(self, volume_id: int) -> List[Any]:
        """
        Recupera tutti i capitoli per un dato volume, ordinati per 'order'.

        Args:
            volume_id: ID del volume

        Returns:
            Lista di Row objects con i capitoli
        """
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    SELECT id, name, "order", description
                    FROM chapters
                    WHERE volume_id = ?
                    ORDER BY "order"
                ''', (volume_id,))
                return c.fetchall()

        except sqlite3.Error as e:
            logger.error(f"Error retrieving chapters for volume {volume_id}: {e}")
            return []

    def get_all_chapters(self) -> List[Any]:
        """
        Recupera tutti i capitoli del manga, ordinati per 'order'.

        Returns:
            Lista di Row objects con tutti i capitoli
        """
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('SELECT id, name, "order", description FROM chapters ORDER BY "order"')
                return c.fetchall()

        except sqlite3.Error as e:
            logger.error(f"Error retrieving all chapters: {e}")
            return []

    def delete_chapter_and_pages(self, chapter_id: int) -> bool:
        """
        Elimina un capitolo e tutte le sue pagine (cascade delete).

        Args:
            chapter_id: ID del capitolo da eliminare

        Returns:
            True in caso di successo, False altrimenti

        Note:
            Questa operazione elimina anche tutte le pagine associate!
        """
        try:
            logger.debug(f"Deleting chapter {chapter_id} with pages")

            with self.get_connection() as conn:
                c = conn.cursor()
                # Prima elimina le pagine
                c.execute('DELETE FROM pages WHERE chapter_id = ?', (chapter_id,))
                # Poi elimina il capitolo
                c.execute('DELETE FROM chapters WHERE id = ?', (chapter_id,))

            logger.info(f"Chapter {chapter_id} deleted successfully with pages")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error deleting chapter {chapter_id}: {e}")
            return False

    def update_chapter_name(self, chapter_id: int, new_name: str) -> bool:
        """
        Rinomina un capitolo.

        Args:
            chapter_id: ID del capitolo
            new_name: Nuovo nome

        Returns:
            True in caso di successo, False altrimenti
        """
        try:
            logger.debug(f"Renaming chapter {chapter_id} to: {new_name}")

            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('UPDATE chapters SET name = ? WHERE id = ?', (new_name, chapter_id))

            logger.info(f"Chapter {chapter_id} renamed successfully")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error renaming chapter {chapter_id}: {e}")
            return False

    def update_chapters_order(self, chapter_ids: List[int]) -> bool:
        """
        Aggiorna l'ordine dei capitoli.

        Args:
            chapter_ids: Lista di ID capitoli nell'ordine desiderato

        Returns:
            True in caso di successo, False altrimenti

        Example:
            # Riordina i capitoli: [3, 1, 2]
            success = chapter_mgr.update_chapters_order([3, 1, 2])
        """
        try:
            logger.debug(f"Reordering {len(chapter_ids)} chapters")

            with self.get_connection() as conn:
                c = conn.cursor()
                for index, chapter_id in enumerate(chapter_ids):
                    c.execute('UPDATE chapters SET "order" = ? WHERE id = ?', (index + 1, chapter_id))

            logger.info(f"Chapters reordered successfully")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error reordering chapters: {e}")
            return False

    # ============================================================================
    # PAGE OPERATIONS
    # ============================================================================

    def get_pages_for_chapter(self, chapter_id: int) -> List[Any]:
        """
        Recupera tutte le pagine per un dato capitolo, ordinate per page_number.

        Args:
            chapter_id: ID del capitolo

        Returns:
            Lista di Row objects con le pagine (page_number, image_data)
        """
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    SELECT page_number, image_data
                    FROM pages
                    WHERE chapter_id = ?
                    ORDER BY page_number
                ''', (chapter_id,))
                return c.fetchall()

        except sqlite3.Error as e:
            logger.error(f"Error retrieving pages for chapter {chapter_id}: {e}")
            return []

    def insert_page(self, chapter_id: int, page_number: int, image_path: str) -> bool:
        """
        Inserisce una nuova pagina in un capitolo.

        Supporta conversione automatica formati:
        - .webp, .jfif → PNG (se trasparenza) o JPEG (quality 95)
        - Altri formati → salvati direttamente

        Args:
            chapter_id: ID del capitolo
            page_number: Numero pagina
            image_path: Percorso al file immagine

        Returns:
            True in caso di successo, False altrimenti

        Example:
            success = chapter_mgr.insert_page(
                chapter_id=1,
                page_number=1,
                image_path="/path/to/page001.webp"
            )
        """
        try:
            logger.debug(f"Inserting page {page_number} for chapter {chapter_id}")

            # Controlla se il file è webp o jfif e convertilo
            file_ext = os.path.splitext(image_path)[1].lower()
            if file_ext in ['.webp', '.jfif']:
                # Converti usando Pillow
                img = Image.open(image_path)

                # Converti in RGB se necessario (per PNG con trasparenza)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Mantieni trasparenza se presente → PNG
                    buffer = BytesIO()
                    img.save(buffer, format='PNG')
                    image_data = buffer.getvalue()
                else:
                    # Converti in JPEG per immagini senza trasparenza (più efficiente)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=95)
                    image_data = buffer.getvalue()
            else:
                # Formati standard, leggi direttamente
                with open(image_path, 'rb') as f:
                    image_data = f.read()

            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO pages (chapter_id, page_number, image_data)
                    VALUES (?, ?, ?)
                ''', (chapter_id, page_number, image_data))

            logger.info(f"Page {page_number} inserted successfully for chapter {chapter_id}")
            return True

        except (sqlite3.Error, IOError, Exception) as e:
            logger.error(f"Error inserting page {page_number} for chapter {chapter_id}: {e}")
            return False

    def delete_page(self, chapter_id: int, page_number: int) -> bool:
        """
        Elimina una pagina da un capitolo.

        Args:
            chapter_id: ID del capitolo
            page_number: Numero pagina da eliminare

        Returns:
            True in caso di successo, False altrimenti
        """
        try:
            logger.debug(f"Deleting page {page_number} from chapter {chapter_id}")

            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    DELETE FROM pages
                    WHERE chapter_id = ? AND page_number = ?
                ''', (chapter_id, page_number))

            logger.info(f"Page {page_number} deleted from chapter {chapter_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error deleting page {page_number} from chapter {chapter_id}: {e}")
            return False

    def update_page_order(self, chapter_id: int, ordered_pages_data: List[bytes]) -> bool:
        """
        Aggiorna l'ordine delle pagine per un capitolo.

        Cancella tutte le pagine esistenti e le reinserisce nel nuovo ordine.

        Args:
            chapter_id: ID del capitolo
            ordered_pages_data: Lista di BLOB immagini nel nuovo ordine

        Returns:
            True in caso di successo, False altrimenti

        Example:
            # Riordina pagine: [page3_data, page1_data, page2_data]
            success = chapter_mgr.update_page_order(
                chapter_id=1,
                ordered_pages_data=[img3, img1, img2]
            )
        """
        try:
            logger.debug(f"Reordering {len(ordered_pages_data)} pages for chapter {chapter_id}")

            with self.get_connection() as conn:
                c = conn.cursor()

                # Cancella tutte le pagine esistenti
                c.execute('DELETE FROM pages WHERE chapter_id = ?', (chapter_id,))

                # Inserisce le pagine nel nuovo ordine
                for index, image_data in enumerate(ordered_pages_data):
                    c.execute('''
                        INSERT INTO pages (chapter_id, page_number, image_data)
                        VALUES (?, ?, ?)
                    ''', (chapter_id, index + 1, image_data))

            logger.info(f"Pages reordered successfully for chapter {chapter_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error reordering pages for chapter {chapter_id}: {e}")
            return False

    def swap_page_order(self, chapter_id: int, page_number1: int, page_number2: int) -> bool:
        """
        Scambia l'ordine di due pagine.

        Args:
            chapter_id: ID del capitolo
            page_number1: Numero prima pagina
            page_number2: Numero seconda pagina

        Returns:
            True in caso di successo, False altrimenti

        Example:
            # Scambia pagina 1 con pagina 3
            success = chapter_mgr.swap_page_order(
                chapter_id=1,
                page_number1=1,
                page_number2=3
            )
        """
        try:
            logger.debug(f"Swapping pages {page_number1} and {page_number2} in chapter {chapter_id}")

            with self.get_connection() as conn:
                c = conn.cursor()

                # Ottieni i dati delle due pagine
                c.execute('''
                    SELECT image_data FROM pages
                    WHERE chapter_id = ? AND page_number = ?
                ''', (chapter_id, page_number1))
                page1_data = c.fetchone()[0]

                c.execute('''
                    SELECT image_data FROM pages
                    WHERE chapter_id = ? AND page_number = ?
                ''', (chapter_id, page_number2))
                page2_data = c.fetchone()[0]

                # Scambia i dati
                c.execute('''
                    UPDATE pages SET image_data = ?
                    WHERE chapter_id = ? AND page_number = ?
                ''', (page2_data, chapter_id, page_number1))

                c.execute('''
                    UPDATE pages SET image_data = ?
                    WHERE chapter_id = ? AND page_number = ?
                ''', (page1_data, chapter_id, page_number2))

            logger.info(f"Pages {page_number1} and {page_number2} swapped successfully")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error swapping pages in chapter {chapter_id}: {e}")
            return False
