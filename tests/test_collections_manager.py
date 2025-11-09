"""
Test suite completa per il Collections Manager (v0.3.0).

Verifica funzionalità di creazione, gestione e persistenza delle collezioni.
"""
import pytest
import os
import tempfile
import sqlite3
from datetime import datetime
from src.collections.collection_manager import CollectionManager


class TestCollectionsManager:
    """Test suite per Collections Manager."""

    @pytest.fixture
    def temp_collections_db(self, monkeypatch, tmp_path):
        """Crea un database collezioni temporaneo per i test."""
        # Override del path del database per usare temp directory
        db_path = tmp_path / "test_collections.db"

        # Monkey patch get_app_data_dir per usare temp directory
        def mock_get_app_data_dir():
            return str(tmp_path)

        monkeypatch.setattr("src.collections.collection_manager.get_app_data_dir",
                           mock_get_app_data_dir)

        manager = CollectionManager()
        yield manager, str(db_path)

        # Cleanup
        manager.close()

    def test_database_initialization(self, temp_collections_db):
        """Test creazione e inizializzazione database."""
        manager, db_path = temp_collections_db

        assert os.path.exists(db_path)

        # Verifica schema database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Verifica tabella collections
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='collections'
            """)
            assert cursor.fetchone() is not None

            # Verifica tabella collection_items
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='collection_items'
            """)
            assert cursor.fetchone() is not None

    def test_create_collection_success(self, temp_collections_db):
        """Test creazione collezione con successo."""
        manager, _ = temp_collections_db

        result = manager.create_collection(
            name="Shonen Jump",
            description="Best shonen manga"
        )

        assert result is True

        # Verifica che la collezione esista
        collections = manager.get_all_collections()
        assert len(collections) == 1
        assert collections[0]['name'] == "Shonen Jump"
        assert collections[0]['description'] == "Best shonen manga"
        assert 'created_at' in collections[0]
        assert 'id' in collections[0]

    def test_create_collection_duplicate_name(self, temp_collections_db):
        """Test creazione collezione con nome duplicato."""
        manager, _ = temp_collections_db

        manager.create_collection("Action", "Action manga")
        result = manager.create_collection("Action", "More action")

        # Non dovrebbe creare duplicati
        assert result is False

        collections = manager.get_all_collections()
        assert len(collections) == 1

    def test_create_multiple_collections(self, temp_collections_db):
        """Test creazione multiple collezioni."""
        manager, _ = temp_collections_db

        manager.create_collection("Action", "Action manga")
        manager.create_collection("Romance", "Romance manga")
        manager.create_collection("Sci-Fi", "Science fiction")

        collections = manager.get_all_collections()
        assert len(collections) == 3

        names = [c['name'] for c in collections]
        assert "Action" in names
        assert "Romance" in names
        assert "Sci-Fi" in names

    def test_delete_collection_success(self, temp_collections_db):
        """Test eliminazione collezione con successo."""
        manager, _ = temp_collections_db

        manager.create_collection("To Delete", "Will be deleted")
        collections = manager.get_all_collections()
        collection_id = collections[0]['id']

        result = manager.delete_collection(collection_id)
        assert result is True

        # Verifica che sia stata eliminata
        collections = manager.get_all_collections()
        assert len(collections) == 0

    def test_delete_nonexistent_collection(self, temp_collections_db):
        """Test eliminazione collezione inesistente."""
        manager, _ = temp_collections_db

        result = manager.delete_collection(999)
        assert result is False

    def test_delete_collection_cascades_items(self, temp_collections_db):
        """Test che eliminare collezione rimuova anche i suoi items."""
        manager, _ = temp_collections_db

        manager.create_collection("Test", "Test collection")
        collections = manager.get_all_collections()
        collection_id = collections[0]['id']

        # Aggiungi manga alla collezione
        manager.add_to_collection(collection_id, "/path/to/manga1.manga")
        manager.add_to_collection(collection_id, "/path/to/manga2.manga")

        # Verifica items aggiunti
        items = manager.get_collection_items(collection_id)
        assert len(items) == 2

        # Elimina collezione
        manager.delete_collection(collection_id)

        # Verifica che gli items siano stati eliminati (CASCADE)
        items = manager.get_collection_items(collection_id)
        assert len(items) == 0

    def test_add_to_collection_success(self, temp_collections_db):
        """Test aggiunta manga a collezione."""
        manager, _ = temp_collections_db

        manager.create_collection("Favorites", "My favorites")
        collections = manager.get_all_collections()
        collection_id = collections[0]['id']

        result = manager.add_to_collection(collection_id, "/manga/naruto.manga")
        assert result is True

        items = manager.get_collection_items(collection_id)
        assert len(items) == 1
        assert items[0]['manga_path'] == "/manga/naruto.manga"
        assert 'added_at' in items[0]

    def test_add_duplicate_to_collection(self, temp_collections_db):
        """Test aggiunta stesso manga due volte alla stessa collezione."""
        manager, _ = temp_collections_db

        manager.create_collection("Test", "Test")
        collections = manager.get_all_collections()
        collection_id = collections[0]['id']

        manager.add_to_collection(collection_id, "/manga/same.manga")
        result = manager.add_to_collection(collection_id, "/manga/same.manga")

        # Non dovrebbe creare duplicati
        assert result is False

        items = manager.get_collection_items(collection_id)
        assert len(items) == 1

    def test_add_multiple_manga_to_collection(self, temp_collections_db):
        """Test aggiunta multipli manga a collezione."""
        manager, _ = temp_collections_db

        manager.create_collection("Library", "Full library")
        collections = manager.get_all_collections()
        collection_id = collections[0]['id']

        manga_paths = [
            "/manga/one_piece.manga",
            "/manga/naruto.manga",
            "/manga/bleach.manga",
            "/manga/dragon_ball.manga"
        ]

        for path in manga_paths:
            manager.add_to_collection(collection_id, path)

        items = manager.get_collection_items(collection_id)
        assert len(items) == 4

        paths = [item['manga_path'] for item in items]
        assert all(path in paths for path in manga_paths)

    def test_add_to_nonexistent_collection(self, temp_collections_db):
        """Test aggiunta manga a collezione inesistente."""
        manager, _ = temp_collections_db

        result = manager.add_to_collection(999, "/manga/test.manga")
        assert result is False

    def test_remove_from_collection_success(self, temp_collections_db):
        """Test rimozione manga da collezione."""
        manager, _ = temp_collections_db

        manager.create_collection("Test", "Test")
        collections = manager.get_all_collections()
        collection_id = collections[0]['id']

        manager.add_to_collection(collection_id, "/manga/to_remove.manga")

        result = manager.remove_from_collection(collection_id, "/manga/to_remove.manga")
        assert result is True

        items = manager.get_collection_items(collection_id)
        assert len(items) == 0

    def test_remove_nonexistent_from_collection(self, temp_collections_db):
        """Test rimozione manga non presente in collezione."""
        manager, _ = temp_collections_db

        manager.create_collection("Test", "Test")
        collections = manager.get_all_collections()
        collection_id = collections[0]['id']

        result = manager.remove_from_collection(collection_id, "/manga/not_there.manga")
        assert result is False

    def test_get_collections_for_manga_empty(self, temp_collections_db):
        """Test recupero collezioni per manga non presente in alcuna collezione."""
        manager, _ = temp_collections_db

        manager.create_collection("Collection1", "Test 1")
        manager.create_collection("Collection2", "Test 2")

        collections = manager.get_collections_for_manga("/manga/not_added.manga")
        assert len(collections) == 0

    def test_get_collections_for_manga_single(self, temp_collections_db):
        """Test recupero collezioni per manga in una sola collezione."""
        manager, _ = temp_collections_db

        manager.create_collection("Favorites", "My favorites")
        collections = manager.get_all_collections()
        collection_id = collections[0]['id']

        manga_path = "/manga/naruto.manga"
        manager.add_to_collection(collection_id, manga_path)

        manga_collections = manager.get_collections_for_manga(manga_path)
        assert len(manga_collections) == 1
        assert manga_collections[0]['name'] == "Favorites"

    def test_get_collections_for_manga_multiple(self, temp_collections_db):
        """Test recupero collezioni per manga in multiple collezioni."""
        manager, _ = temp_collections_db

        manager.create_collection("Action", "Action manga")
        manager.create_collection("Favorites", "Favorites")
        manager.create_collection("Complete", "Completed series")

        collections = manager.get_all_collections()

        manga_path = "/manga/one_piece.manga"

        # Aggiungi stesso manga a tutte e tre le collezioni
        for collection in collections:
            manager.add_to_collection(collection['id'], manga_path)

        manga_collections = manager.get_collections_for_manga(manga_path)
        assert len(manga_collections) == 3

        names = [c['name'] for c in manga_collections]
        assert "Action" in names
        assert "Favorites" in names
        assert "Complete" in names

    def test_rename_collection(self, temp_collections_db):
        """Test rinomina collezione."""
        manager, _ = temp_collections_db

        manager.create_collection("Old Name", "Description")
        collections = manager.get_all_collections()
        collection_id = collections[0]['id']

        result = manager.rename_collection(collection_id, "New Name")
        assert result is True

        collections = manager.get_all_collections()
        assert collections[0]['name'] == "New Name"
        assert collections[0]['description'] == "Description"  # Description unchanged

    def test_update_collection_description(self, temp_collections_db):
        """Test aggiornamento descrizione collezione."""
        manager, _ = temp_collections_db

        manager.create_collection("Test", "Old description")
        collections = manager.get_all_collections()
        collection_id = collections[0]['id']

        result = manager.update_collection_description(collection_id, "New description")
        assert result is True

        collections = manager.get_all_collections()
        assert collections[0]['description'] == "New description"

    def test_get_collection_count(self, temp_collections_db):
        """Test conteggio manga in collezione."""
        manager, _ = temp_collections_db

        manager.create_collection("Test", "Test")
        collections = manager.get_all_collections()
        collection_id = collections[0]['id']

        # Inizialmente vuota
        count = manager.get_collection_count(collection_id)
        assert count == 0

        # Aggiungi manga
        manager.add_to_collection(collection_id, "/manga/manga1.manga")
        manager.add_to_collection(collection_id, "/manga/manga2.manga")
        manager.add_to_collection(collection_id, "/manga/manga3.manga")

        count = manager.get_collection_count(collection_id)
        assert count == 3

    def test_persistence_across_instances(self, temp_collections_db):
        """Test persistenza dati tra diverse istanze del manager."""
        manager1, db_path = temp_collections_db

        # Crea collezione e aggiungi manga con prima istanza
        manager1.create_collection("Persistent", "Test persistence")
        collections = manager1.get_all_collections()
        collection_id = collections[0]['id']
        manager1.add_to_collection(collection_id, "/manga/test.manga")
        manager1.close()

        # Crea seconda istanza e verifica dati persistiti
        from src.collections.collection_manager import CollectionManager
        import importlib
        import sys

        # Ricarica modulo per creare nuova istanza
        if 'src.collections.collection_manager' in sys.modules:
            importlib.reload(sys.modules['src.collections.collection_manager'])

        # Usa stesso db_path
        manager2 = CollectionManager()
        manager2.db_path = db_path
        manager2._init_database()
        manager2._load_collections()

        collections = manager2.get_all_collections()
        assert len(collections) == 1
        assert collections[0]['name'] == "Persistent"

        items = manager2.get_collection_items(collection_id)
        assert len(items) == 1
        assert items[0]['manga_path'] == "/manga/test.manga"

        manager2.close()

    def test_get_all_collections_empty(self, temp_collections_db):
        """Test get_all_collections con database vuoto."""
        manager, _ = temp_collections_db

        collections = manager.get_all_collections()
        assert collections == []

    def test_collection_ordering(self, temp_collections_db):
        """Test ordine collezioni (dovrebbero essere ordinate per created_at)."""
        manager, _ = temp_collections_db

        import time

        manager.create_collection("First", "Created first")
        time.sleep(0.01)  # Piccolo delay per assicurare timestamp diversi
        manager.create_collection("Second", "Created second")
        time.sleep(0.01)
        manager.create_collection("Third", "Created third")

        collections = manager.get_all_collections()

        # Verifica ordine cronologico
        assert collections[0]['name'] == "First"
        assert collections[1]['name'] == "Second"
        assert collections[2]['name'] == "Third"

    def test_transaction_rollback_on_error(self, temp_collections_db):
        """Test rollback transazione in caso di errore."""
        manager, db_path = temp_collections_db

        # Crea collezione valida
        manager.create_collection("Valid", "Valid collection")

        # Simula errore chiudendo il database
        manager.close()

        # Tentativo di operazione dovrebbe fallire gracefully
        result = manager.create_collection("After Close", "Should fail")
        assert result is False

        # Riapri e verifica solo la collezione valida esiste
        from src.collections.collection_manager import CollectionManager
        manager2 = CollectionManager()
        manager2.db_path = db_path
        manager2._init_database()
        manager2._load_collections()

        collections = manager2.get_all_collections()
        assert len(collections) == 1
        assert collections[0]['name'] == "Valid"

        manager2.close()
