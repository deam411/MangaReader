"""
Test per il modulo importers (CBZ/CBR).
Verifica import archivi, estrazione immagini e conversione in formato .manga.
"""
import pytest
import os
import zipfile
import tempfile
from pathlib import Path
from PIL import Image
import io

from src.importers import ArchiveImporter


class TestArchiveDetection:
    """Test per detect_archive_type()."""

    def test_detect_cbz_by_extension(self, temp_dir):
        """Verifica rilevamento CBZ da estensione."""
        cbz_file = os.path.join(temp_dir, "test.cbz")
        Path(cbz_file).touch()

        archive_type = ArchiveImporter.detect_archive_type(cbz_file)
        assert archive_type == 'cbz'

    def test_detect_zip_extension(self, temp_dir):
        """Verifica rilevamento ZIP."""
        zip_file = os.path.join(temp_dir, "test.zip")
        Path(zip_file).touch()

        archive_type = ArchiveImporter.detect_archive_type(zip_file)
        assert archive_type == 'cbz'

    def test_detect_cbz_by_magic_number(self, temp_dir):
        """Verifica rilevamento CBZ da magic number."""
        # File senza estensione ma con magic number ZIP
        file_path = os.path.join(temp_dir, "test_no_ext")

        # Crea un ZIP valido
        with zipfile.ZipFile(file_path, 'w') as zf:
            zf.writestr("dummy.txt", "test")

        archive_type = ArchiveImporter.detect_archive_type(file_path)
        assert archive_type == 'cbz'

    def test_detect_invalid_file(self, temp_dir):
        """Verifica comportamento con file non valido."""
        invalid_file = os.path.join(temp_dir, "test.txt")
        with open(invalid_file, 'w') as f:
            f.write("Not an archive")

        archive_type = ArchiveImporter.detect_archive_type(invalid_file)
        assert archive_type is None


class TestImageFileDetection:
    """Test per is_image_file()."""

    def test_is_image_png(self):
        """Verifica riconoscimento PNG."""
        assert ArchiveImporter.is_image_file("test.png") is True

    def test_is_image_jpg(self):
        """Verifica riconoscimento JPG/JPEG."""
        assert ArchiveImporter.is_image_file("test.jpg") is True
        assert ArchiveImporter.is_image_file("test.jpeg") is True

    def test_is_image_webp(self):
        """Verifica riconoscimento WebP."""
        assert ArchiveImporter.is_image_file("test.webp") is True

    def test_is_not_image(self):
        """Verifica che non-immagini vengano escluse."""
        assert ArchiveImporter.is_image_file("test.txt") is False
        assert ArchiveImporter.is_image_file("test.pdf") is False
        assert ArchiveImporter.is_image_file("test.exe") is False

    def test_is_image_case_insensitive(self):
        """Verifica case-insensitivity."""
        assert ArchiveImporter.is_image_file("test.PNG") is True
        assert ArchiveImporter.is_image_file("test.JPG") is True


