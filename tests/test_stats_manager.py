"""
Test suite completa per lo Stats Manager (v0.3.0).

Verifica funzionalità di tracciamento sessioni, calcolo streak e statistiche.
"""
import pytest
import os
import tempfile
import sqlite3
from datetime import datetime, timedelta
from src.stats.stats_manager import StatsManager


class TestStatsManager:
    """Test suite per Stats Manager."""

    @pytest.fixture
    def temp_stats_db(self, monkeypatch, tmp_path):
        """Crea un database stats temporaneo per i test."""
        db_path = tmp_path / "test_reading_stats.db"

        # Monkey patch get_app_data_dir per usare temp directory
        def mock_get_app_data_dir():
            return str(tmp_path)

        monkeypatch.setattr("src.stats.stats_manager.get_app_data_dir",
                           mock_get_app_data_dir)

        # Pass explicit db_path to ensure manager uses the test database
        manager = StatsManager(str(db_path))
        yield manager, str(db_path)

        # Cleanup
        manager.close()

    def test_database_initialization(self, temp_stats_db):
        """Test creazione e inizializzazione database."""
        manager, db_path = temp_stats_db

        assert os.path.exists(db_path)

        # Verifica schema database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Verifica tabella reading_sessions
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='reading_sessions'
            """)
            assert cursor.fetchone() is not None

            # Verifica colonne
            cursor.execute("PRAGMA table_info(reading_sessions)")
            columns = [row[1] for row in cursor.fetchall()]

            assert 'id' in columns
            assert 'manga_path' in columns
            assert 'chapter_id' in columns
            assert 'pages_read' in columns
            assert 'duration_seconds' in columns
            assert 'session_date' in columns
            assert 'timestamp' in columns

    def test_record_session_success(self, temp_stats_db):
        """Test registrazione sessione di lettura."""
        manager, _ = temp_stats_db

        result = manager.record_session(
            manga_path="/manga/naruto.manga",
            pages_read=10,
            duration_seconds=600,
            chapter_id=1
        )

        assert result is True

        # Verifica sessione salvata
        stats = manager.get_total_stats()
        assert stats['total_pages'] == 10
        assert stats['total_time_seconds'] == 600
        assert stats['total_sessions'] == 1

    def test_record_multiple_sessions(self, temp_stats_db):
        """Test registrazione multiple sessioni."""
        manager, _ = temp_stats_db

        # Registra 3 sessioni
        manager.record_session("/manga/naruto.manga", 10, 300, 1)
        manager.record_session("/manga/onepiece.manga", 15, 450, 2)
        manager.record_session("/manga/naruto.manga", 5, 150, 1)

        stats = manager.get_total_stats()
        assert stats['total_pages'] == 30  # 10 + 15 + 5
        assert stats['total_time_seconds'] == 900  # 300 + 450 + 150
        assert stats['total_sessions'] == 3

    def test_record_session_without_chapter(self, temp_stats_db):
        """Test registrazione sessione senza chapter_id specificato."""
        manager, _ = temp_stats_db

        result = manager.record_session(
            manga_path="/manga/test.manga",
            pages_read=20,
            duration_seconds=1200
        )

        assert result is True

        stats = manager.get_total_stats()
        assert stats['total_pages'] == 20

    def test_get_manga_stats_specific(self, temp_stats_db):
        """Test statistiche per manga specifico."""
        manager, _ = temp_stats_db

        # Registra sessioni per diversi manga
        manager.record_session("/manga/naruto.manga", 10, 300, 1)
        manager.record_session("/manga/naruto.manga", 15, 450, 2)
        manager.record_session("/manga/onepiece.manga", 20, 600, 1)

        # Verifica stats per Naruto
        naruto_stats = manager.get_manga_stats("/manga/naruto.manga")
        assert naruto_stats['total_pages'] == 25  # 10 + 15
        assert naruto_stats['total_time_seconds'] == 750  # 300 + 450
        assert naruto_stats['total_sessions'] == 2

        # Verifica stats per One Piece
        op_stats = manager.get_manga_stats("/manga/onepiece.manga")
        assert op_stats['total_pages'] == 20
        assert op_stats['total_time_seconds'] == 600
        assert op_stats['total_sessions'] == 1

    def test_get_manga_stats_nonexistent(self, temp_stats_db):
        """Test statistiche per manga senza sessioni."""
        manager, _ = temp_stats_db

        stats = manager.get_manga_stats("/manga/nonexistent.manga")

        assert stats['total_pages'] == 0
        assert stats['total_time_seconds'] == 0
        assert stats['total_sessions'] == 0

    def test_streak_calculation_single_day(self, temp_stats_db):
        """Test calcolo streak con una sola giornata di lettura."""
        manager, db_path = temp_stats_db

        # Registra sessione oggi
        manager.record_session("/manga/test.manga", 10, 300)

        streak = manager.get_reading_streak()
        assert streak == 1

    def test_streak_calculation_consecutive_days(self, temp_stats_db):
        """Test calcolo streak con giorni consecutivi."""
        manager, db_path = temp_stats_db

        # Inserisci manualmente sessioni per giorni consecutivi
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            today = datetime.now()

            for i in range(5):
                date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO reading_sessions
                    (manga_path, pages_read, duration_seconds, session_date)
                    VALUES (?, ?, ?, ?)
                """, ("/manga/test.manga", 10, 300, date))

            conn.commit()

        streak = manager.get_reading_streak()
        assert streak == 5

    def test_streak_calculation_broken_streak(self, temp_stats_db):
        """Test calcolo streak con streak interrotto."""
        manager, db_path = temp_stats_db

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            today = datetime.now()

            # Leggi oggi
            cursor.execute("""
                INSERT INTO reading_sessions
                (manga_path, pages_read, duration_seconds, session_date)
                VALUES (?, ?, ?, ?)
            """, ("/manga/test.manga", 10, 300, today.strftime('%Y-%m-%d')))

            # Leggi ieri
            yesterday = (today - timedelta(days=1)).strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO reading_sessions
                (manga_path, pages_read, duration_seconds, session_date)
                VALUES (?, ?, ?, ?)
            """, ("/manga/test.manga", 10, 300, yesterday))

            # SALTA un giorno

            # Leggi 3 giorni fa
            three_days_ago = (today - timedelta(days=3)).strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO reading_sessions
                (manga_path, pages_read, duration_seconds, session_date)
                VALUES (?, ?, ?, ?)
            """, ("/manga/test.manga", 10, 300, three_days_ago))

            conn.commit()

        # Streak dovrebbe essere 2 (oggi + ieri), poi si interrompe
        streak = manager.get_reading_streak()
        assert streak == 2

    def test_streak_calculation_no_sessions(self, temp_stats_db):
        """Test streak senza sessioni registrate."""
        manager, _ = temp_stats_db

        streak = manager.get_reading_streak()
        assert streak == 0

    def test_streak_only_old_sessions(self, temp_stats_db):
        """Test streak quando ci sono solo sessioni vecchie (streak = 0)."""
        manager, db_path = temp_stats_db

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Sessione di 5 giorni fa (non consecutiva fino a oggi)
            old_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO reading_sessions
                (manga_path, pages_read, duration_seconds, session_date)
                VALUES (?, ?, ?, ?)
            """, ("/manga/test.manga", 10, 300, old_date))

            conn.commit()

        streak = manager.get_reading_streak()
        assert streak == 0  # Nessuna lettura recente consecutiva

    def test_get_recent_sessions(self, temp_stats_db):
        """Test recupero sessioni recenti."""
        manager, _ = temp_stats_db

        # Registra diverse sessioni
        manager.record_session("/manga/naruto.manga", 10, 300, 1)
        manager.record_session("/manga/onepiece.manga", 15, 450, 2)
        manager.record_session("/manga/bleach.manga", 20, 600, 3)

        # Recupera ultime 2 sessioni
        recent = manager.get_recent_sessions(limit=2)

        assert len(recent) == 2
        # Le più recenti sono le ultime inserite
        assert recent[0]['manga_path'] == "/manga/bleach.manga"
        assert recent[1]['manga_path'] == "/manga/onepiece.manga"

    def test_get_recent_sessions_limit(self, temp_stats_db):
        """Test limite recupero sessioni recenti."""
        manager, _ = temp_stats_db

        # Registra 10 sessioni
        for i in range(10):
            manager.record_session(f"/manga/manga{i}.manga", 5, 100)

        # Richiedi solo 3
        recent = manager.get_recent_sessions(limit=3)
        assert len(recent) == 3

        # Richiedi tutte
        all_recent = manager.get_recent_sessions(limit=100)
        assert len(all_recent) == 10

    def test_get_sessions_by_date_range(self, temp_stats_db):
        """Test recupero sessioni per range di date."""
        manager, db_path = temp_stats_db

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            today = datetime.now()

            # Sessioni in giorni diversi
            for i in range(7):
                date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO reading_sessions
                    (manga_path, pages_read, duration_seconds, session_date)
                    VALUES (?, ?, ?, ?)
                """, (f"/manga/day{i}.manga", 10, 300, date))

            conn.commit()

        # Recupera sessioni ultimi 3 giorni
        start_date = (today - timedelta(days=2)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')

        sessions = manager.get_sessions_by_date_range(start_date, end_date)

        # Dovrebbe includere oggi, ieri e l'altro ieri = 3 sessioni
        assert len(sessions) == 3

    def test_get_total_stats_empty(self, temp_stats_db):
        """Test statistiche totali con database vuoto."""
        manager, _ = temp_stats_db

        stats = manager.get_total_stats()

        assert stats['total_pages'] == 0
        assert stats['total_time_seconds'] == 0
        assert stats['total_sessions'] == 0

    def test_average_pages_per_session(self, temp_stats_db):
        """Test calcolo media pagine per sessione."""
        manager, _ = temp_stats_db

        # Registra sessioni con pagine diverse
        manager.record_session("/manga/test.manga", 10, 300)
        manager.record_session("/manga/test.manga", 20, 600)
        manager.record_session("/manga/test.manga", 30, 900)

        stats = manager.get_total_stats()

        # Media: (10 + 20 + 30) / 3 = 20
        avg_pages = stats['total_pages'] / stats['total_sessions']
        assert avg_pages == pytest.approx(20.0)

    def test_delete_old_sessions(self, temp_stats_db):
        """Test eliminazione sessioni vecchie."""
        manager, db_path = temp_stats_db

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            today = datetime.now()

            # Sessione recente
            cursor.execute("""
                INSERT INTO reading_sessions
                (manga_path, pages_read, duration_seconds, session_date)
                VALUES (?, ?, ?, ?)
            """, ("/manga/recent.manga", 10, 300, today.strftime('%Y-%m-%d')))

            # Sessione molto vecchia (1 anno fa)
            old_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO reading_sessions
                (manga_path, pages_read, duration_seconds, session_date)
                VALUES (?, ?, ?, ?)
            """, ("/manga/old.manga", 10, 300, old_date))

            conn.commit()

        # Elimina sessioni più vecchie di 180 giorni
        cutoff_date = (today - timedelta(days=180)).strftime('%Y-%m-%d')
        result = manager.delete_sessions_before(cutoff_date)

        assert result is True

        # Verifica solo la sessione recente rimane
        stats = manager.get_total_stats()
        assert stats['total_sessions'] == 1

        recent = manager.get_recent_sessions(limit=10)
        assert len(recent) == 1
        assert recent[0]['manga_path'] == "/manga/recent.manga"

    def test_get_most_read_manga(self, temp_stats_db):
        """Test recupero manga più letti."""
        manager, _ = temp_stats_db

        # Leggi diversi manga con quantità diverse
        manager.record_session("/manga/naruto.manga", 100, 3000)
        manager.record_session("/manga/naruto.manga", 50, 1500)

        manager.record_session("/manga/onepiece.manga", 200, 6000)
        manager.record_session("/manga/onepiece.manga", 100, 3000)

        manager.record_session("/manga/bleach.manga", 30, 900)

        # Recupera top 3
        top_manga = manager.get_most_read_manga(limit=3)

        assert len(top_manga) == 3

        # One Piece dovrebbe essere primo (300 pagine totali)
        assert top_manga[0]['manga_path'] == "/manga/onepiece.manga"
        assert top_manga[0]['total_pages'] == 300

        # Naruto secondo (150 pagine)
        assert top_manga[1]['manga_path'] == "/manga/naruto.manga"
        assert top_manga[1]['total_pages'] == 150

        # Bleach terzo (30 pagine)
        assert top_manga[2]['manga_path'] == "/manga/bleach.manga"
        assert top_manga[2]['total_pages'] == 30

    def test_session_timestamp_auto_generation(self, temp_stats_db):
        """Test che timestamp venga generato automaticamente."""
        manager, db_path = temp_stats_db

        manager.record_session("/manga/test.manga", 10, 300)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp FROM reading_sessions")
            timestamp = cursor.fetchone()[0]

            assert timestamp is not None
            # Verifica formato timestamp (stored as Unix timestamp integer)
            datetime.fromtimestamp(timestamp)  # Dovrebbe non lanciare eccezione

    def test_multiple_sessions_same_day(self, temp_stats_db):
        """Test multiple sessioni nello stesso giorno (streak = 1)."""
        manager, _ = temp_stats_db

        # Registra 3 sessioni oggi
        manager.record_session("/manga/test.manga", 10, 300)
        manager.record_session("/manga/test.manga", 15, 450)
        manager.record_session("/manga/test.manga", 20, 600)

        streak = manager.get_reading_streak()
        assert streak == 1  # Conta come un solo giorno

        stats = manager.get_total_stats()
        assert stats['total_sessions'] == 3  # Ma 3 sessioni totali

    def test_persistence_across_instances(self, temp_stats_db):
        """Test persistenza dati tra diverse istanze del manager."""
        manager1, db_path = temp_stats_db

        # Registra sessione con prima istanza
        manager1.record_session("/manga/test.manga", 50, 1500, 1)
        manager1.close()

        # Crea seconda istanza
        from src.stats.stats_manager import StatsManager
        import importlib
        import sys

        if 'src.stats.stats_manager' in sys.modules:
            importlib.reload(sys.modules['src.stats.stats_manager'])

        manager2 = StatsManager()
        manager2.db_path = db_path
        manager2._init_database()

        # Verifica dati persistiti
        stats = manager2.get_total_stats()
        assert stats['total_pages'] == 50
        assert stats['total_time_seconds'] == 1500
        assert stats['total_sessions'] == 1

        manager2.close()

    def test_concurrent_sessions_different_manga(self, temp_stats_db):
        """Test registrazione sessioni per manga diversi in parallelo."""
        manager, _ = temp_stats_db

        manga_list = [
            ("/manga/naruto.manga", 10, 300),
            ("/manga/onepiece.manga", 15, 450),
            ("/manga/bleach.manga", 20, 600),
            ("/manga/dragonball.manga", 25, 750),
        ]

        for manga_path, pages, duration in manga_list:
            manager.record_session(manga_path, pages, duration)

        # Verifica tutte registrate correttamente
        stats = manager.get_total_stats()
        assert stats['total_sessions'] == 4
        assert stats['total_pages'] == 70  # 10+15+20+25

    def test_zero_pages_session(self, temp_stats_db):
        """Test sessione con 0 pagine lette (caso edge)."""
        manager, _ = temp_stats_db

        # Potrebbe accadere se l'utente apre e chiude subito
        result = manager.record_session("/manga/test.manga", 0, 5)
        assert result is True

        stats = manager.get_total_stats()
        assert stats['total_pages'] == 0
        assert stats['total_sessions'] == 1

    def test_long_duration_session(self, temp_stats_db):
        """Test sessione con durata molto lunga."""
        manager, _ = temp_stats_db

        # Sessione di 3 ore (10800 secondi)
        manager.record_session("/manga/test.manga", 200, 10800)

        stats = manager.get_total_stats()
        assert stats['total_time_seconds'] == 10800

        # Converti in ore per verifica
        hours = stats['total_time_seconds'] / 3600
        assert hours == pytest.approx(3.0)
