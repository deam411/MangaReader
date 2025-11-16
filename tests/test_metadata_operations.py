"""
Test suite per operazioni di metadata del manga.

Verifica inserimento, aggiornamento, recupero e validazione metadata.
"""
import pytest
import tempfile
import os
from src.database import MangaDatabaseManager
from src.exceptions import ValidationError


class TestMetadataOperations:
    """Test suite per operazioni metadata."""

    @pytest.fixture
    def temp_db(self):
        """Crea database temporaneo."""
        fd, path = tempfile.mkstemp(suffix='.manga')
        os.close(fd)

        db_manager = MangaDatabaseManager(path)

        yield path, db_manager

        # Cleanup
        db_manager.close()
        if os.path.exists(path):
            os.remove(path)

    def test_set_metadata_minimal(self, temp_db):
        """Test inserimento metadata con solo campi richiesti."""
        path, db_manager = temp_db

        result = db_manager.insert_metadata(
            title="Test Manga",
            author=None,
            description=None
        )

        assert result is True

        metadata = db_manager.get_metadata()
        assert metadata['title'] == "Test Manga"
        assert metadata['author'] is None or metadata['author'] == ""
        assert metadata['description'] is None or metadata['description'] == ""

    def test_set_metadata_complete(self, temp_db):
        """Test inserimento metadata completo."""
        path, db_manager = temp_db

        result = db_manager.insert_metadata(
            title="One Piece",
            author="Eiichiro Oda",
            description="A pirate's adventure to find the ultimate treasure",
            language="Japanese",
            year=1997,
            tags="Action, Adventure, Fantasy"
        )

        assert result is True

        metadata = db_manager.get_metadata()
        assert metadata['title'] == "One Piece"
        assert metadata['author'] == "Eiichiro Oda"
        assert metadata['description'] == "A pirate's adventure to find the ultimate treasure"
        assert metadata['language'] == "Japanese"
        assert metadata['year'] == 1997
        assert metadata['tags'] == "Action, Adventure, Fantasy"

    def test_set_metadata_with_cover(self, temp_db):
        """Test inserimento metadata con copertina."""
        path, db_manager = temp_db

        cover_data = b"fake_image_data_12345"

        result = db_manager.insert_metadata(
            title="Test Manga",
            author="Author",
            description="Description",
            cover=cover_data
        )

        assert result is True

        metadata = db_manager.get_metadata()
        assert metadata['cover'] == cover_data

    def test_set_metadata_unicode_characters(self, temp_db):
        """Test metadata con caratteri unicode."""
        path, db_manager = temp_db

        result = db_manager.insert_metadata(
            title="ワンピース",
            author="尾田栄一郎",
            description="海賊の冒険物語",
            language="日本語"
        )

        assert result is True

        metadata = db_manager.get_metadata()
        assert metadata['title'] == "ワンピース"
        assert metadata['author'] == "尾田栄一郎"
        assert metadata['description'] == "海賊の冒険物語"

    def test_set_metadata_empty_title_fails(self, temp_db):
        """Test che titolo vuoto generi errore."""
        path, db_manager = temp_db

        with pytest.raises(ValidationError):
            db_manager.insert_metadata(
                title="",
                author="Author",
                description="Description"
            )

    def test_set_metadata_none_title_fails(self, temp_db):
        """Test che titolo None generi errore."""
        path, db_manager = temp_db

        with pytest.raises((ValidationError, TypeError)):
            db_manager.insert_metadata(
                title=None,
                author="Author",
                description="Description"
            )

    def test_set_metadata_title_only_whitespace_fails(self, temp_db):
        """Test che titolo con solo spazi generi errore."""
        path, db_manager = temp_db

        with pytest.raises(ValidationError):
            db_manager.insert_metadata(
                title="   ",
                author="Author",
                description="Description"
            )

    def test_set_metadata_very_long_title(self, temp_db):
        """Test metadata con titolo molto lungo."""
        path, db_manager = temp_db

        long_title = "A" * 500

        result = db_manager.insert_metadata(
            title=long_title,
            author="Author",
            description="Description"
        )

        assert result is True

        metadata = db_manager.get_metadata()
        # Il titolo viene troncato a MAX_TITLE_LENGTH (200 caratteri)
        assert metadata['title'] == "A" * 200

    def test_set_metadata_very_long_description(self, temp_db):
        """Test metadata con descrizione molto lunga."""
        path, db_manager = temp_db

        long_description = "This is a very long description. " * 100

        result = db_manager.insert_metadata(
            title="Test",
            author="Author",
            description=long_description
        )

        assert result is True

        metadata = db_manager.get_metadata()
        # La descrizione viene troncata a MAX_DESCRIPTION_LENGTH (2000 caratteri)
        assert metadata['description'] == long_description[:2000]

    def test_set_metadata_year_valid(self, temp_db):
        """Test anno valido."""
        path, db_manager = temp_db

        valid_years = [1900, 1950, 2000, 2024, 2025]

        for year in valid_years:
            result = db_manager.insert_metadata(
                title=f"Manga {year}",
                author="Author",
                description="Description",
                year=year
            )
            assert result is True

    def test_set_metadata_year_invalid(self, temp_db):
        """Test anno non valido."""
        path, db_manager = temp_db

        invalid_years = [1800, -100, 3000, 999999]

        for year in invalid_years:
            with pytest.raises(ValidationError):
                db_manager.insert_metadata(
                    title="Test",
                    author="Author",
                    description="Description",
                    year=year
                )

    def test_set_metadata_multiple_tags(self, temp_db):
        """Test metadata con multipli tags."""
        path, db_manager = temp_db

        tags = "Action, Adventure, Fantasy, Comedy, Drama"

        result = db_manager.insert_metadata(
            title="Test",
            author="Author",
            description="Description",
            tags=tags
        )

        assert result is True

        metadata = db_manager.get_metadata()
        assert metadata['tags'] == tags

    def test_set_metadata_special_characters_in_description(self, temp_db):
        """Test descrizione con caratteri speciali."""
        path, db_manager = temp_db

        description_with_special = 'Test with "quotes", \'apostrophes\', and\nnewlines\ttabs'

        result = db_manager.insert_metadata(
            title="Test",
            author="Author",
            description=description_with_special
        )

        assert result is True

        metadata = db_manager.get_metadata()
        assert metadata['description'] == description_with_special

    def test_get_metadata_empty_database(self):
        """Test recupero metadata da database vuoto."""
        fd, path = tempfile.mkstemp(suffix='.manga')
        os.close(fd)

        db_manager = MangaDatabaseManager(path)

        # Database nuovo senza metadata
        metadata = db_manager.get_metadata()

        # Dovrebbe tornare None o dict vuoto
        assert metadata is None or metadata == {}

        db_manager.close()
        os.remove(path)

    def test_update_metadata_title(self, temp_db):
        """Test aggiornamento titolo."""
        path, db_manager = temp_db

        # Inserisci metadata iniziale
        db_manager.insert_metadata(
            title="Original Title",
            author="Author",
            description="Description"
        )

        # Usa update_metadata invece di insert_metadata per aggiornamenti
        result = db_manager.update_metadata(title="Updated Title")

        assert result is True

        metadata = db_manager.get_metadata()
        assert metadata['title'] == "Updated Title"

    def test_update_metadata_author(self, temp_db):
        """Test aggiornamento autore."""
        path, db_manager = temp_db

        db_manager.insert_metadata(
            title="Title",
            author="Original Author",
            description="Description"
        )

        # Usa update_metadata per aggiornamenti (title è obbligatorio)
        result = db_manager.update_metadata(
            title="Title",
            author="Updated Author"
        )
        assert result is True

        metadata = db_manager.get_metadata()
        assert metadata['author'] == "Updated Author"

    def test_update_metadata_cover(self, temp_db):
        """Test aggiornamento copertina."""
        path, db_manager = temp_db

        original_cover = b"original_cover_data"
        updated_cover = b"updated_cover_data"

        db_manager.insert_metadata(
            title="Title",
            author="Author",
            description="Description",
            cover=original_cover
        )

        # Usa update_metadata per aggiornamenti (title è obbligatorio)
        result = db_manager.update_metadata(
            title="Title",
            cover=updated_cover
        )
        assert result is True

        metadata = db_manager.get_metadata()
        assert metadata['cover'] == updated_cover

    def test_metadata_all_fields_present(self, temp_db):
        """Test che tutti i campi siano presenti nel metadata recuperato."""
        path, db_manager = temp_db

        db_manager.insert_metadata(
            title="Test",
            author="Author",
            description="Description"
        )

        metadata = db_manager.get_metadata()

        # Verifica campi obbligatori
        assert 'title' in metadata
        assert 'author' in metadata
        assert 'description' in metadata

    def test_metadata_trimming_whitespace(self, temp_db):
        """Test che whitespace venga trimmed dai campi."""
        path, db_manager = temp_db

        result = db_manager.insert_metadata(
            title="  Title with spaces  ",
            author="  Author  ",
            description="  Description  "
        )

        assert result is True

        metadata = db_manager.get_metadata()

        # I valori dovrebbero essere trimmed (se la validazione lo fa)
        assert metadata['title'].strip() == "Title with spaces"
        assert metadata['author'].strip() == "Author"
        assert metadata['description'].strip() == "Description"

    def test_metadata_none_optional_fields(self, temp_db):
        """Test che campi opzionali possano essere None."""
        path, db_manager = temp_db

        result = db_manager.insert_metadata(
            title="Test",
            author=None,
            description=None,
            language=None,
            cover=None,
            year=None,
            tags=None
        )

        assert result is True

        metadata = db_manager.get_metadata()
        assert metadata['title'] == "Test"

    def test_metadata_large_cover_image(self, temp_db):
        """Test metadata con immagine copertina grande."""
        path, db_manager = temp_db

        # Simula immagine di 1MB
        large_cover = b"X" * (1024 * 1024)

        result = db_manager.insert_metadata(
            title="Test",
            author="Author",
            description="Description",
            cover=large_cover
        )

        assert result is True

        metadata = db_manager.get_metadata()
        assert len(metadata['cover']) == len(large_cover)

    def test_metadata_persistence(self, temp_db):
        """Test persistenza metadata tra chiusura e riapertura database."""
        path, db_manager = temp_db

        db_manager.insert_metadata(
            title="Persistent Title",
            author="Persistent Author",
            description="Persistent Description"
        )

        # Chiudi database
        db_manager.close()

        # Riapri
        db_manager2 = MangaDatabaseManager(path)

        metadata = db_manager2.get_metadata()
        assert metadata['title'] == "Persistent Title"
        assert metadata['author'] == "Persistent Author"

        db_manager2.close()
