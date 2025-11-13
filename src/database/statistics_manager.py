"""
Statistics manager per gestione statistiche di lettura.

Gestisce:
- Tracciamento sessioni di lettura
- Calcolo statistiche aggregate (tempo, pagine, velocità)
- Streak di lettura (giorni consecutivi)
- Statistiche giornaliere e storiche
"""
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from .base_manager import BaseManager
from ..logger import get_logger

logger = get_logger(__name__)


class StatisticsManager(BaseManager):
    """
    Manager per statistiche di lettura.

    Responsabile di:
    - Tracking reading sessions (start/stop)
    - Calcolo statistiche aggregate
    - Daily statistics management
    - Reading streak calculation
    - Reading speed analytics
    """

    def __init__(self, db_path: str):
        """
        Inizializza il statistics manager.

        Args:
            db_path: Percorso al file database
        """
        super().__init__(db_path)
        self.current_session_id = None
        self.session_start_page = None

    def start_reading_session(
        self,
        chapter_id: int,
        page_number: int,
        user: str = "default"
    ) -> Optional[int]:
        """
        Inizia una nuova sessione di lettura.

        Args:
            chapter_id: ID del capitolo iniziale
            page_number: Numero pagina iniziale
            user: Nome utente

        Returns:
            ID della sessione creata, None se fallisce
        """
        try:
            start_time = int(time.time() * 1000)  # milliseconds
            logger.debug(f"Starting reading session for user {user}, chapter {chapter_id}")

            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO reading_sessions
                    (user, start_time, start_chapter_id, pages_read)
                    VALUES (?, ?, ?, ?)
                ''', (user, start_time, chapter_id, 0))

                session_id = c.lastrowid
                self.current_session_id = session_id
                self.session_start_page = page_number

                logger.debug(f"Created reading session {session_id}")
                return session_id

        except sqlite3.Error as e:
            logger.error(f"Error starting reading session: {e}")
            return None

    def update_reading_session(
        self,
        session_id: int,
        current_chapter_id: int,
        pages_read: int
    ) -> bool:
        """
        Aggiorna una sessione di lettura in corso.

        Args:
            session_id: ID della sessione
            current_chapter_id: ID capitolo corrente
            pages_read: Numero di pagine lette in questa sessione

        Returns:
            True se l'aggiornamento è riuscito
        """
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    UPDATE reading_sessions
                    SET end_chapter_id = ?, pages_read = ?
                    WHERE id = ?
                ''', (current_chapter_id, pages_read, session_id))

                return True

        except sqlite3.Error as e:
            logger.error(f"Error updating reading session: {e}")
            return False

    def end_reading_session(
        self,
        session_id: int,
        end_chapter_id: int,
        total_pages_read: int,
        user: str = "default"
    ) -> bool:
        """
        Termina una sessione di lettura e aggiorna statistiche giornaliere.

        Args:
            session_id: ID della sessione
            end_chapter_id: ID capitolo finale
            total_pages_read: Totale pagine lette nella sessione
            user: Nome utente

        Returns:
            True se l'operazione è riuscita
        """
        try:
            end_time = int(time.time() * 1000)
            logger.debug(f"Ending reading session {session_id}")

            with self.get_connection() as conn:
                c = conn.cursor()

                # Aggiorna la sessione con end_time
                c.execute('''
                    UPDATE reading_sessions
                    SET end_time = ?, end_chapter_id = ?, pages_read = ?
                    WHERE id = ?
                ''', (end_time, end_chapter_id, total_pages_read, session_id))

                # Recupera dati della sessione per calcolare durata
                c.execute('''
                    SELECT start_time, end_time, pages_read
                    FROM reading_sessions
                    WHERE id = ?
                ''', (session_id,))

                session = c.fetchone()
                if session:
                    start_time = session[0]
                    duration_ms = end_time - start_time
                    duration_minutes = int(duration_ms / 60000)  # Convert to minutes

                    # Aggiorna statistiche giornaliere
                    today = datetime.now().strftime('%Y-%m-%d')
                    self._update_daily_statistics(
                        user, today, duration_minutes, total_pages_read, conn
                    )

                self.current_session_id = None
                self.session_start_page = None
                logger.debug(f"Session {session_id} ended successfully")
                return True

        except sqlite3.Error as e:
            logger.error(f"Error ending reading session: {e}")
            return False

    def _update_daily_statistics(
        self,
        user: str,
        date: str,
        time_minutes: int,
        pages: int,
        conn: sqlite3.Connection
    ) -> None:
        """
        Aggiorna le statistiche giornaliere (uso interno).

        Args:
            user: Nome utente
            date: Data in formato YYYY-MM-DD
            time_minutes: Minuti da aggiungere
            pages: Pagine da aggiungere
            conn: Connessione database attiva
        """
        c = conn.cursor()

        # Controlla se esistono già statistiche per questo giorno
        c.execute('''
            SELECT id, total_time_minutes, total_pages, total_sessions
            FROM daily_statistics
            WHERE user = ? AND date = ?
        ''', (user, date))

        existing = c.fetchone()

        if existing:
            # Aggiorna statistiche esistenti
            new_time = existing[1] + time_minutes
            new_pages = existing[2] + pages
            new_sessions = existing[3] + 1

            c.execute('''
                UPDATE daily_statistics
                SET total_time_minutes = ?, total_pages = ?, total_sessions = ?
                WHERE user = ? AND date = ?
            ''', (new_time, new_pages, new_sessions, user, date))
        else:
            # Crea nuove statistiche per oggi
            c.execute('''
                INSERT INTO daily_statistics
                (user, date, total_time_minutes, total_pages, total_sessions)
                VALUES (?, ?, ?, ?, ?)
            ''', (user, date, time_minutes, pages, 1))

    def get_total_reading_time(self, user: str = "default") -> int:
        """
        Calcola il tempo totale di lettura (in minuti).

        Args:
            user: Nome utente

        Returns:
            Tempo totale in minuti
        """
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    SELECT SUM(total_time_minutes)
                    FROM daily_statistics
                    WHERE user = ?
                ''', (user,))

                result = c.fetchone()
                return result[0] if result and result[0] else 0

        except sqlite3.Error as e:
            logger.error(f"Error calculating total reading time: {e}")
            return 0

    def get_total_pages_read(self, user: str = "default") -> int:
        """
        Calcola il totale di pagine lette.

        Args:
            user: Nome utente

        Returns:
            Numero totale di pagine lette
        """
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    SELECT SUM(total_pages)
                    FROM daily_statistics
                    WHERE user = ?
                ''', (user,))

                result = c.fetchone()
                return result[0] if result and result[0] else 0

        except sqlite3.Error as e:
            logger.error(f"Error calculating total pages read: {e}")
            return 0

    def get_reading_streak(self, user: str = "default") -> int:
        """
        Calcola lo streak corrente (giorni consecutivi di lettura).

        Args:
            user: Nome utente

        Returns:
            Numero di giorni consecutivi
        """
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    SELECT date
                    FROM daily_statistics
                    WHERE user = ?
                    ORDER BY date DESC
                ''', (user,))

                dates = [row[0] for row in c.fetchall()]

                if not dates:
                    return 0

                # Controlla se l'ultimo giorno di lettura è oggi o ieri
                today = datetime.now().date()
                last_read = datetime.strptime(dates[0], '%Y-%m-%d').date()

                days_diff = (today - last_read).days
                if days_diff > 1:
                    # Streak interrotto
                    return 0

                # Calcola streak consecutivo
                streak = 1
                for i in range(len(dates) - 1):
                    current = datetime.strptime(dates[i], '%Y-%m-%d').date()
                    next_date = datetime.strptime(dates[i + 1], '%Y-%m-%d').date()

                    if (current - next_date).days == 1:
                        streak += 1
                    else:
                        break

                return streak

        except sqlite3.Error as e:
            logger.error(f"Error calculating reading streak: {e}")
            return 0

    def get_average_reading_speed(self, user: str = "default") -> float:
        """
        Calcola la velocità media di lettura (pagine/minuto).

        Args:
            user: Nome utente

        Returns:
            Pagine per minuto (media)
        """
        try:
            total_time = self.get_total_reading_time(user)
            total_pages = self.get_total_pages_read(user)

            if total_time > 0:
                return round(total_pages / total_time, 2)
            return 0.0

        except Exception as e:
            logger.error(f"Error calculating average reading speed: {e}")
            return 0.0

    def get_daily_statistics(
        self,
        user: str = "default",
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Recupera statistiche giornaliere per gli ultimi N giorni.

        Args:
            user: Nome utente
            days: Numero di giorni da recuperare

        Returns:
            Lista di dizionari con statistiche giornaliere
        """
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    SELECT date, total_time_minutes, total_pages, total_sessions
                    FROM daily_statistics
                    WHERE user = ?
                    ORDER BY date DESC
                    LIMIT ?
                ''', (user, days))

                results = []
                for row in c.fetchall():
                    results.append({
                        'date': row[0],
                        'time_minutes': row[1],
                        'pages': row[2],
                        'sessions': row[3]
                    })

                return results

        except sqlite3.Error as e:
            logger.error(f"Error getting daily statistics: {e}")
            return []

    def get_statistics_summary(self, user: str = "default") -> Dict[str, Any]:
        """
        Recupera un riassunto completo delle statistiche.

        Args:
            user: Nome utente

        Returns:
            Dizionario con tutte le statistiche principali
        """
        try:
            total_time = self.get_total_reading_time(user)
            total_pages = self.get_total_pages_read(user)
            streak = self.get_reading_streak(user)
            avg_speed = self.get_average_reading_speed(user)

            # Statistiche oggi
            today = datetime.now().strftime('%Y-%m-%d')
            today_stats = self.get_daily_statistics(user, days=1)
            today_data = today_stats[0] if today_stats and today_stats[0]['date'] == today else None

            # Statistiche questa settimana (ultimi 7 giorni)
            week_stats = self.get_daily_statistics(user, days=7)
            week_time = sum(s['time_minutes'] for s in week_stats)
            week_pages = sum(s['pages'] for s in week_stats)

            return {
                'total_time_minutes': total_time,
                'total_time_hours': round(total_time / 60, 1),
                'total_pages': total_pages,
                'current_streak': streak,
                'average_speed': avg_speed,
                'today': {
                    'time_minutes': today_data['time_minutes'] if today_data else 0,
                    'pages': today_data['pages'] if today_data else 0,
                    'sessions': today_data['sessions'] if today_data else 0
                },
                'this_week': {
                    'time_minutes': week_time,
                    'pages': week_pages,
                    'days_read': len(week_stats)
                }
            }

        except Exception as e:
            logger.error(f"Error getting statistics summary: {e}")
            return {
                'total_time_minutes': 0,
                'total_time_hours': 0,
                'total_pages': 0,
                'current_streak': 0,
                'average_speed': 0.0,
                'today': {'time_minutes': 0, 'pages': 0, 'sessions': 0},
                'this_week': {'time_minutes': 0, 'pages': 0, 'days_read': 0}
            }
