"""
Bookmark manager per gestione segnalibri utente.

Gestisce:
- Creazione bookmarks
- Recupero bookmarks con info chapter/volume
- Eliminazione bookmarks
- Rinomina bookmarks
"""
import sqlite3
import time
from typing import List, Dict, Any
from .base_manager import BaseManager
from ..logger import get_logger

logger = get_logger(__name__)


class BookmarkManager(BaseManager):
    """
    Manager per operazioni CRUD su bookmarks utente.

    Responsabile di:
    - Aggiunta bookmark con timestamp
    - Recupero bookmarks con JOIN chapter/volume info
    - Eliminazione bookmark
    - Rinomina bookmark
    """

    def add_bookmark(
        self,
        chapter_id: int,
        page_number: int,
        name: str,
        user: str = "default"
    ) -> int:
        """
        Aggiunge un bookmark alla posizione specificata.

        Args:
            chapter_id: ID del capitolo
            page_number: Numero della pagina
            name: Nome del bookmark
            user: Nome utente (default: "default")

        Returns:
            ID del bookmark creato, -1 in caso di errore

        Example:
            bookmark_id = bookmark_mgr.add_bookmark(
                chapter_id=1,
                page_number=10,
                name="Scena epica",
                user="default"
            )
        """
        try:
            logger.debug(f"Creating bookmark: {name} at chapter {chapter_id}, page {page_number}")

            with self.get_connection() as conn:
                c = conn.cursor()
                timestamp = int(time.time())

                c.execute('''
                    INSERT INTO bookmarks (user, chapter_id, page_number, name, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user, chapter_id, page_number, name, timestamp))

                bookmark_id = c.lastrowid

            logger.info(f"Bookmark created: {name} (ID: {bookmark_id})")
            return bookmark_id

        except sqlite3.Error as e:
            logger.error(f"Error creating bookmark: {e}")
            return -1

    def get_bookmarks(self, user: str = "default") -> List[Dict[str, Any]]:
        """
        Ottiene tutti i bookmarks dell'utente con informazioni capitolo/volume.

        Esegue JOIN tra bookmarks, chapters e volumes per informazioni complete.

        Args:
            user: Nome utente (default: "default")

        Returns:
            Lista di dizionari con info bookmark completo

        Example:
            bookmarks = bookmark_mgr.get_bookmarks(user="default")
            for bm in bookmarks:
                print(f"{bm['name']} - {bm['volume_name']}/{bm['chapter_name']} p.{bm['page_number']}")
        """
        try:
            logger.debug(f"Retrieving bookmarks for user: {user}")

            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    SELECT
                        b.id,
                        b.chapter_id,
                        b.page_number,
                        b.name,
                        b.timestamp,
                        c.name as chapter_name,
                        v.name as volume_name
                    FROM bookmarks b
                    JOIN chapters c ON b.chapter_id = c.id
                    JOIN volumes v ON c.volume_id = v.id
                    WHERE b.user = ?
                    ORDER BY b.timestamp DESC
                ''', (user,))

                bookmarks = []
                for row in c.fetchall():
                    bookmarks.append({
                        'id': row['id'],
                        'chapter_id': row['chapter_id'],
                        'page_number': row['page_number'],
                        'name': row['name'],
                        'timestamp': row['timestamp'],
                        'chapter_name': row['chapter_name'],
                        'volume_name': row['volume_name']
                    })

            logger.debug(f"Retrieved {len(bookmarks)} bookmarks for user: {user}")
            return bookmarks

        except sqlite3.Error as e:
            logger.error(f"Error retrieving bookmarks for user {user}: {e}")
            return []

    def delete_bookmark(self, bookmark_id: int) -> bool:
        """
        Elimina un bookmark.

        Args:
            bookmark_id: ID del bookmark da eliminare

        Returns:
            True se eliminazione riuscita, False altrimenti

        Example:
            success = bookmark_mgr.delete_bookmark(bookmark_id=5)
        """
        try:
            logger.debug(f"Deleting bookmark: {bookmark_id}")

            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('DELETE FROM bookmarks WHERE id = ?', (bookmark_id,))

            logger.info(f"Bookmark deleted (ID: {bookmark_id})")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error deleting bookmark {bookmark_id}: {e}")
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
            success = bookmark_mgr.update_bookmark_name(
                bookmark_id=5,
                new_name="Scena drammatica"
            )
        """
        try:
            logger.debug(f"Renaming bookmark {bookmark_id} to: {new_name}")

            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('UPDATE bookmarks SET name = ? WHERE id = ?', (new_name, bookmark_id))

            logger.info(f"Bookmark renamed (ID: {bookmark_id}) -> {new_name}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error renaming bookmark {bookmark_id}: {e}")
            return False
