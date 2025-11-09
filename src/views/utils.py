"""
Utility functions per views.

Contiene funzioni di utilità condivise tra le views.

v0.2.0: Importa sanitize_filename da security.py centralizzato.
"""

from src.logger import get_logger
# v0.2.0: Import da security centralizzato
from src.utils.security import sanitize_filename  # noqa: F401 (re-export)

logger = get_logger(__name__)

# sanitize_filename è ora importato da src.utils.security
# Mantenuto qui per backward compatibility tramite re-export


def calculate_reading_progress_fast(cursor, user='default'):
    """
    Calcola il progresso di lettura con una query ottimizzata per libreria.
    Versione lightweight senza creare MangaDatabaseManager.

    Args:
        cursor: Cursore SQLite già connesso
        user: Nome utente

    Returns:
        Dict con total_pages, read_pages, percentage o None
    """
    try:
        # Query singola ottimizzata per calcolare progresso
        # FIX: Considera sia volume_id che chapter order per calcolo corretto su multi-volume
        cursor.execute('''
            SELECT
                (SELECT COUNT(*) FROM pages) as total_pages,
                COALESCE(
                    (SELECT COUNT(*)
                     FROM pages p
                     JOIN chapters ch ON p.chapter_id = ch.id
                     JOIN volumes v ON ch.volume_id = v.id
                     WHERE (
                         v."order" < (
                             SELECT v2."order" FROM volumes v2
                             JOIN chapters c2 ON v2.id = c2.volume_id
                             WHERE c2.id = (
                                 SELECT chapter_id FROM history
                                 WHERE user = ?
                                 ORDER BY timestamp DESC LIMIT 1
                             )
                         )
                     ) OR (
                         v."order" = (
                             SELECT v2."order" FROM volumes v2
                             JOIN chapters c2 ON v2.id = c2.volume_id
                             WHERE c2.id = (
                                 SELECT chapter_id FROM history
                                 WHERE user = ?
                                 ORDER BY timestamp DESC LIMIT 1
                             )
                         )
                         AND ch."order" < (
                             SELECT c2."order" FROM chapters c2
                             WHERE c2.id = (
                                 SELECT chapter_id FROM history
                                 WHERE user = ?
                                 ORDER BY timestamp DESC LIMIT 1
                             )
                         )
                     ) OR (
                         ch.id = (SELECT chapter_id FROM history WHERE user = ? ORDER BY timestamp DESC LIMIT 1)
                         AND p.page_number <= (SELECT page_number FROM history WHERE user = ? ORDER BY timestamp DESC LIMIT 1)
                     )
                    ), 0
                ) as read_pages
        ''', (user, user, user, user, user))

        row = cursor.fetchone()
        if row:
            total_pages = row[0]
            read_pages = row[1]

            if total_pages == 0:
                return None

            percentage = (read_pages / total_pages) * 100 if total_pages > 0 else 0.0

            return {
                'total_pages': total_pages,
                'read_pages': read_pages,
                'percentage': percentage
            }
    except Exception as e:
        logger.debug(f"Error calculating fast progress: {e}")
        return None
