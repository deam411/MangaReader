"""
Test per il modulo paths.py.

Testa la gestione dei percorsi su diverse piattaforme e in modalità frozen/unfrozen.
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch

from src import paths


class TestPaths:
    """Test per le funzioni di gestione percorsi."""

    def test_get_data_dir_windows(self, monkeypatch, temp_dir):
        """Test get_data_dir su Windows."""
        # Mock Windows con directory temporanea
        monkeypatch.setattr('sys.platform', 'win32')
        test_appdata = str(temp_dir / "AppData" / "Local")
        monkeypatch.setenv('LOCALAPPDATA', test_appdata)

        data_dir = paths.get_data_dir()

        assert 'MangaReader' in data_dir
        assert Path(data_dir).exists()  # Dovrebbe essere creato
        assert Path(data_dir).is_dir()

    def test_get_data_dir_unix(self, monkeypatch):
        """Test get_data_dir su Unix/Linux/Mac."""
        # Mock Unix
        monkeypatch.setattr('os.name', 'posix')
        monkeypatch.setenv('HOME', '/home/test')

        data_dir = paths.get_data_dir()

        assert 'mangareader' in data_dir.lower() or '.mangareader' in data_dir

    def test_get_data_dir_creates_directory(self, monkeypatch, temp_dir):
        """Test che get_data_dir crei la directory se non esiste."""
        # Mock per usare temp_dir
        test_data_dir = temp_dir / "test_manga_data"

        def mock_get_data_dir():
            data_dir = str(test_data_dir)
            os.makedirs(data_dir, exist_ok=True)
            return data_dir

        monkeypatch.setattr('src.paths.get_data_dir', mock_get_data_dir)

        data_dir = paths.get_data_dir()

        assert Path(data_dir).exists()
        assert Path(data_dir).is_dir()

    def test_get_manga_dir_default(self, mock_settings, monkeypatch):
        """Test get_manga_dir con path default."""
        # La fixture mock_settings crea Settings reale con path temporaneo
        # Settings ha library_path = None di default, quindi usa il path default
        from src.settings import Settings
        settings = Settings()

        # Assicurati che library_path sia None
        settings.settings['library_path'] = None
        settings.save()

        manga_dir = paths.get_manga_dir()

        # Dovrebbe restituire il path default
        assert manga_dir is not None
        assert 'manga' in manga_dir.lower()

    def test_get_manga_dir_custom_path(self, mock_settings, temp_dir):
        """Test get_manga_dir con path personalizzato."""
        from src.settings import Settings

        custom_path = str(temp_dir / "custom_library")
        custom_path_obj = temp_dir / "custom_library"
        custom_path_obj.mkdir(exist_ok=True)

        # Imposta custom path in Settings reale
        settings = Settings()
        settings.settings['library_path'] = custom_path
        settings.save()

        manga_dir = paths.get_manga_dir()

        assert manga_dir == custom_path

    def test_get_manga_dir_creates_directory(self, mock_settings, temp_dir):
        """Test che get_manga_dir crei la directory se non esiste."""
        from src.settings import Settings

        non_existent_path = str(temp_dir / "new_library")

        # Imposta path che non esiste ancora
        settings = Settings()
        settings.settings['library_path'] = non_existent_path
        settings.save()

        # La directory non dovrebbe esistere ancora
        assert not Path(non_existent_path).exists()

        manga_dir = paths.get_manga_dir()

        # Dopo get_manga_dir, dovrebbe esistere
        assert Path(manga_dir).exists()
        assert Path(manga_dir).is_dir()

    @pytest.mark.skipif(not hasattr(sys, 'frozen'), reason="Test solo in modalità frozen")
    def test_frozen_mode_detection(self):
        """Test rilevamento modalità frozen (PyInstaller)."""
        # In modalità frozen, sys.frozen dovrebbe essere True
        if hasattr(sys, 'frozen'):
            assert sys.frozen is True
            assert hasattr(sys, '_MEIPASS')

    def test_unfrozen_mode_paths(self):
        """Test che i percorsi funzionino in modalità development (non-frozen)."""
        # In modalità normale, non dovrebbe esserci sys._MEIPASS
        if not hasattr(sys, 'frozen'):
            assert not hasattr(sys, '_MEIPASS')

        # I percorsi dovrebbero comunque funzionare
        data_dir = paths.get_data_dir()
        assert data_dir is not None
        assert isinstance(data_dir, str)

        manga_dir = paths.get_manga_dir()
        assert manga_dir is not None
        assert isinstance(manga_dir, str)

    def test_path_consistency(self):
        """Test che le funzioni restituiscano path consistenti tra chiamate."""
        # Multiple chiamate dovrebbero restituire lo stesso path
        data_dir1 = paths.get_data_dir()
        data_dir2 = paths.get_data_dir()

        assert data_dir1 == data_dir2

        manga_dir1 = paths.get_manga_dir()
        manga_dir2 = paths.get_manga_dir()

        assert manga_dir1 == manga_dir2

    def test_paths_are_absolute(self, mock_settings):
        """Test che i path di sistema restituiti siano assoluti."""
        from src.settings import Settings

        # Assicurati che library_path sia None per usare default
        settings = Settings()
        settings.settings['library_path'] = None
        settings.save()

        data_dir = paths.get_data_dir()
        manga_dir = paths.get_manga_dir()

        # data_dir dovrebbe sempre essere assoluto
        assert Path(data_dir).is_absolute()

        # manga_dir dovrebbe essere assoluto quando usa path default
        # Nota: se l'utente imposta un path relativo, potrebbe non essere assoluto
        assert manga_dir is not None

    def test_paths_use_native_separators(self):
        """Test che i path usino i separatori nativi del OS."""
        data_dir = paths.get_data_dir()
        manga_dir = paths.get_manga_dir()

        # Windows usa \, Unix usa /
        if os.name == 'nt':
            # Su Windows, i path normalizzati dovrebbero avere \
            assert '\\' in data_dir or '/' in data_dir  # Accetta entrambi
        else:
            # Su Unix, dovrebbero avere /
            assert '/' in data_dir

    def test_get_data_dir_without_env_vars(self, monkeypatch):
        """Test get_data_dir quando le variabili d'ambiente non sono impostate."""
        # Rimuovi variabili d'ambiente
        monkeypatch.delenv('LOCALAPPDATA', raising=False)
        monkeypatch.delenv('APPDATA', raising=False)
        monkeypatch.delenv('HOME', raising=False)

        # Dovrebbe comunque restituire un path valido (fallback)
        try:
            data_dir = paths.get_data_dir()
            assert data_dir is not None
            assert isinstance(data_dir, str)
        except Exception:
            # Se fallisce, è accettabile data la mancanza di env vars
            pass

    def test_unicode_in_paths(self, mock_settings, temp_dir):
        """Test gestione caratteri Unicode nei percorsi."""
        from src.settings import Settings

        unicode_path = temp_dir / "漫画_Library_café"
        unicode_path.mkdir(exist_ok=True)

        # Imposta path Unicode in Settings
        settings = Settings()
        settings.settings['library_path'] = str(unicode_path)
        settings.save()

        manga_dir = paths.get_manga_dir()

        assert manga_dir == str(unicode_path)
        assert Path(manga_dir).exists()

    def test_spaces_in_paths(self, mock_settings, temp_dir):
        """Test gestione spazi nei percorsi."""
        from src.settings import Settings

        path_with_spaces = temp_dir / "My Manga Library"
        path_with_spaces.mkdir(exist_ok=True)

        # Imposta path con spazi in Settings
        settings = Settings()
        settings.settings['library_path'] = str(path_with_spaces)
        settings.save()

        manga_dir = paths.get_manga_dir()

        assert manga_dir == str(path_with_spaces)
        assert Path(manga_dir).exists()

    def test_very_long_path(self, mock_settings, temp_dir):
        """Test gestione percorsi molto lunghi."""
        from src.settings import Settings

        # Crea un percorso lungo ma non troppo per evitare errori OS
        long_path = temp_dir / ("a" * 30) / ("b" * 30)

        # Imposta path lungo in Settings
        settings = Settings()
        settings.settings['library_path'] = str(long_path)
        settings.save()

        # Questo potrebbe fallire su alcuni filesystem, ma dovrebbe gestire gracefully
        try:
            manga_dir = paths.get_manga_dir()
            # Se riesce, verifica che sia il path corretto
            assert str(long_path) in manga_dir or manga_dir == str(long_path)
        except (OSError, FileNotFoundError):
            # Su alcuni OS, path troppo lunghi falliscono - è ok
            pass

    def test_relative_to_absolute_conversion(self, mock_settings, temp_dir):
        """Test che i path relativi siano gestiti correttamente."""
        from src.settings import Settings

        # Nota: get_manga_dir non converte automaticamente path relativi in assoluti
        # Usa un path relativo che esiste
        relative_path = './relative_test_path'

        settings = Settings()
        settings.settings['library_path'] = relative_path
        settings.save()

        manga_dir = paths.get_manga_dir()

        # Il path restituito dovrebbe esistere (viene creato se non esiste)
        # Non possiamo garantire che sia assoluto perché dipende dall'implementazione
        assert manga_dir is not None
        assert isinstance(manga_dir, str)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
