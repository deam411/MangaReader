"""
Test suite per operazioni su volumi, capitoli e pagine.

Verifica inserimento, recupero, ordinamento e relazioni tra volume/chapter/page.
"""
import pytest
import tempfile
import os
from pathlib import Path
from src.database import MangaDatabaseManager
from tests.conftest import create_temp_image


class TestVolumeChapterOperations:
    """Test suite per operazioni volume/chapter/page."""

    @pytest.fixture
    def temp_db(self):
        """Crea database temporaneo con metadata e test image."""
        fd, path = tempfile.mkstemp(suffix='.manga')
        os.close(fd)

        db_manager = MangaDatabaseManager(path)
        db_manager.insert_metadata("Test Manga", "Author", "Description")

        # Crea immagine di test
        temp_dir = Path(tempfile.mkdtemp())
        test_image = create_temp_image(temp_dir, "test_page.png")

        yield path, db_manager, str(test_image)

        # Cleanup
        db_manager.close()
        if os.path.exists(path):
            os.remove(path)
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_insert_volume_success(self, temp_db):
        """Test inserimento volume con successo."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)

        assert volume_id > 0

        # Verifica salvato
        volumes = db_manager.get_volumes()
        assert len(volumes) == 1
        assert volumes[0]['name'] == "Volume 1"
        assert volumes[0]['order'] == 1

    def test_insert_multiple_volumes(self, temp_db):
        """Test inserimento multipli volumi."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)
        vol3_id = db_manager.insert_volume("Volume 3", 3)

        assert vol1_id > 0
        assert vol2_id > 0
        assert vol3_id > 0

        volumes = db_manager.get_volumes()
        assert len(volumes) == 3

    def test_volumes_ordered_by_order_field(self, temp_db):
        """Test che volumi siano ordinati per campo order."""
        path, db_manager, test_image = temp_db

        # Inserisci fuori ordine
        db_manager.insert_volume("Volume 3", 3)
        db_manager.insert_volume("Volume 1", 1)
        db_manager.insert_volume("Volume 2", 2)

        volumes = db_manager.get_volumes()

        # Dovrebbero essere ordinati
        assert volumes[0]['name'] == "Volume 1"
        assert volumes[1]['name'] == "Volume 2"
        assert volumes[2]['name'] == "Volume 3"

    def test_insert_volume_duplicate_order(self, temp_db):
        """Test inserimento volumi con stesso order number."""
        path, db_manager, test_image = temp_db

        # Due volumi con order = 1
        vol1_id = db_manager.insert_volume("Volume A", 1)
        vol2_id = db_manager.insert_volume("Volume B", 1)

        # Entrambi dovrebbero essere salvati
        assert vol1_id > 0
        assert vol2_id > 0

        volumes = db_manager.get_volumes()
        assert len(volumes) == 2

    def test_insert_chapter_success(self, temp_db):
        """Test inserimento capitolo con successo."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)

        assert chapter_id > 0

        chapters = db_manager.get_chapters(volume_id)
        assert len(chapters) == 1
        assert chapters[0]['name'] == "Chapter 1"
        assert chapters[0]['order'] == 1

    def test_insert_multiple_chapters_same_volume(self, temp_db):
        """Test inserimento multipli capitoli nello stesso volume."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)

        ch1_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)
        ch2_id = db_manager.insert_chapter("Chapter 2", 2, volume_id)
        ch3_id = db_manager.insert_chapter("Chapter 3", 3, volume_id)

        chapters = db_manager.get_chapters(volume_id)
        assert len(chapters) == 3

    def test_chapters_ordered_by_order_field(self, temp_db):
        """Test che capitoli siano ordinati per campo order."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)

        # Inserisci fuori ordine
        db_manager.insert_chapter("Chapter 3", 3, volume_id)
        db_manager.insert_chapter("Chapter 1", 1, volume_id)
        db_manager.insert_chapter("Chapter 2", 2, volume_id)

        chapters = db_manager.get_chapters(volume_id)

        # Dovrebbero essere ordinati
        assert chapters[0]['name'] == "Chapter 1"
        assert chapters[1]['name'] == "Chapter 2"
        assert chapters[2]['name'] == "Chapter 3"

    def test_chapter_order_resets_per_volume(self, temp_db):
        """Test che chapter order possa riprendere da 1 per ogni volume."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)

        # Volume 1: chapters 1-3
        db_manager.insert_chapter("V1 Ch1", 1, vol1_id)
        db_manager.insert_chapter("V1 Ch2", 2, vol1_id)
        db_manager.insert_chapter("V1 Ch3", 3, vol1_id)

        # Volume 2: chapters ripartono da 1
        db_manager.insert_chapter("V2 Ch1", 1, vol2_id)
        db_manager.insert_chapter("V2 Ch2", 2, vol2_id)

        chapters_vol1 = db_manager.get_chapters(vol1_id)
        chapters_vol2 = db_manager.get_chapters(vol2_id)

        assert len(chapters_vol1) == 3
        assert len(chapters_vol2) == 2

        assert chapters_vol2[0]['order'] == 1  # Order riparte da 1

    def test_insert_page_success(self, temp_db):
        """Test inserimento pagina con successo."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)

        image_data = b"fake_image_data"
        page_id = db_manager.insert_page(chapter_id, 1, image_data)

        assert page_id > 0

        pages = db_manager.get_pages(chapter_id)
        assert len(pages) == 1
        assert pages[0]['page_number'] == 1

    def test_insert_multiple_pages(self, temp_db):
        """Test inserimento multiple pagine."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)

        # Inserisci 10 pagine
        for i in range(1, 11):
            page_id = db_manager.insert_page(chapter_id, i, test_image)
            assert page_id > 0

        pages = db_manager.get_pages(chapter_id)
        assert len(pages) == 10

    def test_pages_ordered_by_page_number(self, temp_db):
        """Test che pagine siano ordinate per page_number."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)

        # Inserisci fuori ordine
        db_manager.insert_page(chapter_id, 5, test_image)
        db_manager.insert_page(chapter_id, 2, test_image)
        db_manager.insert_page(chapter_id, 1, test_image)
        db_manager.insert_page(chapter_id, 3, test_image)

        pages = db_manager.get_pages(chapter_id)

        # Dovrebbero essere ordinate
        assert pages[0]['page_number'] == 1
        assert pages[1]['page_number'] == 2
        assert pages[2]['page_number'] == 3
        assert pages[3]['page_number'] == 5

    def test_get_page_by_id(self, temp_db):
        """Test recupero singola pagina per ID."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)

        unique_data = b"unique_page_data_12345"
        page_id = db_manager.insert_page(chapter_id, 1, unique_data)

        # Recupera singola pagina
        page = db_manager.get_page(page_id)

        assert page is not None
        assert page['image'] == unique_data
        assert page['page_number'] == 1

    def test_get_pages_empty_chapter(self, temp_db):
        """Test recupero pagine da capitolo vuoto."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter_id = db_manager.insert_chapter("Empty Chapter", 1, volume_id)

        # Nessuna pagina aggiunta
        pages = db_manager.get_pages(chapter_id)

        assert pages == []

    def test_get_chapters_empty_volume(self, temp_db):
        """Test recupero capitoli da volume vuoto."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Empty Volume", 1)

        # Nessun capitolo aggiunto
        chapters = db_manager.get_chapters(volume_id)

        assert chapters == []

    def test_hierarchical_structure(self, temp_db):
        """Test struttura gerarchica completa volume>chapter>page."""
        path, db_manager, test_image = temp_db

        # Crea struttura completa
        vol1_id = db_manager.insert_volume("Volume 1", 1)

        ch1_id = db_manager.insert_chapter("Chapter 1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("Chapter 2", 2, vol1_id)

        # Chapter 1: 5 pagine
        for i in range(1, 6):
            db_manager.insert_page(ch1_id, i, test_image)

        # Chapter 2: 3 pagine
        for i in range(1, 4):
            db_manager.insert_page(ch2_id, i, test_image)

        # Verifica struttura
        volumes = db_manager.get_volumes()
        assert len(volumes) == 1

        chapters = db_manager.get_chapters(vol1_id)
        assert len(chapters) == 2

        pages_ch1 = db_manager.get_pages(ch1_id)
        pages_ch2 = db_manager.get_pages(ch2_id)

        assert len(pages_ch1) == 5
        assert len(pages_ch2) == 3

    def test_volume_with_unicode_name(self, temp_db):
        """Test volume con nome unicode."""
        path, db_manager, test_image = temp_db

        unicode_name = "第一巻"
        volume_id = db_manager.insert_volume(unicode_name, 1)

        volumes = db_manager.get_volumes()
        assert volumes[0]['name'] == unicode_name

    def test_chapter_with_unicode_name(self, temp_db):
        """Test capitolo con nome unicode."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)

        unicode_chapter = "第一章：冒険の始まり"
        chapter_id = db_manager.insert_chapter(unicode_chapter, 1, volume_id)

        chapters = db_manager.get_chapters(volume_id)
        assert chapters[0]['name'] == unicode_chapter

    def test_large_image_data(self, temp_db):
        """Test inserimento immagine di grandi dimensioni."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)

        # Simula immagine di 5MB
        large_image = b"X" * (5 * 1024 * 1024)

        page_id = db_manager.insert_page(chapter_id, 1, large_image)

        assert page_id > 0

        page = db_manager.get_page(page_id)
        assert len(page['image']) == len(large_image)

    def test_many_pages_performance(self, temp_db):
        """Test inserimento di molte pagine."""
        import time

        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter_id = db_manager.insert_chapter("Long Chapter", 1, volume_id)

        # Inserisci 100 pagine
        start = time.time()

        for i in range(1, 101):
            db_manager.insert_page(chapter_id, i, test_image)

        elapsed = time.time() - start

        # Dovrebbe essere veloce
        assert elapsed < 5.0  # Meno di 5 secondi per 100 pagine

        pages = db_manager.get_pages(chapter_id)
        assert len(pages) == 100

    def test_get_volumes_count(self, temp_db):
        """Test conteggio volumi."""
        path, db_manager, test_image = temp_db

        # Aggiungi 5 volumi
        for i in range(1, 6):
            db_manager.insert_volume(f"Volume {i}", i)

        volumes = db_manager.get_volumes()
        assert len(volumes) == 5

    def test_get_chapters_count_per_volume(self, temp_db):
        """Test conteggio capitoli per volume."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)

        # Volume 1: 5 capitoli
        for i in range(1, 6):
            db_manager.insert_chapter(f"V1 Ch{i}", i, vol1_id)

        # Volume 2: 3 capitoli
        for i in range(1, 4):
            db_manager.insert_chapter(f"V2 Ch{i}", i, vol2_id)

        chapters_vol1 = db_manager.get_chapters(vol1_id)
        chapters_vol2 = db_manager.get_chapters(vol2_id)

        assert len(chapters_vol1) == 5
        assert len(chapters_vol2) == 3

    def test_insert_volume_with_long_name(self, temp_db):
        """Test volume con nome molto lungo."""
        path, db_manager, test_image = temp_db

        long_name = "A" * 500

        volume_id = db_manager.insert_volume(long_name, 1)
        assert volume_id > 0

        volumes = db_manager.get_volumes()
        assert volumes[0]['name'] == long_name

    def test_insert_chapter_with_long_name(self, temp_db):
        """Test capitolo con nome molto lungo."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)

        long_name = "B" * 500

        chapter_id = db_manager.insert_chapter(long_name, 1, volume_id)
        assert chapter_id > 0

        chapters = db_manager.get_chapters(volume_id)
        assert chapters[0]['name'] == long_name

    def test_volume_chapter_page_ids_unique(self, temp_db):
        """Test che ID siano univoci e incrementali."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)

        assert vol1_id != vol2_id

        ch1_id = db_manager.insert_chapter("Chapter 1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("Chapter 2", 1, vol2_id)

        assert ch1_id != ch2_id

        page1_id = db_manager.insert_page(ch1_id, 1, test_image)
        page2_id = db_manager.insert_page(ch2_id, 1, test_image)

        assert page1_id != page2_id

    def test_get_page_count_for_chapter(self, temp_db):
        """Test conteggio pagine per capitolo."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)

        ch1_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)
        ch2_id = db_manager.insert_chapter("Chapter 2", 2, volume_id)

        # Chapter 1: 10 pagine
        for i in range(1, 11):
            db_manager.insert_page(ch1_id, i, test_image)

        # Chapter 2: 5 pagine
        for i in range(1, 6):
            db_manager.insert_page(ch2_id, i, test_image)

        pages_ch1 = db_manager.get_pages(ch1_id)
        pages_ch2 = db_manager.get_pages(ch2_id)

        assert len(pages_ch1) == 10
        assert len(pages_ch2) == 5

    def test_total_pages_count(self, temp_db):
        """Test conteggio totale pagine nel manga."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)

        ch1_id = db_manager.insert_chapter("Chapter 1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("Chapter 2", 2, vol1_id)
        ch3_id = db_manager.insert_chapter("Chapter 3", 3, vol1_id)

        # 10 + 15 + 20 = 45 pagine totali
        for i in range(1, 11):
            db_manager.insert_page(ch1_id, i, test_image)

        for i in range(1, 16):
            db_manager.insert_page(ch2_id, i, test_image)

        for i in range(1, 21):
            db_manager.insert_page(ch3_id, i, test_image)

        # Conta tutte le pagine
        import sqlite3
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pages")
            total = cursor.fetchone()[0]

        assert total == 45

    def test_empty_database_volumes(self):
        """Test get_volumes su database vuoto."""
        fd, path = tempfile.mkstemp(suffix='.manga')
        os.close(fd)

        db_manager = MangaDatabaseManager(path)
        db_manager.insert_metadata("Test", "Author", "Desc")

        volumes = db_manager.get_volumes()
        assert volumes == []

        db_manager.close()
        os.remove(path)
