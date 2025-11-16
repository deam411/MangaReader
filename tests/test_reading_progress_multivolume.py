"""
Test per il calcolo corretto della percentuale di lettura su manga multi-volume.

Verifica che il fix per il calcolo del progresso consideri correttamente
sia volume.order che chapter.order invece di solo chapter.order.
"""
import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from src.database import MangaDatabaseManager
from src.database.history_manager import HistoryManager
from src.views.utils import calculate_reading_progress_fast
from tests.conftest import create_temp_image


class TestReadingProgressMultiVolume:
    """Test suite per il calcolo progresso lettura multi-volume."""

    @pytest.fixture
    def temp_manga_db(self):
        """Crea un database manga temporaneo per i test."""
        fd, path = tempfile.mkstemp(suffix='.manga')
        os.close(fd)

        # Crea database con schema completo
        db_manager = MangaDatabaseManager(path)

        # Aggiungi metadata
        db_manager.insert_metadata(
            title="Test Manga Multi-Volume",
            author="Test Author",
            description="Test description"
        )

        # Crea immagine di test
        temp_dir = Path(tempfile.mkdtemp())
        test_image = create_temp_image(temp_dir, "test_page.png")

        yield path, db_manager, str(test_image)

        # Cleanup
        db_manager.close()

        # Force garbage collection to close any lingering connections
        import gc
        gc.collect()

        # On Windows, SQLite may leave lock files, retry with delay
        import time
        max_retries = 3
        for i in range(max_retries):
            try:
                if os.path.exists(path):
                    os.remove(path)
                break
            except PermissionError:
                if i < max_retries - 1:
                    time.sleep(0.1)
                    gc.collect()
                else:
                    # Last attempt failed, ignore
                    pass

        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_progress_single_volume(self, temp_manga_db):
        """Test progresso su manga con singolo volume."""
        path, db_manager, test_image = temp_manga_db

        # Crea volume con 2 capitoli
        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter1_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)
        chapter2_id = db_manager.insert_chapter("Chapter 2", 2, volume_id)

        # Aggiungi 10 pagine per capitolo
        for i in range(1, 11):
            db_manager.insert_page(chapter1_id, i, test_image)
            db_manager.insert_page(chapter2_id, i, test_image)

        # Salva posizione a pagina 5 del capitolo 1
        history_mgr = HistoryManager(path)
        history_mgr.save_reading_position(chapter1_id, 5, "default")

        # Verifica progresso: 5 pagine su 20 totali = 25%
        progress = history_mgr.get_reading_progress("default")

        assert progress is not None
        assert progress['total_pages'] == 20
        assert progress['read_pages'] == 5
        assert progress['percentage'] == pytest.approx(25.0, rel=0.1)

    def test_progress_multi_volume_first_volume(self, temp_manga_db):
        """Test progresso su primo volume di manga multi-volume."""
        path, db_manager, test_image = temp_manga_db

        # Crea 3 volumi con 1 capitolo ciascuno
        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)
        vol3_id = db_manager.insert_volume("Volume 3", 3)

        ch1_id = db_manager.insert_chapter("Chapter 1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("Chapter 2", 1, vol2_id)  # order riparte da 1
        ch3_id = db_manager.insert_chapter("Chapter 3", 1, vol3_id)  # order riparte da 1

        # 10 pagine per capitolo (30 totali)
        for ch_id in [ch1_id, ch2_id, ch3_id]:
            for i in range(1, 11):
                db_manager.insert_page(ch_id, i, test_image)

        # Lettura a metà del primo volume
        history_mgr = HistoryManager(path)
        history_mgr.save_reading_position(ch1_id, 5, "default")

        progress = history_mgr.get_reading_progress("default")

        assert progress is not None
        assert progress['total_pages'] == 30
        assert progress['read_pages'] == 5
        assert progress['percentage'] == pytest.approx(16.67, rel=0.1)

    def test_progress_multi_volume_second_volume(self, temp_manga_db):
        """Test progresso su secondo volume di manga multi-volume."""
        path, db_manager, test_image = temp_manga_db

        # Crea 3 volumi con 1 capitolo ciascuno
        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)
        vol3_id = db_manager.insert_volume("Volume 3", 3)

        ch1_id = db_manager.insert_chapter("Chapter 1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("Chapter 2", 1, vol2_id)
        ch3_id = db_manager.insert_chapter("Chapter 3", 1, vol3_id)

        # 10 pagine per capitolo
        for ch_id in [ch1_id, ch2_id, ch3_id]:
            for i in range(1, 11):
                db_manager.insert_page(ch_id, i, test_image)

        # Lettura a metà del secondo volume
        history_mgr = HistoryManager(path)
        history_mgr.save_reading_position(ch2_id, 5, "default")

        progress = history_mgr.get_reading_progress("default")

        # Volume 1 completo (10) + 5 pagine volume 2 = 15 su 30
        assert progress is not None
        assert progress['total_pages'] == 30
        assert progress['read_pages'] == 15
        assert progress['percentage'] == pytest.approx(50.0, rel=0.1)

    def test_progress_multi_volume_last_page(self, temp_manga_db):
        """Test progresso all'ultima pagina dell'ultimo volume."""
        path, db_manager, test_image = temp_manga_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)

        ch1_id = db_manager.insert_chapter("Chapter 1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("Chapter 2", 1, vol2_id)

        for ch_id in [ch1_id, ch2_id]:
            for i in range(1, 11):
                db_manager.insert_page(ch_id, i, test_image)

        # Ultima pagina
        history_mgr = HistoryManager(path)
        history_mgr.save_reading_position(ch2_id, 10, "default")

        progress = history_mgr.get_reading_progress("default")

        # 20 pagine lette su 20 = 100%
        assert progress is not None
        assert progress['total_pages'] == 20
        assert progress['read_pages'] == 20
        assert progress['percentage'] == pytest.approx(100.0, rel=0.1)

    def test_progress_fast_calculation(self, temp_manga_db):
        """Test calcolo veloce progresso (utilizzato in library view)."""
        path, db_manager, test_image = temp_manga_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)

        ch1_id = db_manager.insert_chapter("Chapter 1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("Chapter 2", 1, vol2_id)

        for ch_id in [ch1_id, ch2_id]:
            for i in range(1, 11):
                db_manager.insert_page(ch_id, i, test_image)

        # Salva posizione
        history_mgr = HistoryManager(path)
        history_mgr.save_reading_position(ch2_id, 3, "default")

        # Usa funzione fast
        with sqlite3.connect(path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            progress = calculate_reading_progress_fast(cursor, "default")

        # Volume 1 completo (10) + 3 pagine volume 2 = 13 su 20
        assert progress is not None
        assert progress['total_pages'] == 20
        assert progress['read_pages'] == 13
        assert progress['percentage'] == pytest.approx(65.0, rel=0.1)

    def test_progress_multiple_chapters_per_volume(self, temp_manga_db):
        """Test progresso con più capitoli per volume."""
        path, db_manager, test_image = temp_manga_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)

        # Volume 1: 2 capitoli
        ch1_id = db_manager.insert_chapter("Chapter 1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("Chapter 2", 2, vol1_id)

        # Volume 2: 2 capitoli (order riparte da 1)
        ch3_id = db_manager.insert_chapter("Chapter 3", 1, vol2_id)
        ch4_id = db_manager.insert_chapter("Chapter 4", 2, vol2_id)

        # 5 pagine per capitolo (20 totali)
        for ch_id in [ch1_id, ch2_id, ch3_id, ch4_id]:
            for i in range(1, 6):
                db_manager.insert_page(ch_id, i, test_image)

        # Lettura al capitolo 3, pagina 2
        history_mgr = HistoryManager(path)
        history_mgr.save_reading_position(ch3_id, 2, "default")

        progress = history_mgr.get_reading_progress("default")

        # Vol 1 completo (10) + 2 pagine ch3 = 12 su 20
        assert progress is not None
        assert progress['total_pages'] == 20
        assert progress['read_pages'] == 12
        assert progress['percentage'] == pytest.approx(60.0, rel=0.1)

    def test_progress_zero_pages(self, temp_manga_db):
        """Test progresso su manga senza pagine."""
        path, db_manager, test_image = temp_manga_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        ch1_id = db_manager.insert_chapter("Chapter 1", 1, vol1_id)

        # Nessuna pagina aggiunta
        history_mgr = HistoryManager(path)
        progress = history_mgr.get_reading_progress("default")

        # Dovrebbe ritornare None per manga senza pagine
        assert progress is None

    def test_progress_no_history(self, temp_manga_db):
        """Test progresso senza cronologia di lettura."""
        path, db_manager, test_image = temp_manga_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        ch1_id = db_manager.insert_chapter("Chapter 1", 1, vol1_id)

        for i in range(1, 6):
            db_manager.insert_page(ch1_id, i, test_image)

        # Nessuna posizione salvata
        history_mgr = HistoryManager(path)
        progress = history_mgr.get_reading_progress("default")

        # Dovrebbe ritornare 0%
        assert progress is not None
        assert progress['total_pages'] == 5
        assert progress['read_pages'] == 0
        assert progress['percentage'] == 0.0
