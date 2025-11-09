"""
Test suite estesa per History Manager.

Verifica funzionalità di salvataggio posizione, recupero e calcolo progresso.
Include test per multi-utente e edge cases.
"""
import pytest
import sqlite3
import tempfile
import os
from src.database import MangaDatabaseManager
from src.database.history_manager import HistoryManager


class TestHistoryManagerExtended:
    """Test suite estesa per History Manager."""

    @pytest.fixture
    def temp_manga_db(self):
        """Crea un database manga temporaneo con struttura completa."""
        from tests.conftest import create_temp_image
        from pathlib import Path

        fd, path = tempfile.mkstemp(suffix='.manga')
        os.close(fd)

        db_manager = MangaDatabaseManager(path)

        # Setup base
        db_manager.insert_metadata(
            title="Test Manga",
            author="Test Author",
            description="Test description"
        )

        # Crea 2 volumi con 2 capitoli ciascuno
        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)

        ch1_id = db_manager.insert_chapter("Chapter 1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("Chapter 2", 2, vol1_id)
        ch3_id = db_manager.insert_chapter("Chapter 3", 1, vol2_id)
        ch4_id = db_manager.insert_chapter("Chapter 4", 2, vol2_id)

        # Crea temp directory per immagini
        temp_dir = Path(tempfile.mkdtemp())
        test_image = create_temp_image(temp_dir, "test_page.png")

        # 10 pagine per capitolo
        for ch_id in [ch1_id, ch2_id, ch3_id, ch4_id]:
            for i in range(1, 11):
                db_manager.insert_page(ch_id, i, str(test_image))

        yield path, db_manager

        # Cleanup
        db_manager.close()
        if os.path.exists(path):
            os.remove(path)
        # Cleanup temp images
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_save_reading_position_first_time(self, temp_manga_db):
        """Test salvataggio prima posizione di lettura."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        result = history_mgr.save_reading_position(
            chapter_id=1,
            page_number=5,
            user="default"
        )

        assert result is True

        # Verifica salvata
        position = history_mgr.get_last_reading_position()
        assert position is not None
        assert position['chapter_id'] == 1
        assert position['page_number'] == 5

    def test_save_reading_position_update_existing(self, temp_manga_db):
        """Test aggiornamento posizione esistente."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # Prima posizione
        history_mgr.save_reading_position(1, 5, "default")

        # Aggiorna
        history_mgr.save_reading_position(2, 10, "default")

        # Dovrebbe esserci solo una entry, aggiornata
        position = history_mgr.get_last_reading_position()
        assert position['chapter_id'] == 2
        assert position['page_number'] == 10

    def test_multiple_users_separate_positions(self, temp_manga_db):
        """Test posizioni separate per utenti diversi."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # User 1
        history_mgr.save_reading_position(1, 5, "user1")

        # User 2
        history_mgr.save_reading_position(2, 10, "user2")

        # User 3
        history_mgr.save_reading_position(3, 15, "user3")

        # Verifica posizioni separate
        pos1 = history_mgr.get_last_reading_position("user1")
        pos2 = history_mgr.get_last_reading_position("user2")
        pos3 = history_mgr.get_last_reading_position("user3")

        assert pos1['chapter_id'] == 1 and pos1['page_number'] == 5
        assert pos2['chapter_id'] == 2 and pos2['page_number'] == 10
        assert pos3['chapter_id'] == 3 and pos3['page_number'] == 15

    def test_get_last_position_no_history(self, temp_manga_db):
        """Test recupero posizione quando non c'è cronologia."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        position = history_mgr.get_last_reading_position("nonexistent_user")
        assert position is None

    def test_get_last_position_with_chapter_volume_info(self, temp_manga_db):
        """Test che get_last_position includa info chapter e volume."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        history_mgr.save_reading_position(1, 5, "default")

        position = history_mgr.get_last_reading_position()

        assert 'chapter_name' in position
        assert 'volume_name' in position
        assert 'volume_id' in position
        assert position['chapter_name'] == "Chapter 1"
        assert position['volume_name'] == "Volume 1"

    def test_reading_progress_no_history(self, temp_manga_db):
        """Test progresso senza cronologia (0%)."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        progress = history_mgr.get_reading_progress("default")

        assert progress is not None
        assert progress['total_pages'] == 40  # 4 capitoli × 10 pagine
        assert progress['read_pages'] == 0
        assert progress['percentage'] == 0.0

    def test_reading_progress_first_chapter(self, temp_manga_db):
        """Test progresso a metà primo capitolo."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # Pagina 5 del capitolo 1
        history_mgr.save_reading_position(1, 5, "default")

        progress = history_mgr.get_reading_progress()

        assert progress['total_pages'] == 40
        assert progress['read_pages'] == 5
        assert progress['percentage'] == pytest.approx(12.5, rel=0.1)

    def test_reading_progress_second_volume(self, temp_manga_db):
        """Test progresso nel secondo volume."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # Capitolo 3 (primo del volume 2), pagina 3
        history_mgr.save_reading_position(3, 3, "default")

        progress = history_mgr.get_reading_progress()

        # Volume 1 completo (20 pagine) + 3 pagine volume 2 = 23
        assert progress['total_pages'] == 40
        assert progress['read_pages'] == 23
        assert progress['percentage'] == pytest.approx(57.5, rel=0.1)

    def test_reading_progress_last_page(self, temp_manga_db):
        """Test progresso all'ultima pagina (100%)."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # Ultimo capitolo, ultima pagina
        history_mgr.save_reading_position(4, 10, "default")

        progress = history_mgr.get_reading_progress()

        assert progress['total_pages'] == 40
        assert progress['read_pages'] == 40
        assert progress['percentage'] == pytest.approx(100.0, rel=0.01)

    def test_clear_reading_history(self, temp_manga_db):
        """Test cancellazione cronologia."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # Salva posizione
        history_mgr.save_reading_position(1, 5, "default")

        # Verifica salvata
        position = history_mgr.get_last_reading_position()
        assert position is not None

        # Cancella
        result = history_mgr.clear_reading_history("default")
        assert result is True

        # Verifica cancellata
        position = history_mgr.get_last_reading_position()
        assert position is None

    def test_clear_history_specific_user(self, temp_manga_db):
        """Test che clear_history cancelli solo utente specificato."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # Salva per due utenti
        history_mgr.save_reading_position(1, 5, "user1")
        history_mgr.save_reading_position(2, 10, "user2")

        # Cancella solo user1
        history_mgr.clear_reading_history("user1")

        # Verifica
        pos1 = history_mgr.get_last_reading_position("user1")
        pos2 = history_mgr.get_last_reading_position("user2")

        assert pos1 is None
        assert pos2 is not None
        assert pos2['chapter_id'] == 2

    def test_timestamp_updated_on_save(self, temp_manga_db):
        """Test che timestamp venga aggiornato ad ogni salvataggio."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        import time

        # Primo salvataggio
        history_mgr.save_reading_position(1, 5, "default")
        pos1 = history_mgr.get_last_reading_position()
        timestamp1 = pos1['timestamp']

        time.sleep(0.1)  # Piccolo delay

        # Secondo salvataggio
        history_mgr.save_reading_position(1, 6, "default")
        pos2 = history_mgr.get_last_reading_position()
        timestamp2 = pos2['timestamp']

        # Timestamp dovrebbe essere diverso
        assert timestamp2 > timestamp1

    def test_save_position_page_zero(self, temp_manga_db):
        """Test salvataggio con page_number = 0 (caso edge)."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # Potrebbe accadere all'inizio della lettura
        result = history_mgr.save_reading_position(1, 0, "default")
        assert result is True

        position = history_mgr.get_last_reading_position()
        assert position['page_number'] == 0

    def test_save_position_invalid_chapter(self, temp_manga_db):
        """Test salvataggio con chapter_id non esistente."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # Chapter 999 non esiste
        result = history_mgr.save_reading_position(999, 5, "default")

        # Il salvataggio riesce (non c'è validazione di FK)
        # Ma get_last_reading_position non troverà i dati del chapter
        assert result is True

        position = history_mgr.get_last_reading_position()
        # chapter_name e volume_name saranno None per FK invalidi
        assert position['chapter_id'] == 999

    def test_progress_empty_manga(self):
        """Test progresso su manga senza pagine."""
        fd, path = tempfile.mkstemp(suffix='.manga')
        os.close(fd)

        db_manager = MangaDatabaseManager(path)
        db_manager.insert_metadata("Empty Manga", "Author", "Description")

        # Crea volume e capitolo ma nessuna pagina
        vol_id = db_manager.insert_volume("Volume 1", 1)
        ch_id = db_manager.insert_chapter("Chapter 1", 1, vol_id)

        history_mgr = HistoryManager(path)

        # Nessuna cronologia
        progress = history_mgr.get_reading_progress()
        assert progress is None  # Nessuna pagina = nessun progresso

        db_manager.close()
        os.remove(path)

    def test_concurrent_position_updates(self, temp_manga_db):
        """Test aggiornamenti consecutivi rapidi della posizione."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # Simula lettura veloce con aggiornamenti consecutivi
        for page in range(1, 11):
            result = history_mgr.save_reading_position(1, page, "default")
            assert result is True

        # L'ultima dovrebbe essere salvata
        position = history_mgr.get_last_reading_position()
        assert position['page_number'] == 10

    def test_progress_calculation_performance(self, temp_manga_db):
        """Test che calcolo progresso sia veloce anche con molte pagine."""
        import time

        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # Aggiungi più pagine per test performance
        vol_id = db_manager.insert_volume("Volume 3", 3)

        for i in range(10):  # 10 capitoli extra
            ch_id = db_manager.insert_chapter(f"Chapter Extra {i}", i + 1, vol_id)
            for j in range(1, 51):  # 50 pagine ciascuno
                db_manager.insert_page(ch_id, j, b"data")

        # Salva posizione
        history_mgr.save_reading_position(1, 5, "default")

        # Misura tempo calcolo progresso
        start = time.time()
        progress = history_mgr.get_reading_progress()
        elapsed = time.time() - start

        # Dovrebbe essere veloce (< 100ms anche con centinaia di pagine)
        assert elapsed < 0.1
        assert progress is not None

    def test_reading_position_with_deleted_chapter(self, temp_manga_db):
        """Test comportamento quando capitolo salvato viene eliminato."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # Salva posizione
        history_mgr.save_reading_position(1, 5, "default")

        # Elimina il capitolo dal database (manualmente, non c'è API)
        with sqlite3.connect(path) as conn:
            conn.execute("DELETE FROM chapters WHERE id = 1")

        # get_last_reading_position dovrebbe gestire gracefully
        position = history_mgr.get_last_reading_position()

        # Position esiste ma chapter_name/volume_name saranno None
        assert position is not None
        assert position['chapter_id'] == 1
        assert position['chapter_name'] is None

    def test_progress_with_unordered_chapters(self, temp_manga_db):
        """Test calcolo progresso con capitoli non ordinati."""
        # Crea database con ordine non sequenziale
        fd, path = tempfile.mkstemp(suffix='.manga')
        os.close(fd)

        db_manager = MangaDatabaseManager(path)
        db_manager.insert_metadata("Test", "Author", "Desc")

        vol_id = db_manager.insert_volume("Volume 1", 1)

        # Capitoli con order non sequenziale
        ch1 = db_manager.insert_chapter("Ch 1", 1, vol_id)
        ch3 = db_manager.insert_chapter("Ch 3", 3, vol_id)
        ch2 = db_manager.insert_chapter("Ch 2", 2, vol_id)

        # 5 pagine ciascuno
        for ch_id in [ch1, ch2, ch3]:
            for i in range(1, 6):
                db_manager.insert_page(ch_id, i, b"data")

        history_mgr = HistoryManager(path)

        # Posizione a chapter 2 (order=2), pagina 3
        history_mgr.save_reading_position(ch2, 3, "default")

        progress = history_mgr.get_reading_progress()

        # Chapter 1 completo (5) + 3 pagine ch2 = 8 su 15
        assert progress['total_pages'] == 15
        assert progress['read_pages'] == 8
        assert progress['percentage'] == pytest.approx(53.33, rel=0.1)

        db_manager.close()
        os.remove(path)

    def test_user_names_with_special_characters(self, temp_manga_db):
        """Test utenti con nomi speciali."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        special_users = [
            "user@email.com",
            "user-123",
            "user_test",
            "用户",  # Caratteri unicode
        ]

        for user in special_users:
            history_mgr.save_reading_position(1, 5, user)
            position = history_mgr.get_last_reading_position(user)
            assert position is not None
            assert position['chapter_id'] == 1

    def test_progress_multiple_users_independent(self, temp_manga_db):
        """Test che progresso sia indipendente per ogni utente."""
        path, db_manager = temp_manga_db
        history_mgr = HistoryManager(path)

        # User1 a metà
        history_mgr.save_reading_position(2, 5, "user1")

        # User2 quasi finito
        history_mgr.save_reading_position(4, 8, "user2")

        progress1 = history_mgr.get_reading_progress("user1")
        progress2 = history_mgr.get_reading_progress("user2")

        # Entrambi hanno total_pages uguale
        assert progress1['total_pages'] == progress2['total_pages']

        # Ma read_pages diverso
        assert progress1['read_pages'] < progress2['read_pages']
        assert progress1['percentage'] < progress2['percentage']
