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
        # Il nome viene troncato a MAX_VOLUME_NAME_LENGTH (100 caratteri)
        assert volumes[0]['name'] == "A" * 100

    def test_insert_chapter_with_long_name(self, temp_db):
        """Test capitolo con nome molto lungo."""
        path, db_manager, test_image = temp_db

        volume_id = db_manager.insert_volume("Volume 1", 1)

        long_name = "B" * 500

        chapter_id = db_manager.insert_chapter(long_name, 1, volume_id)
        assert chapter_id > 0

        chapters = db_manager.get_chapters(volume_id)
        # Il nome viene troncato a MAX_CHAPTER_NAME_LENGTH (200 caratteri)
        assert chapters[0]['name'] == "B" * 200

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

    def test_update_volumes_order_basic(self, temp_db):
        """Test riordinamento base di 3 volumi."""
        path, db_manager, test_image = temp_db

        # Crea 3 volumi in ordine
        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)
        vol3_id = db_manager.insert_volume("Volume 3", 3)

        # Verifica ordine iniziale
        volumes = db_manager.get_volumes()
        assert volumes[0]['name'] == "Volume 1"
        assert volumes[1]['name'] == "Volume 2"
        assert volumes[2]['name'] == "Volume 3"

        # Riordina: inverti l'ordine [3, 2, 1]
        result = db_manager.update_volumes_order([vol3_id, vol2_id, vol1_id])
        assert result is True

        # Verifica nuovo ordine
        volumes = db_manager.get_volumes()
        assert len(volumes) == 3
        assert volumes[0]['name'] == "Volume 3"
        assert volumes[0]['order'] == 1
        assert volumes[1]['name'] == "Volume 2"
        assert volumes[1]['order'] == 2
        assert volumes[2]['name'] == "Volume 1"
        assert volumes[2]['order'] == 3

    def test_update_volumes_order_database_persistence(self, temp_db):
        """Test che l'ordine aggiornato sia persistente nel database."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("Volume A", 1)
        vol2_id = db_manager.insert_volume("Volume B", 2)
        vol3_id = db_manager.insert_volume("Volume C", 3)

        # Riordina
        db_manager.update_volumes_order([vol2_id, vol3_id, vol1_id])

        # Chiudi e riapri il database
        db_manager.close()

        # Crea nuova connessione
        db_manager2 = MangaDatabaseManager(path)
        volumes = db_manager2.get_volumes()

        # Verifica che l'ordine sia persistito
        assert volumes[0]['name'] == "Volume B"
        assert volumes[1]['name'] == "Volume C"
        assert volumes[2]['name'] == "Volume A"

        db_manager2.close()

    def test_update_volumes_order_single_volume(self, temp_db):
        """Test riordinamento con singolo volume."""
        path, db_manager, test_image = temp_db

        vol_id = db_manager.insert_volume("Only Volume", 1)

        # Riordina con un solo elemento
        result = db_manager.update_volumes_order([vol_id])
        assert result is True

        volumes = db_manager.get_volumes()
        assert len(volumes) == 1
        assert volumes[0]['name'] == "Only Volume"
        assert volumes[0]['order'] == 1

    def test_update_volumes_order_empty_list(self, temp_db):
        """Test riordinamento con lista vuota."""
        path, db_manager, test_image = temp_db

        db_manager.insert_volume("Volume 1", 1)

        # Riordina con lista vuota
        result = db_manager.update_volumes_order([])
        assert result is True  # Dovrebbe completare senza errori

    def test_update_volumes_order_many_volumes(self, temp_db):
        """Test riordinamento con molti volumi (10)."""
        path, db_manager, test_image = temp_db

        # Crea 10 volumi
        volume_ids = []
        for i in range(1, 11):
            vol_id = db_manager.insert_volume(f"Volume {i}", i)
            volume_ids.append(vol_id)

        # Inverti completamente l'ordine
        reversed_ids = list(reversed(volume_ids))
        result = db_manager.update_volumes_order(reversed_ids)
        assert result is True

        # Verifica nuovo ordine
        volumes = db_manager.get_volumes()
        assert len(volumes) == 10
        assert volumes[0]['name'] == "Volume 10"
        assert volumes[9]['name'] == "Volume 1"

        # Verifica che gli ordini siano sequenziali 1-10
        for i, vol in enumerate(volumes):
            assert vol['order'] == i + 1

    def test_update_volumes_order_partial_reorder(self, temp_db):
        """Test riordinamento parziale (swap di 2 volumi centrali)."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)
        vol3_id = db_manager.insert_volume("Volume 3", 3)
        vol4_id = db_manager.insert_volume("Volume 4", 4)

        # Swap volume 2 e 3
        result = db_manager.update_volumes_order([vol1_id, vol3_id, vol2_id, vol4_id])
        assert result is True

        volumes = db_manager.get_volumes()
        assert volumes[0]['name'] == "Volume 1"
        assert volumes[1]['name'] == "Volume 3"
        assert volumes[2]['name'] == "Volume 2"
        assert volumes[3]['name'] == "Volume 4"

    def test_update_volumes_order_preserves_chapters(self, temp_db):
        """Test che il riordinamento volumi preservi i capitoli associati."""
        path, db_manager, test_image = temp_db

        # Crea volumi con capitoli
        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)

        ch1_id = db_manager.insert_chapter("V1 Chapter 1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("V2 Chapter 1", 1, vol2_id)

        # Riordina volumi
        db_manager.update_volumes_order([vol2_id, vol1_id])

        # Verifica che i capitoli siano ancora associati correttamente
        chapters_vol1 = db_manager.get_chapters(vol1_id)
        chapters_vol2 = db_manager.get_chapters(vol2_id)

        assert len(chapters_vol1) == 1
        assert chapters_vol1[0]['name'] == "V1 Chapter 1"

        assert len(chapters_vol2) == 1
        assert chapters_vol2[0]['name'] == "V2 Chapter 1"

    def test_update_volumes_order_with_unicode_names(self, temp_db):
        """Test riordinamento volumi con nomi unicode."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("第一巻", 1)
        vol2_id = db_manager.insert_volume("第二巻", 2)
        vol3_id = db_manager.insert_volume("第三巻", 3)

        # Riordina
        result = db_manager.update_volumes_order([vol3_id, vol1_id, vol2_id])
        assert result is True

        volumes = db_manager.get_volumes()
        assert volumes[0]['name'] == "第三巻"
        assert volumes[1]['name'] == "第一巻"
        assert volumes[2]['name'] == "第二巻"

    def test_update_volumes_order_duplicate_detection(self, temp_db):
        """Test che riordinamento gestisca correttamente duplicati nella lista."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)
        vol3_id = db_manager.insert_volume("Volume 3", 3)

        # Passa lista con duplicato (vol1 appare 2 volte)
        # Il comportamento dovrebbe essere deterministico
        result = db_manager.update_volumes_order([vol1_id, vol2_id, vol1_id])
        assert result is True  # Non dovrebbe crashare

        # Verifica che il database sia in uno stato consistente
        volumes = db_manager.get_volumes()
        assert len(volumes) == 3  # Tutti i volumi dovrebbero esistere ancora

    def test_update_volumes_order_complex_scenario(self, temp_db):
        """Test scenario complesso: riordina, aggiungi, riordina di nuovo."""
        path, db_manager, test_image = temp_db

        # Fase 1: Crea 3 volumi
        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)
        vol3_id = db_manager.insert_volume("Volume 3", 3)

        # Fase 2: Riordina
        db_manager.update_volumes_order([vol3_id, vol1_id, vol2_id])

        # Fase 3: Aggiungi nuovo volume
        vol4_id = db_manager.insert_volume("Volume 4", 4)

        # Fase 4: Riordina di nuovo includendo il nuovo volume
        db_manager.update_volumes_order([vol4_id, vol3_id, vol2_id, vol1_id])

        # Verifica ordine finale
        volumes = db_manager.get_volumes()
        assert len(volumes) == 4
        assert volumes[0]['name'] == "Volume 4"
        assert volumes[1]['name'] == "Volume 3"
        assert volumes[2]['name'] == "Volume 2"
        assert volumes[3]['name'] == "Volume 1"

    def test_update_volumes_order_after_update_volume(self, temp_db):
        """Test che update_volumes_order funzioni dopo update_volume."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)
        vol3_id = db_manager.insert_volume("Volume 3", 3)

        # Aggiorna nome di un volume
        result = db_manager.update_volume(vol2_id, "Volume 2 Updated", 2, None)
        assert result is True

        # Riordina volumi
        result = db_manager.update_volumes_order([vol3_id, vol2_id, vol1_id])
        assert result is True

        # Verifica che il nome aggiornato sia preservato
        volumes = db_manager.get_volumes()
        assert volumes[0]['name'] == "Volume 3"
        assert volumes[1]['name'] == "Volume 2 Updated"
        assert volumes[2]['name'] == "Volume 1"

    def test_update_volumes_order_before_delete_volume(self, temp_db):
        """Test che delete_volume funzioni dopo update_volumes_order."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)
        vol3_id = db_manager.insert_volume("Volume 3", 3)

        # Riordina
        db_manager.update_volumes_order([vol3_id, vol1_id, vol2_id])

        # Elimina volume centrale
        result = db_manager.delete_volume(vol1_id)
        assert result is True

        # Verifica che rimangano solo 2 volumi nell'ordine corretto
        volumes = db_manager.get_volumes()
        assert len(volumes) == 2
        assert volumes[0]['name'] == "Volume 3"
        assert volumes[1]['name'] == "Volume 2"

    def test_update_volumes_order_with_invalid_id(self, temp_db):
        """Test update_volumes_order con ID non esistente."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)

        # Usa un ID che non esiste (999)
        result = db_manager.update_volumes_order([vol1_id, 999, vol2_id])

        # Dovrebbe completare senza crashare (comportamento implementazione-specifico)
        assert result is True

        # Database dovrebbe rimanere consistente
        volumes = db_manager.get_volumes()
        assert len(volumes) == 2

    def test_update_volumes_order_independent_from_chapters_order(self, temp_db):
        """Test che update_volumes_order non influenzi update_chapters_order."""
        path, db_manager, test_image = temp_db

        # Crea struttura con volumi e capitoli
        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)

        ch1_id = db_manager.insert_chapter("Vol1 Ch1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("Vol1 Ch2", 2, vol1_id)
        ch3_id = db_manager.insert_chapter("Vol2 Ch1", 1, vol2_id)

        # Riordina volumi
        db_manager.update_volumes_order([vol2_id, vol1_id])

        # Riordina capitoli del volume 1
        db_manager.update_chapters_order([ch2_id, ch1_id])

        # Verifica che entrambi gli ordini siano corretti
        volumes = db_manager.get_volumes()
        assert volumes[0]['name'] == "Volume 2"
        assert volumes[1]['name'] == "Volume 1"

        chapters = db_manager.get_chapters(vol1_id)
        assert chapters[0]['name'] == "Vol1 Ch2"
        assert chapters[1]['name'] == "Vol1 Ch1"

        # Verifica che i capitoli del volume 2 non siano influenzati
        chapters_vol2 = db_manager.get_chapters(vol2_id)
        assert len(chapters_vol2) == 1
        assert chapters_vol2[0]['name'] == "Vol2 Ch1"

    def test_update_volumes_order_maintains_database_integrity(self, temp_db):
        """Test che update_volumes_order mantenga integrità referenziale."""
        path, db_manager, test_image = temp_db

        # Crea struttura complessa
        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)

        ch1_id = db_manager.insert_chapter("Ch1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("Ch2", 1, vol2_id)

        db_manager.insert_page(ch1_id, 1, test_image)
        db_manager.insert_page(ch2_id, 1, test_image)

        # Riordina volumi
        db_manager.update_volumes_order([vol2_id, vol1_id])

        # Verifica integrità completa della gerarchia
        import sqlite3
        with sqlite3.connect(path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Verifica che i capitoli siano ancora associati ai volumi corretti
            cursor.execute('SELECT * FROM chapters WHERE volume_id = ?', (vol1_id,))
            ch_vol1 = cursor.fetchall()
            assert len(ch_vol1) == 1
            assert ch_vol1[0]['name'] == "Ch1"

            cursor.execute('SELECT * FROM chapters WHERE volume_id = ?', (vol2_id,))
            ch_vol2 = cursor.fetchall()
            assert len(ch_vol2) == 1
            assert ch_vol2[0]['name'] == "Ch2"

            # Verifica che le pagine esistano ancora
            cursor.execute('SELECT COUNT(*) FROM pages')
            page_count = cursor.fetchone()[0]
            assert page_count == 2

    def test_update_volumes_order_with_cover_data(self, temp_db):
        """Test che update_volumes_order preservi cover data."""
        path, db_manager, test_image = temp_db

        # Crea volumi con cover
        cover1 = b"cover_data_1"
        cover2 = b"cover_data_2"

        vol1_id = db_manager.insert_volume("Volume 1", 1, cover1)
        vol2_id = db_manager.insert_volume("Volume 2", 2, cover2)

        # Riordina
        db_manager.update_volumes_order([vol2_id, vol1_id])

        # Verifica che le cover siano preservate
        volumes = db_manager.get_volumes()
        assert volumes[0]['name'] == "Volume 2"
        assert volumes[0]['cover'] == cover2
        assert volumes[1]['name'] == "Volume 1"
        assert volumes[1]['cover'] == cover1

    def test_update_volumes_order_stress_test(self, temp_db):
        """Test stress: riordina 50 volumi multiple volte."""
        path, db_manager, test_image = temp_db

        # Crea 50 volumi
        volume_ids = []
        for i in range(1, 51):
            vol_id = db_manager.insert_volume(f"Volume {i}", i)
            volume_ids.append(vol_id)

        # Riordina 5 volte con ordini diversi
        import random
        for iteration in range(5):
            shuffled = volume_ids.copy()
            random.shuffle(shuffled)
            result = db_manager.update_volumes_order(shuffled)
            assert result is True

        # Verifica che tutti i volumi esistano ancora
        volumes = db_manager.get_volumes()
        assert len(volumes) == 50

        # Verifica che gli ordini siano sequenziali 1-50
        for i, vol in enumerate(volumes):
            assert vol['order'] == i + 1

    def test_update_volumes_order_idempotency(self, temp_db):
        """Test che riordinare con stesso ordine sia idempotente."""
        path, db_manager, test_image = temp_db

        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)
        vol3_id = db_manager.insert_volume("Volume 3", 3)

        # Riordina
        new_order = [vol3_id, vol1_id, vol2_id]
        db_manager.update_volumes_order(new_order)

        # Riordina di nuovo con stesso ordine
        result = db_manager.update_volumes_order(new_order)
        assert result is True

        # Verifica che l'ordine sia ancora lo stesso
        volumes = db_manager.get_volumes()
        assert volumes[0]['name'] == "Volume 3"
        assert volumes[1]['name'] == "Volume 1"
        assert volumes[2]['name'] == "Volume 2"

    def test_update_volumes_order_after_multiple_operations(self, temp_db):
        """Test riordinamento dopo operazioni CRUD complesse."""
        path, db_manager, test_image = temp_db

        # Fase 1: Crea 5 volumi
        vol_ids = [db_manager.insert_volume(f"Vol {i}", i) for i in range(1, 6)]

        # Fase 2: Aggiorna nome di alcuni volumi
        db_manager.update_volume(vol_ids[1], "Volume 2 Renamed", 2, None)
        db_manager.update_volume(vol_ids[3], "Volume 4 Renamed", 4, None)

        # Fase 3: Elimina un volume
        db_manager.delete_volume(vol_ids[2])  # Elimina Volume 3
        vol_ids.pop(2)  # Rimuovi dalla lista

        # Fase 4: Aggiungi nuovo volume
        new_vol_id = db_manager.insert_volume("New Volume", 99)
        vol_ids.append(new_vol_id)

        # Fase 5: Riordina tutti i volumi rimasti
        import random
        shuffled = vol_ids.copy()
        random.shuffle(shuffled)
        result = db_manager.update_volumes_order(shuffled)
        assert result is True

        # Verifica consistenza finale
        volumes = db_manager.get_volumes()
        assert len(volumes) == 5  # 5 volumi originali - 1 eliminato + 1 nuovo

        # Verifica che ordini siano sequenziali
        for i, vol in enumerate(volumes):
            assert vol['order'] == i + 1

    def test_update_volumes_order_zero_volumes(self):
        """Test update_volumes_order su database senza volumi."""
        import tempfile
        fd, path = tempfile.mkstemp(suffix='.manga')
        os.close(fd)

        db_manager = MangaDatabaseManager(path)
        db_manager.insert_metadata("Test", "Author", "Desc")

        # Riordina lista vuota su database vuoto
        result = db_manager.update_volumes_order([])
        assert result is True

        volumes = db_manager.get_volumes()
        assert volumes == []

        db_manager.close()
        os.remove(path)

    def test_complete_workflow_with_reordering(self, temp_db):
        """
        Smoke test completo: workflow realistico con tutte le operazioni.
        Se questo test passa, il sistema funziona correttamente end-to-end.
        """
        path, db_manager, test_image = temp_db

        # STEP 1: Crea struttura manga completa
        vol1_id = db_manager.insert_volume("Volume 1: Beginning", 1, b"cover1")
        vol2_id = db_manager.insert_volume("Volume 2: Rising Action", 2, b"cover2")
        vol3_id = db_manager.insert_volume("Volume 3: Climax", 3, b"cover3")

        # STEP 2: Aggiungi capitoli a ogni volume
        v1_ch1 = db_manager.insert_chapter("Chapter 1", 1, vol1_id)
        v1_ch2 = db_manager.insert_chapter("Chapter 2", 2, vol1_id)

        v2_ch1 = db_manager.insert_chapter("Chapter 3", 1, vol2_id)
        v2_ch2 = db_manager.insert_chapter("Chapter 4", 2, vol2_id)

        v3_ch1 = db_manager.insert_chapter("Chapter 5", 1, vol3_id)

        # STEP 3: Aggiungi pagine a ogni capitolo
        for i in range(1, 6):
            db_manager.insert_page(v1_ch1, i, test_image)
            db_manager.insert_page(v1_ch2, i, test_image)
            db_manager.insert_page(v2_ch1, i, test_image)
            db_manager.insert_page(v2_ch2, i, test_image)
            db_manager.insert_page(v3_ch1, i, test_image)

        # STEP 4: Riordina volumi (user cambia idea sull'ordine)
        db_manager.update_volumes_order([vol2_id, vol1_id, vol3_id])

        # STEP 5: Aggiorna nome di un volume
        db_manager.update_volume(vol1_id, "Volume 1: The Beginning (Revised)", 2, b"cover1")

        # STEP 6: Riordina capitoli in un volume
        db_manager.update_chapters_order([v1_ch2, v1_ch1])

        # STEP 7: Aggiungi bookmark e reading history
        bookmark_id = db_manager.add_bookmark(v2_ch1, 3, "Great scene!", "default")
        db_manager.save_reading_position(v2_ch2, 2, "default")

        # STEP 8: Aggiungi nuovo volume e riordina di nuovo
        vol4_id = db_manager.insert_volume("Volume 4: Epilogue", 4)
        db_manager.update_volumes_order([vol2_id, vol1_id, vol3_id, vol4_id])

        # STEP 9: Elimina un capitolo
        db_manager.delete_chapter_and_pages(v3_ch1)

        # STEP 10: Verifica COMPLETA dello stato finale
        # ================================================

        # Verifica volumi
        volumes = db_manager.get_volumes()
        assert len(volumes) == 4
        assert volumes[0]['name'] == "Volume 2: Rising Action"
        assert volumes[0]['order'] == 1
        assert volumes[1]['name'] == "Volume 1: The Beginning (Revised)"
        assert volumes[1]['order'] == 2
        assert volumes[2]['name'] == "Volume 3: Climax"
        assert volumes[2]['order'] == 3
        assert volumes[3]['name'] == "Volume 4: Epilogue"
        assert volumes[3]['order'] == 4

        # Verifica cover preservate
        assert volumes[0]['cover'] == b"cover2"
        assert volumes[1]['cover'] == b"cover1"

        # Verifica capitoli del volume 1 (riordinati)
        v1_chapters = db_manager.get_chapters(vol1_id)
        assert len(v1_chapters) == 2
        assert v1_chapters[0]['name'] == "Chapter 2"
        assert v1_chapters[1]['name'] == "Chapter 1"

        # Verifica capitoli del volume 2 (non modificati)
        v2_chapters = db_manager.get_chapters(vol2_id)
        assert len(v2_chapters) == 2

        # Verifica capitoli del volume 3 (eliminato)
        v3_chapters = db_manager.get_chapters(vol3_id)
        assert len(v3_chapters) == 0

        # Verifica pagine
        v1_ch1_pages = db_manager.get_pages(v1_ch1)
        assert len(v1_ch1_pages) == 5

        # Verifica bookmark
        bookmarks = db_manager.get_bookmarks("default")
        assert len(bookmarks) == 1
        assert bookmarks[0]['page_number'] == 3

        # Verifica reading position
        reading_pos = db_manager.get_last_reading_position("default")
        assert reading_pos is not None
        assert reading_pos['page_number'] == 2

        # Verifica integrità database (query diretta)
        import sqlite3
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()

            # Conta totale entità
            cursor.execute("SELECT COUNT(*) FROM volumes")
            assert cursor.fetchone()[0] == 4

            cursor.execute("SELECT COUNT(*) FROM chapters")
            assert cursor.fetchone()[0] == 4  # 5 originali - 1 eliminato

            cursor.execute("SELECT COUNT(*) FROM pages")
            assert cursor.fetchone()[0] == 20  # 25 originali - 5 eliminate con chapter

            # Verifica che tutti gli ordini siano validi (no NULL, no negativi)
            cursor.execute("SELECT COUNT(*) FROM volumes WHERE \"order\" IS NULL OR \"order\" < 1")
            assert cursor.fetchone()[0] == 0

            cursor.execute("SELECT COUNT(*) FROM chapters WHERE \"order\" IS NULL OR \"order\" < 1")
            assert cursor.fetchone()[0] == 0

        # Se arriviamo qui, TUTTO funziona correttamente! 🎯
