"""
Test custom exceptions hierarchy for Phase 3: Code Quality.

Valida che le custom exceptions funzionino correttamente e vengano
usate dai moduli refactorati.
"""

import pytest
import os
import tempfile
import shutil
from src.exceptions import (
    MangaReaderError,
    DatabaseError,
    DatabaseSchemaError,
    DatabaseConnectionError,
    DatabaseQueryError,
    ImportError as MangaImportError,
    FileSizeError,
    CacheError,
    SettingsError,
    SettingsLoadError,
    SettingsSaveError,
)


class TestExceptionHierarchy:
    """Test la gerarchia di eccezioni."""

    def test_base_exception(self):
        """Test eccezione base."""
        exc = MangaReaderError("Test error")
        assert str(exc) == "Test error"
        assert isinstance(exc, Exception)

    def test_database_exceptions(self):
        """Test eccezioni database."""
        exc = DatabaseError("DB error")
        assert isinstance(exc, MangaReaderError)

        exc_schema = DatabaseSchemaError("Schema error")
        assert isinstance(exc_schema, DatabaseError)

        exc_conn = DatabaseConnectionError("Connection error")
        assert isinstance(exc_conn, DatabaseError)

        exc_query = DatabaseQueryError("Query error")
        assert isinstance(exc_query, DatabaseError)

    def test_import_exceptions(self):
        """Test eccezioni import."""
        exc = MangaImportError("Import error")
        assert isinstance(exc, MangaReaderError)

    def test_file_size_error(self):
        """Test FileSizeError con parametri."""
        exc = FileSizeError(100.5, 50)
        assert exc.actual_size_mb == 100.5
        assert exc.max_size_mb == 50
        assert "100.5" in str(exc)
        assert "50" in str(exc)
        assert isinstance(exc, MangaReaderError)

    def test_cache_exceptions(self):
        """Test eccezioni cache."""
        exc = CacheError("Cache error")
        assert isinstance(exc, MangaReaderError)

    def test_settings_exceptions(self):
        """Test eccezioni settings."""
        exc_load = SettingsLoadError("Load error")
        assert isinstance(exc_load, SettingsError)
        assert isinstance(exc_load, MangaReaderError)

        exc_save = SettingsSaveError("Save error")
        assert isinstance(exc_save, SettingsError)


class TestImageConverterExceptions:
    """Test che image_converter usi FileSizeError."""

    def test_file_size_validation(self):
        """Test che file troppo grandi sollevano FileSizeError."""
        from src.utils.image_converter import convert_image_sync
        from src.constants import MAX_IMAGE_SIZE_MB

        # Crea file temporaneo troppo grande (mock)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            temp_path = f.name
            # Scrivi dati fittizi per simulare file grande
            # (Non scriviamo veramente 51MB per performance)
            f.write(b'x' * 1024)

        try:
            # Mocka getsize per simulare file grande
            import os
            original_getsize = os.path.getsize

            def mock_getsize(path):
                if path == temp_path:
                    return int((MAX_IMAGE_SIZE_MB + 1) * 1024 * 1024)
                return original_getsize(path)

            os.path.getsize = mock_getsize

            # Dovrebbe sollevare FileSizeError
            with pytest.raises(FileSizeError) as exc_info:
                convert_image_sync(temp_path)

            assert exc_info.value.actual_size_mb > MAX_IMAGE_SIZE_MB

        finally:
            os.path.getsize = original_getsize
            os.unlink(temp_path)


class TestCacheManagerExceptions:
    """Test che cache_manager usi CacheError."""

    def test_cache_key_invalid_file(self):
        """Test generazione cache key con file non esistente."""
        from src.cache_manager import CacheManager

        cache_mgr = CacheManager()

        # File che non esiste dovrebbe sollevare CacheError
        with pytest.raises(CacheError):
            cache_mgr.get_cache_key("/percorso/inesistente/file.manga", 150)


class TestDatabaseExceptions:
    """Test che database.py usi DatabaseError variants."""

    def test_invalid_database_path(self):
        """Test connessione a database invalido."""
        from src.database import MangaDatabaseManager

        # Path invalido in directory di sola lettura
        invalid_path = "/root/invalid.manga"

        # Su Linux, /root è solitamente non accessibile per utenti normali
        # Questo dovrebbe sollevare DatabaseConnectionError o DatabaseSchemaError
        with pytest.raises((DatabaseSchemaError, DatabaseConnectionError, PermissionError)):
            db = MangaDatabaseManager(invalid_path)

    def test_schema_creation(self):
        """Test creazione schema con path valido."""
        from src.database import MangaDatabaseManager

        # Usa file temporaneo
        with tempfile.NamedTemporaryFile(delete=False, suffix='.manga') as f:
            temp_db = f.name

        try:
            # Creazione dovrebbe andare a buon fine
            db = MangaDatabaseManager(temp_db)
            assert os.path.exists(temp_db)

            # Verifica che tabelle esistano
            import sqlite3
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                assert 'metadata' in tables
                assert 'chapters' in tables
                assert 'pages' in tables

        finally:
            if os.path.exists(temp_db):
                os.unlink(temp_db)


class TestSettingsExceptions:
    """Test che settings.py usi SettingsError variants."""

    def test_load_corrupted_settings(self):
        """Test caricamento settings corrotti."""
        from src.settings import Settings

        # Crea file settings corrotto
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            settings_path = f.name
            f.write("{invalid json content")

        try:
            # Sostituisci temporaneamente il path
            settings = Settings()
            original_path = settings.settings_file
            settings.settings_file = settings_path

            # Caricamento dovrebbe usare default invece di errore
            # (comportamento aggiornato: JSONDecodeError -> default)
            loaded = settings._load_settings()
            assert loaded is not None
            assert 'version' in loaded  # Dovrebbe avere i default

            settings.settings_file = original_path

        finally:
            os.unlink(settings_path)

    def test_save_to_readonly_directory(self):
        """Test salvataggio in directory sola lettura."""
        from src.settings import Settings

        # Crea directory temporanea
        temp_dir = tempfile.mkdtemp()

        try:
            settings = Settings()
            original_path = settings.settings_file

            # Imposta path in directory che diventerà read-only
            readonly_file = os.path.join(temp_dir, "readonly_settings.json")
            settings.settings_file = readonly_file

            # Rendi directory read-only
            os.chmod(temp_dir, 0o444)

            # Salvataggio dovrebbe sollevare SettingsSaveError
            with pytest.raises(SettingsSaveError):
                settings.save()

            settings.settings_file = original_path

        finally:
            # Ripristina permessi e pulisci
            os.chmod(temp_dir, 0o755)
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
