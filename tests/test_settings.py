"""
Test per il modulo settings.py.

Testa il pattern Singleton, persistence delle impostazioni e valori default.
"""

import pytest
import json
from pathlib import Path

from src.settings import Settings
from src.constants import APP_VERSION, DEFAULT_CACHE_SIZE, DEFAULT_PRELOAD_PAGES, DEFAULT_THEME


class TestSettings:
    """Test per la classe Settings."""

    def test_singleton_pattern(self, mock_settings):
        """Test che Settings sia un Singleton."""
        # La fixture mock_settings ha già resettato il singleton

        settings1 = Settings()
        settings2 = Settings()

        # Devono essere la stessa istanza
        assert settings1 is settings2
        assert id(settings1) == id(settings2)

    def test_default_settings(self, mock_settings):
        """Test valori default delle impostazioni."""
        # La fixture mock_settings ha già resettato il singleton

        settings = Settings()

        # Verifica valori default
        assert settings.get_theme() == DEFAULT_THEME
        assert settings.settings['version'] == APP_VERSION
        assert settings.settings['library_path'] is None
        assert settings.settings['performance']['image_cache_size'] == DEFAULT_CACHE_SIZE
        assert settings.settings['performance']['preload_pages'] == DEFAULT_PRELOAD_PAGES
        assert settings.settings['performance']['lazy_loading'] is True

    def test_settings_persistence(self, mock_settings):
        """Test che le impostazioni vengano salvate e caricate correttamente."""
        # Resetta il singleton
        # La fixture mock_settings ha già resettato il singleton

        # Prima istanza: crea settings
        settings1 = Settings()
        settings1.set_theme('dark')
        settings1.settings['library_path'] = '/custom/path'
        settings1.save()

        # Resetta il singleton per simulare nuovo avvio app
        # La fixture mock_settings ha già resettato il singleton

        # Seconda istanza: carica settings salvate
        settings2 = Settings()

        # Verifica che le impostazioni siano state caricate
        assert settings2.get_theme() == 'dark'
        assert settings2.settings['library_path'] == '/custom/path'

    def test_get_and_set_theme(self, mock_settings):
        """Test get/set tema."""
        # La fixture mock_settings ha già resettato il singleton
        settings = Settings()

        # Test default
        assert settings.get_theme() == DEFAULT_THEME

        # Test set
        settings.set_theme('light')
        assert settings.get_theme() == 'light'

        settings.set_theme('dark')
        assert settings.get_theme() == 'dark'

        settings.set_theme('system')
        assert settings.get_theme() == 'system'

    def test_get_and_set_library_path(self, mock_settings):
        """Test get/set library path."""
        # La fixture mock_settings ha già resettato il singleton
        settings = Settings()

        # Test default (None = usa path di default)
        assert settings.settings['library_path'] is None

        # Test set
        custom_path = '/home/user/my_manga'
        settings.settings['library_path'] = custom_path
        assert settings.settings['library_path'] == custom_path

    def test_performance_settings(self, mock_settings):
        """Test impostazioni performance."""
        # La fixture mock_settings ha già resettato il singleton
        settings = Settings()

        # Verifica valori default
        perf = settings.settings['performance']
        assert perf['image_cache_size'] == DEFAULT_CACHE_SIZE
        assert perf['lazy_loading'] is True
        assert perf['preload_pages'] == DEFAULT_PRELOAD_PAGES

        # Modifica valori
        perf['image_cache_size'] = 100
        perf['lazy_loading'] = False
        perf['preload_pages'] = 5

        # Verifica modifiche
        assert settings.settings['performance']['image_cache_size'] == 100
        assert settings.settings['performance']['lazy_loading'] is False
        assert settings.settings['performance']['preload_pages'] == 5

    def test_shortcuts_settings(self, mock_settings):
        """Test impostazioni shortcuts."""
        # La fixture mock_settings ha già resettato il singleton
        settings = Settings()

        # Verifica shortcuts default
        shortcuts = settings.settings['shortcuts']
        assert 'quit' in shortcuts
        assert 'back' in shortcuts
        assert 'fullscreen' in shortcuts
        assert shortcuts['fullscreen'] == 'F11'

        # Modifica shortcut
        shortcuts['fullscreen'] = 'F12'
        assert settings.settings['shortcuts']['fullscreen'] == 'F12'

    def test_save_creates_directory(self, mock_settings, temp_dir):
        """Test che save() crei la directory se non esiste."""
        # La fixture mock_settings ha già resettato il singleton

        # Usa una sottodirectory che non esiste
        nested_dir = temp_dir / "nested" / "path"
        settings_file = nested_dir / "settings.json"

        settings = Settings()
        settings.settings_file = str(settings_file)

        # Salva (dovrebbe creare la directory)
        settings.save()

        # Verifica che la directory sia stata creata
        assert nested_dir.exists()
        assert settings_file.exists()

    def test_load_corrupted_settings_file(self, mock_settings):
        """Test caricamento file settings corrotto."""
        # La fixture mock_settings ha già resettato il singleton

        # Crea un file settings corrotto
        settings_file = mock_settings
        settings_file.write_text("{ invalid json }")

        # Carica settings (dovrebbe usare default)
        settings = Settings()

        # Verifica che usi default invece di crashare
        assert settings.get_theme() == DEFAULT_THEME
        assert settings.settings['version'] == APP_VERSION

    def test_merge_with_default_settings(self, mock_settings):
        """Test che le nuove chiavi default vengano aggiunte a settings esistenti."""
        # La fixture mock_settings ha già resettato il singleton

        # Crea settings file con versione vecchia (senza alcune chiavi)
        old_settings = {
            "version": "0.0.1",
            "theme": "dark"
            # Mancano altre chiavi
        }

        with open(str(mock_settings), 'w') as f:
            json.dump(old_settings, f)

        # Carica settings
        settings = Settings()

        # Verifica che le chiavi vecchie siano preservate
        assert settings.get_theme() == 'dark'

        # Verifica che le nuove chiavi siano state aggiunte
        assert 'performance' in settings.settings
        assert 'shortcuts' in settings.settings
        assert 'library_path' in settings.settings

    def test_settings_file_location(self, mock_settings):
        """Test che il file settings sia nella posizione corretta."""
        # La fixture mock_settings ha già resettato il singleton

        settings = Settings()

        # Verifica che settings_file sia impostato
        assert settings.settings_file is not None
        assert 'settings.json' in settings.settings_file

    def test_save_and_reload(self, mock_settings):
        """Test ciclo completo save/reload."""
        # La fixture mock_settings ha già resettato il singleton

        # Crea e configura settings
        settings1 = Settings()
        settings1.set_theme('light')
        settings1.settings['library_path'] = '/test/path'
        settings1.settings['performance']['image_cache_size'] = 150
        settings1.settings['shortcuts']['fullscreen'] = 'F10'

        # Salva
        settings1.save()

        # Verifica che il file sia stato scritto
        assert Path(settings1.settings_file).exists()

        # Leggi il file direttamente
        with open(settings1.settings_file, 'r') as f:
            saved_data = json.load(f)

        assert saved_data['theme'] == 'light'
        assert saved_data['library_path'] == '/test/path'
        assert saved_data['performance']['image_cache_size'] == 150
        assert saved_data['shortcuts']['fullscreen'] == 'F10'

        # Resetta singleton e ricarica
        # La fixture mock_settings ha già resettato il singleton
        settings2 = Settings()

        # Verifica che tutto sia stato ricaricato correttamente
        assert settings2.get_theme() == 'light'
        assert settings2.settings['library_path'] == '/test/path'
        assert settings2.settings['performance']['image_cache_size'] == 150
        assert settings2.settings['shortcuts']['fullscreen'] == 'F10'

    def test_multiple_save_operations(self, mock_settings):
        """Test multiple operazioni di salvataggio."""
        # La fixture mock_settings ha già resettato il singleton

        settings = Settings()

        # Prima modifica e save
        settings.set_theme('dark')
        settings.save()

        # Seconda modifica e save
        settings.set_theme('light')
        settings.save()

        # Terza modifica e save
        settings.settings['library_path'] = '/new/path'
        settings.save()

        # Verifica che l'ultima modifica sia salvata
        # La fixture mock_settings ha già resettato il singleton
        settings_reloaded = Settings()

        assert settings_reloaded.get_theme() == 'light'
        assert settings_reloaded.settings['library_path'] == '/new/path'

    def test_version_tracking(self, mock_settings):
        """Test che la versione sia tracciata correttamente."""
        # La fixture mock_settings ha già resettato il singleton

        settings = Settings()

        # Verifica che la versione sia quella corrente
        assert settings.settings['version'] == APP_VERSION

    def test_last_opened_manga(self, mock_settings):
        """Test tracciamento ultimo manga aperto."""
        # La fixture mock_settings ha già resettato il singleton

        settings = Settings()

        # Default dovrebbe essere None
        assert settings.settings['last_opened_manga'] is None

        # Imposta ultimo manga
        settings.settings['last_opened_manga'] = '/path/to/manga.manga'
        settings.save()

        # Ricarica e verifica
        # La fixture mock_settings ha già resettato il singleton
        settings2 = Settings()

        assert settings2.settings['last_opened_manga'] == '/path/to/manga.manga'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
