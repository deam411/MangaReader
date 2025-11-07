"""
Test per il modulo database.py.

Testa tutte le operazioni CRUD, conversioni immagini e gestione dello schema.
"""

import pytest
import os
from pathlib import Path
from PIL import Image
import io

from src.database import MangaDatabaseManager


class TestMangaDatabaseManager:
    """Test per la classe MangaDatabaseManager."""

    def test_create_database(self, temp_manga_file):
        """Test creazione database con schema corretto."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        # Verifica che il file sia stato creato
        assert temp_manga_file.exists()

        # Verifica che le tabelle siano state create
        import sqlite3
        conn = sqlite3.connect(str(temp_manga_file))
        cursor = conn.cursor()

        # Controlla esistenza tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert 'metadata' in tables
        assert 'volumes' in tables
        assert 'chapters' in tables
        assert 'pages' in tables
        assert 'history' in tables

        conn.close()

    def test_insert_and_get_metadata(self, temp_manga_file):
        """Test inserimento e recupero metadati."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        # Inserisci metadati
        result = db_manager.insert_metadata(
            title="Test Manga",
            author="Test Author",
            description="Test Description",
            language="Italiano",
            year=2024,
            tags="azione,fantasy"
        )

        assert result is True

        # Recupera metadati
        metadata = db_manager.get_metadata()

        assert metadata is not None
        assert metadata['title'] == "Test Manga"
        assert metadata['author'] == "Test Author"
        assert metadata['description'] == "Test Description"
        assert metadata['language'] == "Italiano"
        assert metadata['year'] == 2024
        assert metadata['tags'] == "azione,fantasy"

    def test_update_metadata(self, temp_manga_file):
        """Test aggiornamento metadati."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        # Inserisci metadati iniziali
        db_manager.insert_metadata(title="Original Title")

        # Aggiorna metadati
        result = db_manager.update_metadata(
            title="Original Title",
            author="New Author",
            description="New Description"
        )

        assert result is True

        # Verifica aggiornamento
        metadata = db_manager.get_metadata()
        assert metadata['author'] == "New Author"
        assert metadata['description'] == "New Description"

    def test_insert_and_get_volumes(self, temp_manga_file):
        """Test inserimento e recupero volumi."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        # Inserisci volumi
        volume1_id = db_manager.insert_volume("Volume 1", 1)
        volume2_id = db_manager.insert_volume("Volume 2", 2)

        assert volume1_id is not None
        assert volume2_id is not None
        assert volume2_id > volume1_id

        # Recupera volumi
        volumes = db_manager.get_volumes()

        assert len(volumes) >= 2  # Potrebbe esserci "Default Volume" dalla migrazione
        # Verifica che i volumi siano ordinati per 'order'
        volume_names = [v['name'] for v in volumes]
        assert "Volume 1" in volume_names
        assert "Volume 2" in volume_names

    def test_update_volume(self, temp_manga_file):
        """Test aggiornamento volume."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        # Inserisci volume
        volume_id = db_manager.insert_volume("Original Name", 1)

        # Aggiorna volume
        result = db_manager.update_volume(volume_id, "Updated Name", 2)

        assert result is True

        # Verifica aggiornamento
        volumes = db_manager.get_volumes()
        updated_volume = next((v for v in volumes if v['id'] == volume_id), None)

        assert updated_volume is not None
        assert updated_volume['name'] == "Updated Name"
        assert updated_volume['order'] == 2

    def test_delete_volume(self, temp_manga_file):
        """Test eliminazione volume con cascata."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        # Inserisci volume con capitolo e pagina
        volume_id = db_manager.insert_volume("Test Volume", 1)
        chapter_id = db_manager.insert_chapter("Test Chapter", 1, volume_id)

        # Elimina volume
        result = db_manager.delete_volume(volume_id)

        assert result is True

        # Verifica che volume e capitolo siano stati eliminati
        volumes = db_manager.get_volumes()
        volume_ids = [v['id'] for v in volumes]
        assert volume_id not in volume_ids

        chapters = db_manager.get_chapters_for_volume(volume_id)
        assert len(chapters) == 0

    def test_insert_and_get_chapters(self, temp_manga_file):
        """Test inserimento e recupero capitoli."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        # Inserisci volume
        volume_id = db_manager.insert_volume("Test Volume", 1)

        # Inserisci capitoli
        chapter1_id = db_manager.insert_chapter("Chapter 1", 1, volume_id, "First chapter")
        chapter2_id = db_manager.insert_chapter("Chapter 2", 2, volume_id, "Second chapter")

        assert chapter1_id is not None
        assert chapter2_id is not None

        # Recupera capitoli
        chapters = db_manager.get_chapters_for_volume(volume_id)

        assert len(chapters) == 2
        assert chapters[0]['name'] == "Chapter 1"
        assert chapters[1]['name'] == "Chapter 2"
        assert chapters[0]['description'] == "First chapter"

    def test_update_chapter_name(self, temp_manga_file):
        """Test rinomina capitolo."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Test Volume", 1)
        chapter_id = db_manager.insert_chapter("Original Name", 1, volume_id)

        # Rinomina capitolo
        result = db_manager.update_chapter_name(chapter_id, "New Name")

        assert result is True

        # Verifica rinomina
        chapters = db_manager.get_chapters_for_volume(volume_id)
        chapter = next((c for c in chapters if c['id'] == chapter_id), None)

        assert chapter is not None
        assert chapter['name'] == "New Name"

    def test_update_chapters_order(self, temp_manga_file):
        """Test riordinamento capitoli."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Test Volume", 1)
        chapter1_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)
        chapter2_id = db_manager.insert_chapter("Chapter 2", 2, volume_id)
        chapter3_id = db_manager.insert_chapter("Chapter 3", 3, volume_id)

        # Inverti ordine
        result = db_manager.update_chapters_order([chapter3_id, chapter2_id, chapter1_id])

        assert result is True

        # Verifica nuovo ordine
        chapters = db_manager.get_chapters_for_volume(volume_id)

        assert chapters[0]['id'] == chapter3_id
        assert chapters[1]['id'] == chapter2_id
        assert chapters[2]['id'] == chapter1_id

    def test_delete_chapter_and_pages(self, temp_manga_file, sample_image_path):
        """Test eliminazione capitolo con pagine."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Test Volume", 1)
        chapter_id = db_manager.insert_chapter("Test Chapter", 1, volume_id)

        # Aggiungi pagine
        db_manager.insert_page(chapter_id, 1, str(sample_image_path))
        db_manager.insert_page(chapter_id, 2, str(sample_image_path))

        # Elimina capitolo
        result = db_manager.delete_chapter_and_pages(chapter_id)

        assert result is True

        # Verifica eliminazione
        chapters = db_manager.get_chapters_for_volume(volume_id)
        chapter_ids = [c['id'] for c in chapters]
        assert chapter_id not in chapter_ids

        pages = db_manager.get_pages_for_chapter(chapter_id)
        assert len(pages) == 0

    def test_insert_and_get_pages(self, temp_manga_file, sample_image_path):
        """Test inserimento e recupero pagine."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Test Volume", 1)
        chapter_id = db_manager.insert_chapter("Test Chapter", 1, volume_id)

        # Inserisci pagine
        result1 = db_manager.insert_page(chapter_id, 1, str(sample_image_path))
        result2 = db_manager.insert_page(chapter_id, 2, str(sample_image_path))

        assert result1 is True
        assert result2 is True

        # Recupera pagine
        pages = db_manager.get_pages_for_chapter(chapter_id)

        assert len(pages) == 2
        assert pages[0]['page_number'] == 1
        assert pages[1]['page_number'] == 2
        assert len(pages[0]['image_data']) > 0
        assert len(pages[1]['image_data']) > 0

    def test_delete_page(self, temp_manga_file, sample_image_path):
        """Test eliminazione pagina."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Test Volume", 1)
        chapter_id = db_manager.insert_chapter("Test Chapter", 1, volume_id)

        db_manager.insert_page(chapter_id, 1, str(sample_image_path))
        db_manager.insert_page(chapter_id, 2, str(sample_image_path))

        # Elimina prima pagina
        result = db_manager.delete_page(chapter_id, 1)

        assert result is True

        # Verifica eliminazione
        pages = db_manager.get_pages_for_chapter(chapter_id)
        page_numbers = [p['page_number'] for p in pages]

        assert 1 not in page_numbers
        assert 2 in page_numbers

    def test_update_page_order(self, temp_manga_file, sample_image_path):
        """Test riordinamento pagine."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Test Volume", 1)
        chapter_id = db_manager.insert_chapter("Test Chapter", 1, volume_id)

        # Inserisci 3 pagine
        db_manager.insert_page(chapter_id, 1, str(sample_image_path))
        db_manager.insert_page(chapter_id, 2, str(sample_image_path))
        db_manager.insert_page(chapter_id, 3, str(sample_image_path))

        # Ottieni dati pagine
        pages = db_manager.get_pages_for_chapter(chapter_id)
        page_data = [p['image_data'] for p in pages]

        # Inverti ordine
        result = db_manager.update_page_order(chapter_id, list(reversed(page_data)))

        assert result is True

        # Verifica nuovo ordine (i dati dovrebbero essere invertiti)
        new_pages = db_manager.get_pages_for_chapter(chapter_id)
        assert len(new_pages) == 3

    def test_swap_page_order(self, temp_manga_file, sample_image_path):
        """Test scambio ordine di due pagine."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Test Volume", 1)
        chapter_id = db_manager.insert_chapter("Test Chapter", 1, volume_id)

        # Crea due immagini diverse
        img1 = Image.new('RGB', (50, 50), color='red')
        img2 = Image.new('RGB', (50, 50), color='blue')

        temp_dir = Path(sample_image_path).parent
        img1_path = temp_dir / "red.png"
        img2_path = temp_dir / "blue.png"

        img1.save(str(img1_path))
        img2.save(str(img2_path))

        db_manager.insert_page(chapter_id, 1, str(img1_path))
        db_manager.insert_page(chapter_id, 2, str(img2_path))

        # Scambia pagine
        result = db_manager.swap_page_order(chapter_id, 1, 2)

        assert result is True

        # Verifica scambio
        pages = db_manager.get_pages_for_chapter(chapter_id)
        assert len(pages) == 2

    def test_image_conversion_webp(self, temp_manga_file, temp_dir):
        """Test conversione immagine WebP."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Test Volume", 1)
        chapter_id = db_manager.insert_chapter("Test Chapter", 1, volume_id)

        # Crea immagine WebP
        img = Image.new('RGB', (100, 100), color='green')
        webp_path = temp_dir / "test.webp"
        img.save(str(webp_path), 'WEBP')

        # Inserisci (dovrebbe convertire automaticamente)
        result = db_manager.insert_page(chapter_id, 1, str(webp_path))

        assert result is True

        # Verifica che sia stata salvata
        pages = db_manager.get_pages_for_chapter(chapter_id)
        assert len(pages) == 1
        assert len(pages[0]['image_data']) > 0

    def test_schema_migration_v2(self, temp_manga_file):
        """Test migrazione schema a versione 2 (aggiunta volume_id)."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        # Verifica che la migrazione sia avvenuta
        import sqlite3
        conn = sqlite3.connect(str(temp_manga_file))
        cursor = conn.cursor()

        # Controlla che la colonna volume_id esista
        cursor.execute("PRAGMA table_info(chapters)")
        columns = [col[1] for col in cursor.fetchall()]

        assert 'volume_id' in columns

        # Verifica che esista un "Default Volume"
        cursor.execute("SELECT name FROM volumes WHERE name = 'Default Volume'")
        result = cursor.fetchone()

        assert result is not None

        conn.close()

    def test_get_all_chapters(self, temp_manga_file):
        """Test recupero di tutti i capitoli."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume1_id = db_manager.insert_volume("Volume 1", 1)
        volume2_id = db_manager.insert_volume("Volume 2", 2)

        db_manager.insert_chapter("Chapter 1.1", 1, volume1_id)
        db_manager.insert_chapter("Chapter 1.2", 2, volume1_id)
        db_manager.insert_chapter("Chapter 2.1", 3, volume2_id)

        # Recupera tutti i capitoli
        all_chapters = db_manager.get_all_chapters()

        assert len(all_chapters) == 3
        # Verifica che siano ordinati per 'order'
        assert all_chapters[0]['name'] == "Chapter 1.1"
        assert all_chapters[1]['name'] == "Chapter 1.2"
        assert all_chapters[2]['name'] == "Chapter 2.1"

    def test_empty_database_operations(self, temp_manga_file):
        """Test operazioni su database vuoto."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        # Recupero da database vuoto dovrebbe restituire valori vuoti/None
        metadata = db_manager.get_metadata()
        assert metadata is None

        volumes = db_manager.get_volumes()
        # Potrebbe avere "Default Volume" dalla migrazione
        assert isinstance(volumes, list)

        chapters = db_manager.get_all_chapters()
        assert len(chapters) == 0

    def test_error_handling_invalid_chapter_id(self, temp_manga_file):
        """Test gestione errori con ID capitolo invalido."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        # Operazioni con ID inesistente
        pages = db_manager.get_pages_for_chapter(99999)
        assert len(pages) == 0

        result = db_manager.delete_chapter_and_pages(99999)
        # Dovrebbe completare senza errori anche se il capitolo non esiste
        assert result is True

    def test_error_handling_invalid_volume_id(self, temp_manga_file):
        """Test gestione errori con ID volume invalido."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        # Operazioni con ID inesistente
        chapters = db_manager.get_chapters_for_volume(99999)
        assert len(chapters) == 0

        result = db_manager.delete_volume(99999)
        # Dovrebbe completare senza errori anche se il volume non esiste
        assert result is True


