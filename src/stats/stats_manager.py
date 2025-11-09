"""Sistema statistiche lettura con persistenza database."""
import sqlite3
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from ..logger import get_logger
from ..paths import get_app_data_dir

logger = get_logger(__name__)

class StatsManager:
    """
    Gestore statistiche lettura con persistenza database.

    Traccia:
    - Sessioni di lettura
    - Pagine lette
    - Tempo di lettura
    - Streak giorni consecutivi
    """

    def __init__(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(get_app_data_dir(), "reading_stats.db")

        self._init_database()
        logger.info(f"StatsManager inizializzato con database: {self.db_path}")

    def _init_database(self):
        """Crea lo schema database per le statistiche."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Tabella reading_sessions
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reading_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        manga_path TEXT NOT NULL,
                        chapter_id INTEGER,
                        pages_read INTEGER NOT NULL,
                        duration_seconds INTEGER NOT NULL,
                        session_date TEXT NOT NULL,
                        timestamp INTEGER DEFAULT (strftime('%s', 'now'))
                    )
                ''')

                # Indici per performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_reading_sessions_date
                    ON reading_sessions(session_date)
                ''')

                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_reading_sessions_manga
                    ON reading_sessions(manga_path)
                ''')

                conn.commit()
                logger.debug("Schema stats database creato")
        except sqlite3.Error as e:
            logger.error(f"Errore creazione database stats: {e}")

    def record_session(self, manga_path: str, pages_read: int, duration_seconds: int,
                       chapter_id: Optional[int] = None) -> bool:
        """
        Registra una sessione di lettura.

        Args:
            manga_path: Path al file .manga
            pages_read: Numero di pagine lette
            duration_seconds: Durata sessione in secondi
            chapter_id: ID del capitolo (opzionale)

        Returns:
            True se registrata, False altrimenti
        """
        try:
            session_date = datetime.now().strftime('%Y-%m-%d')

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO reading_sessions
                    (manga_path, chapter_id, pages_read, duration_seconds, session_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (manga_path, chapter_id, pages_read, duration_seconds, session_date))
                conn.commit()

                logger.debug(f"Sessione registrata: {manga_path}, {pages_read} pagine, {duration_seconds}s")
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore registrazione sessione: {e}")
            return False

    def get_reading_stats(self) -> Dict:
        """
        Ritorna statistiche lettura aggregate.

        Returns:
            Dizionario con statistiche:
            - total_manga_read: Numero manga unici letti
            - total_pages_read: Totale pagine lette
            - total_time_minutes: Tempo totale lettura
            - current_streak_days: Giorni consecutivi lettura
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total manga read (unici)
                cursor.execute('''
                    SELECT COUNT(DISTINCT manga_path) FROM reading_sessions
                ''')
                total_manga = cursor.fetchone()[0] or 0

                # Total pages read
                cursor.execute('''
                    SELECT SUM(pages_read) FROM reading_sessions
                ''')
                total_pages = cursor.fetchone()[0] or 0

                # Total time (in minutes)
                cursor.execute('''
                    SELECT SUM(duration_seconds) FROM reading_sessions
                ''')
                total_seconds = cursor.fetchone()[0] or 0
                total_minutes = total_seconds // 60

                # Current streak
                streak = self._calculate_streak(cursor)

                return {
                    "total_manga_read": total_manga,
                    "total_pages_read": total_pages,
                    "total_time_minutes": total_minutes,
                    "current_streak_days": streak
                }
        except sqlite3.Error as e:
            logger.error(f"Errore recupero statistiche: {e}")
            return {
                "total_manga_read": 0,
                "total_pages_read": 0,
                "total_time_minutes": 0,
                "current_streak_days": 0
            }

    def _calculate_streak(self, cursor) -> int:
        """
        Calcola lo streak di giorni consecutivi di lettura.

        Args:
            cursor: Cursore database

        Returns:
            Numero di giorni consecutivi
        """
        try:
            # Get unique reading dates sorted DESC
            cursor.execute('''
                SELECT DISTINCT session_date
                FROM reading_sessions
                ORDER BY session_date DESC
            ''')
            dates = [row[0] for row in cursor.fetchall()]

            if not dates:
                return 0

            # Check if today or yesterday (streak still active)
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)

            latest_date = datetime.strptime(dates[0], '%Y-%m-%d').date()

            # Streak broken if more than 1 day ago
            if latest_date < yesterday:
                return 0

            # Count consecutive days
            streak = 1
            expected_date = latest_date - timedelta(days=1)

            for date_str in dates[1:]:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if date == expected_date:
                    streak += 1
                    expected_date -= timedelta(days=1)
                else:
                    break

            return streak
        except Exception as e:
            logger.error(f"Errore calcolo streak: {e}")
            return 0

    def get_manga_stats(self, manga_path: str) -> Dict:
        """
        Ritorna statistiche per un manga specifico.

        Args:
            manga_path: Path al file .manga

        Returns:
            Dizionario con statistiche manga
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total sessions
                cursor.execute('''
                    SELECT COUNT(*) FROM reading_sessions
                    WHERE manga_path = ?
                ''', (manga_path,))
                total_sessions = cursor.fetchone()[0] or 0

                # Total pages
                cursor.execute('''
                    SELECT SUM(pages_read) FROM reading_sessions
                    WHERE manga_path = ?
                ''', (manga_path,))
                total_pages = cursor.fetchone()[0] or 0

                # Total time
                cursor.execute('''
                    SELECT SUM(duration_seconds) FROM reading_sessions
                    WHERE manga_path = ?
                ''', (manga_path,))
                total_seconds = cursor.fetchone()[0] or 0

                # Last read date
                cursor.execute('''
                    SELECT session_date FROM reading_sessions
                    WHERE manga_path = ?
                    ORDER BY timestamp DESC LIMIT 1
                ''', (manga_path,))
                result = cursor.fetchone()
                last_read = result[0] if result else None

                return {
                    "total_sessions": total_sessions,
                    "total_pages_read": total_pages,
                    "total_time_seconds": total_seconds,
                    "last_read_date": last_read
                }
        except sqlite3.Error as e:
            logger.error(f"Errore recupero stats manga: {e}")
            return {
                "total_sessions": 0,
                "total_pages_read": 0,
                "total_time_seconds": 0,
                "last_read_date": None
            }

    def get_reading_history(self, days: int = 30) -> List[Dict]:
        """
        Ritorna cronologia lettura degli ultimi N giorni.

        Args:
            days: Numero di giorni da recuperare

        Returns:
            Lista di sessioni
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM reading_sessions
                    WHERE session_date >= ?
                    ORDER BY timestamp DESC
                ''', (cutoff_date,))

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Errore recupero history: {e}")
            return []

    def clear_stats(self) -> bool:
        """
        Cancella tutte le statistiche.

        Returns:
            True se cancellate, False altrimenti
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM reading_sessions')
                conn.commit()

                logger.info("Statistiche cancellate")
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore cancellazione stats: {e}")
            return False
