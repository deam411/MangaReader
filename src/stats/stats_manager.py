"""Sistema statistiche lettura."""
from ..logger import get_logger

logger = get_logger(__name__)

class StatsManager:
    """Gestore statistiche lettura."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path
        logger.info("StatsManager inizializzato")

    def get_reading_stats(self):
        """Ritorna statistiche lettura."""
        return {
            "total_manga_read": 0,
            "total_pages_read": 0,
            "total_time_minutes": 0,
            "current_streak_days": 0
        }

    def record_session(self, manga_id, pages_read, duration_seconds):
        """Registra una sessione di lettura."""
        logger.debug(f"Sessione: {manga_id}, {pages_read} pagine, {duration_seconds}s")