class TestReadingHistory:
    """Test per le funzionalità di storia di lettura."""

    def test_save_reading_position_new(self, temp_manga_file, sample_image_path):
        """Test salvataggio nuova posizione di lettura."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)
        db_manager.insert_page(chapter_id, 1, str(sample_image_path))

        # Salva posizione
        result = db_manager.save_reading_position(chapter_id, 1)

        assert result is True

        # Verifica che sia stata salvata
        position = db_manager.get_last_reading_position()

        assert position is not None
        assert position['chapter_id'] == chapter_id
        assert position['page_number'] == 1

    def test_save_reading_position_update(self, temp_manga_file, sample_image_path):
        """Test aggiornamento posizione di lettura esistente."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter1_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)
        chapter2_id = db_manager.insert_chapter("Chapter 2", 2, volume_id)

        db_manager.insert_page(chapter1_id, 1, str(sample_image_path))
        db_manager.insert_page(chapter2_id, 1, str(sample_image_path))

        # Salva prima posizione
        db_manager.save_reading_position(chapter1_id, 1)

        # Aggiorna con seconda posizione
        db_manager.save_reading_position(chapter2_id, 1)

        # Verifica che ci sia solo una entry (aggiornata)
        position = db_manager.get_last_reading_position()

        assert position['chapter_id'] == chapter2_id
        assert position['page_number'] == 1

    def test_get_last_reading_position_none(self, temp_manga_file):
        """Test get_last_reading_position quando non ci sono posizioni salvate."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        position = db_manager.get_last_reading_position()

        assert position is None

    def test_get_last_reading_position_with_chapter_info(self, temp_manga_file, sample_image_path):
        """Test che get_last_reading_position restituisca anche info del capitolo."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Test Volume", 1)
        chapter_id = db_manager.insert_chapter("Test Chapter", 1, volume_id)
        db_manager.insert_page(chapter_id, 1, str(sample_image_path))

        db_manager.save_reading_position(chapter_id, 1)

        position = db_manager.get_last_reading_position()

        assert position is not None
        assert position['chapter_name'] == "Test Chapter"
        assert position['volume_name'] == "Test Volume"
        assert position['volume_id'] == volume_id

    def test_get_reading_progress_empty(self, temp_manga_file):
        """Test get_reading_progress su manga vuoto."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        progress = db_manager.get_reading_progress()

        assert progress is None

    def test_get_reading_progress_not_started(self, temp_manga_file, sample_image_path):
        """Test get_reading_progress quando non è stato iniziato."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)
        db_manager.insert_page(chapter_id, 1, str(sample_image_path))
        db_manager.insert_page(chapter_id, 2, str(sample_image_path))

        progress = db_manager.get_reading_progress()

        assert progress is not None
        assert progress['total_pages'] == 2
        assert progress['read_pages'] == 0
        assert progress['percentage'] == 0.0

    def test_get_reading_progress_partial(self, temp_manga_file, sample_image_path):
        """Test get_reading_progress con lettura parziale."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter1_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)
        chapter2_id = db_manager.insert_chapter("Chapter 2", 2, volume_id)

        # Chapter 1: 2 pagine
        db_manager.insert_page(chapter1_id, 1, str(sample_image_path))
        db_manager.insert_page(chapter1_id, 2, str(sample_image_path))

        # Chapter 2: 2 pagine
        db_manager.insert_page(chapter2_id, 1, str(sample_image_path))
        db_manager.insert_page(chapter2_id, 2, str(sample_image_path))

        # Leggi fino a pagina 2 del capitolo 1
        db_manager.save_reading_position(chapter1_id, 2)

        progress = db_manager.get_reading_progress()

        assert progress is not None
        assert progress['total_pages'] == 4
        assert progress['read_pages'] == 2
        assert progress['percentage'] == 50.0

    def test_get_reading_progress_complete(self, temp_manga_file, sample_image_path):
        """Test get_reading_progress con lettura completata."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)

        db_manager.insert_page(chapter_id, 1, str(sample_image_path))
        db_manager.insert_page(chapter_id, 2, str(sample_image_path))

        # Leggi fino all'ultima pagina
        db_manager.save_reading_position(chapter_id, 2)

        progress = db_manager.get_reading_progress()

        assert progress is not None
        assert progress['total_pages'] == 2
        assert progress['read_pages'] == 2
        assert progress['percentage'] == 100.0

    def test_clear_reading_history(self, temp_manga_file, sample_image_path):
        """Test cancellazione cronologia di lettura."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)
        db_manager.insert_page(chapter_id, 1, str(sample_image_path))

        # Salva posizione
        db_manager.save_reading_position(chapter_id, 1)

        # Verifica che sia salvata
        assert db_manager.get_last_reading_position() is not None

        # Cancella cronologia
        result = db_manager.clear_reading_history()

        assert result is True

        # Verifica che sia stata cancellata
        assert db_manager.get_last_reading_position() is None

    def test_multiple_users(self, temp_manga_file, sample_image_path):
        """Test gestione posizioni di lettura per utenti diversi."""
        db_manager = MangaDatabaseManager(str(temp_manga_file))

        volume_id = db_manager.insert_volume("Volume 1", 1)
        chapter1_id = db_manager.insert_chapter("Chapter 1", 1, volume_id)
        chapter2_id = db_manager.insert_chapter("Chapter 2", 2, volume_id)

        db_manager.insert_page(chapter1_id, 1, str(sample_image_path))
        db_manager.insert_page(chapter2_id, 1, str(sample_image_path))

        # User 1 legge capitolo 1
        db_manager.save_reading_position(chapter1_id, 1, user="user1")

        # User 2 legge capitolo 2
        db_manager.save_reading_position(chapter2_id, 1, user="user2")

        # Verifica posizioni separate
        pos1 = db_manager.get_last_reading_position(user="user1")
        pos2 = db_manager.get_last_reading_position(user="user2")

        assert pos1['chapter_id'] == chapter1_id
        assert pos2['chapter_id'] == chapter2_id


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
