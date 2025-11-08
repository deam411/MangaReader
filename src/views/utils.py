"""
Utility functions per views.

Contiene funzioni di utilità condivise tra le views.
"""

import re
from src.logger import get_logger

logger = get_logger(__name__)


def sanitize_filename(filename: str, replacement: str = '_') -> str:
    """
    Sanitizza un nome file rimuovendo caratteri pericolosi e riservati.

    Supporta Unicode ma rimuove caratteri di controllo e riservati da filesystem.

    Args:
        filename: Il nome file da sanitizzare
        replacement: Carattere con cui sostituire i caratteri invalidi

    Returns:
        Nome file sanitizzato
    """
    # Rimuovi caratteri riservati Windows/Linux: < > : " / \ | ? * e caratteri di controllo (0x00-0x1F)
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, replacement, filename)
    # Rimuovi punti e spazi finali (problematici su Windows)
    sanitized = sanitized.strip('. ')
    # Se il risultato è vuoto, usa un fallback
    if not sanitized:
        sanitized = 'unnamed'
    return sanitized


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
        cursor.execute('''
            SELECT
                (SELECT COUNT(*) FROM pages) as total_pages,
                COALESCE(
                    (SELECT COUNT(*)
                     FROM pages p
                     JOIN chapters ch ON p.chapter_id = ch.id
                     WHERE ch."order" < (
                         SELECT c2."order" FROM chapters c2
                         WHERE c2.id = (
                             SELECT chapter_id FROM history
                             WHERE user = ?
                             ORDER BY timestamp DESC LIMIT 1
                         )
                     ) OR (
                         ch.id = (SELECT chapter_id FROM history WHERE user = ? ORDER BY timestamp DESC LIMIT 1)
                         AND p.page_number <= (SELECT page_number FROM history WHERE user = ? ORDER BY timestamp DESC LIMIT 1)
                     )
                    ), 0
                ) as read_pages
        ''', (user, user, user))

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
