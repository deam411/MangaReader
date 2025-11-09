"""
Configurazione pytest per i test di Manga Reader.

Questo file contiene fixture comuni e configurazioni per tutti i test.
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Aggiungi la directory root del progetto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir():
    """
    Crea una directory temporanea per i test.

    Yields:
        Path: Percorso alla directory temporanea
    """
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    # Cleanup dopo il test
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_manga_file(temp_dir):
    """
    Crea un file .manga temporaneo per i test.

    Args:
        temp_dir: Fixture della directory temporanea

    Yields:
        Path: Percorso al file .manga temporaneo
    """
    manga_file = temp_dir / "test.manga"
    yield manga_file
    # Il cleanup è fatto dalla fixture temp_dir


@pytest.fixture
def sample_image_path(temp_dir):
    """
    Crea un'immagine di test.

    Args:
        temp_dir: Fixture della directory temporanea

    Yields:
        Path: Percorso all'immagine di test
    """
    from PIL import Image

    image_path = temp_dir / "test_image.png"
    # Crea un'immagine 100x100 rossa
    img = Image.new('RGB', (100, 100), color='red')
    img.save(str(image_path))

    yield image_path
    # Il cleanup è fatto dalla fixture temp_dir


def create_temp_image(temp_dir, name="temp_image.png"):
    """
    Helper function per creare un'immagine temporanea per i test.

    Questa funzione è utile quando serve creare immagini all'interno
    di fixture che già usano temp_dir.

    Args:
        temp_dir: Path alla directory temporanea
        name: Nome del file immagine

    Returns:
        Path: Percorso all'immagine creata
    """
    from PIL import Image

    image_path = temp_dir / name if isinstance(temp_dir, Path) else Path(temp_dir) / name
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(str(image_path))
    return image_path


@pytest.fixture
def mock_settings(temp_dir, monkeypatch):
    """
    Mock del sistema di settings per i test.

    Args:
        temp_dir: Fixture della directory temporanea
        monkeypatch: Fixture pytest per monkey patching

    Yields:
        Path: Percorso al file settings.json di test
    """
    settings_file = temp_dir / "settings.json"

    # Mock della funzione get_data_dir per usare temp_dir
    def mock_get_data_dir():
        return str(temp_dir)

    monkeypatch.setattr("src.paths.get_data_dir", mock_get_data_dir)

    yield settings_file


@pytest.fixture(scope="session")
def qapp():
    """
    Crea un'istanza di QApplication per i test Qt.

    Questa fixture ha scope 'session' per creare l'app una sola volta.

    Yields:
        QApplication: Istanza dell'applicazione Qt
    """
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    yield app

    # Nota: non chiamiamo app.quit() perché può causare problemi
    # con altri test che necessitano di QApplication


# Configurazione pytest
def pytest_configure(config):
    """Configurazione globale di pytest."""
    # Registra marker custom
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as UI test requiring QApplication"
    )