class TestZipExtraction:
    """Test per extract_images_from_zip()."""

    def create_test_zip(self, zip_path, num_images=3):
        """Helper per creare un ZIP di test con immagini."""
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for i in range(num_images):
                # Crea immagine semplice in memoria
                img = Image.new('RGB', (100, 100), color=(i*50, i*50, i*50))
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)

                # Aggiungi al ZIP
                zf.writestr(f"page{i:03d}.png", img_bytes.getvalue())

    def test_extract_from_valid_zip(self, temp_dir):
        """Verifica estrazione da ZIP valido."""
        zip_path = os.path.join(temp_dir, "test.cbz")
        self.create_test_zip(zip_path, num_images=3)

        importer = ArchiveImporter()
        images = importer.extract_images_from_zip(zip_path)

        assert len(images) == 3
        assert all(isinstance(img, tuple) and len(img) == 2 for img in images)
        assert all(isinstance(name, str) and isinstance(data, bytes) for name, data in images)

    def test_extract_images_sorted(self, temp_dir):
        """Verifica che le immagini siano estratte ordinate."""
        zip_path = os.path.join(temp_dir, "test.cbz")
        self.create_test_zip(zip_path, num_images=5)

        importer = ArchiveImporter()
        images = importer.extract_images_from_zip(zip_path)

        # Verifica ordinamento
        filenames = [name for name, _ in images]
        assert filenames == sorted(filenames)

    def test_extract_skip_directories(self, temp_dir):
        """Verifica che le directory vengano saltate."""
        zip_path = os.path.join(temp_dir, "test.cbz")

        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Aggiungi directory
            zf.writestr("folder/", "")

            # Aggiungi immagine
            img = Image.new('RGB', (100, 100))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            zf.writestr("image.png", img_bytes.getvalue())

        importer = ArchiveImporter()
        images = importer.extract_images_from_zip(zip_path)

        # Solo l'immagine, non la directory
        assert len(images) == 1

    def test_extract_skip_hidden_files(self, temp_dir):
        """Verifica che i file nascosti vengano saltati."""
        zip_path = os.path.join(temp_dir, "test.cbz")

        with zipfile.ZipFile(zip_path, 'w') as zf:
            # File nascosto (inizia con .)
            zf.writestr(".hidden.txt", "hidden")

            # Immagine normale
            img = Image.new('RGB', (100, 100))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            zf.writestr("image.png", img_bytes.getvalue())

        importer = ArchiveImporter()
        images = importer.extract_images_from_zip(zip_path)

        # Solo l'immagine, non il file nascosto
        assert len(images) == 1
        assert images[0][0] == "image.png"

    def test_extract_from_corrupted_zip(self, temp_dir):
        """Verifica gestione ZIP corrotto."""
        zip_path = os.path.join(temp_dir, "corrupted.cbz")

        # Crea file che sembra ZIP ma è corrotto
        with open(zip_path, 'wb') as f:
            f.write(b'PK\x03\x04' + b'corrupted data')

        importer = ArchiveImporter()
        images = importer.extract_images_from_zip(zip_path)

        # Dovrebbe restituire lista vuota senza crashare
        assert images == []

    def test_extract_mixed_content(self, temp_dir):
        """Verifica estrazione con contenuto misto."""
        zip_path = os.path.join(temp_dir, "mixed.cbz")

        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Aggiungi vari tipi di file
            zf.writestr("readme.txt", "Some text")

            # Immagini
            for i in range(2):
                img = Image.new('RGB', (100, 100))
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                zf.writestr(f"page{i}.png", img_bytes.getvalue())

            # Non-immagine
            zf.writestr("data.json", "{}")

        importer = ArchiveImporter()
        images = importer.extract_images_from_zip(zip_path)

        # Solo le 2 immagini
        assert len(images) == 2


class TestArchiveImport:
    """Test per import_archive()."""

    def create_test_cbz(self, cbz_path, num_pages=5):
        """Helper per creare un CBZ di test."""
        with zipfile.ZipFile(cbz_path, 'w') as zf:
            for i in range(num_pages):
                img = Image.new('RGB', (800, 1200), color=(i*20, 100, 150))
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                zf.writestr(f"page{i:03d}.png", img_bytes.getvalue())

    def test_import_cbz_success(self, temp_dir):
        """Verifica import completo di un CBZ."""
        cbz_path = os.path.join(temp_dir, "test.cbz")
        output_path = os.path.join(temp_dir, "output.manga")

        self.create_test_cbz(cbz_path, num_pages=5)

        importer = ArchiveImporter()
        success, error_msg = importer.import_archive(
            archive_path=cbz_path,
            output_path=output_path,
            title="Test Manga",
            author="Test Author",
            volume_name="Volume 1",
            chapter_name="Chapter 1"
        )

        assert success is True
        assert error_msg == ""
        assert os.path.exists(output_path)

        # Verifica che il database contenga i dati
        from src.database import MangaDatabaseManager
        db = MangaDatabaseManager(output_path)

        metadata = db.get_metadata()
        assert metadata is not None
        assert metadata['title'] == "Test Manga"
        assert metadata['author'] == "Test Author"

        volumes = db.get_volumes()
        assert len(volumes) > 0

        chapters = db.get_chapters_for_volume(volumes[0]['id'])
        assert len(chapters) > 0

        pages = db.get_pages_for_chapter(chapters[0]['id'])
        assert len(pages) == 5

    def test_import_with_defaults(self, temp_dir):
        """Verifica import con metadata di default."""
        cbz_path = os.path.join(temp_dir, "manga.cbz")
        output_path = os.path.join(temp_dir, "output.manga")

        self.create_test_cbz(cbz_path, num_pages=3)

        importer = ArchiveImporter()
        success, error_msg = importer.import_archive(
            archive_path=cbz_path,
            output_path=output_path
            # Usa tutti i default
        )

        assert success is True
        assert error_msg == ""
        assert os.path.exists(output_path)

    def test_import_nonexistent_file(self, temp_dir):
        """Verifica gestione file inesistente."""
        cbz_path = os.path.join(temp_dir, "nonexistent.cbz")
        output_path = os.path.join(temp_dir, "output.manga")

        importer = ArchiveImporter()
        success, error_msg = importer.import_archive(
            archive_path=cbz_path,
            output_path=output_path
        )

        assert success is False
        assert error_msg != ""  # Deve contenere un messaggio di errore


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
