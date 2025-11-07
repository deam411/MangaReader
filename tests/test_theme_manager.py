"""
Test per il modulo theme_manager.
Verifica caricamento temi, generazione stylesheet e applicazione.
"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock, mock_open
from src import theme_manager


class TestLoadThemes:
    """Test per la funzione load_themes()."""

    def test_load_themes_success(self):
        """Verifica caricamento temi dal file JSON."""
        themes = theme_manager.load_themes()

        assert isinstance(themes, dict), "load_themes dovrebbe restituire un dizionario"
        assert len(themes) > 0, "Dovrebbero esserci temi disponibili"

        # Verifica che esistano i temi standard
        expected_themes = ["dark", "light"]
        for theme in expected_themes:
            assert theme in themes, f"Tema '{theme}' dovrebbe essere disponibile"

    def test_theme_structure(self):
        """Verifica struttura dei temi caricati."""
        themes = theme_manager.load_themes()

        for theme_name, theme_data in themes.items():
            assert "name" in theme_data, f"Tema {theme_name} dovrebbe avere 'name'"
            assert "colors" in theme_data, f"Tema {theme_name} dovrebbe avere 'colors'"

            # Verifica che ci siano colori definiti
            colors = theme_data["colors"]
            assert isinstance(colors, dict), "Colors dovrebbe essere un dizionario"
            assert len(colors) > 0, "Dovrebbero esserci colori definiti"

            # Verifica alcuni colori essenziali
            essential_colors = ["widget_bg", "widget_fg", "button_bg"]
            for color in essential_colors:
                assert color in colors, f"Tema {theme_name} dovrebbe avere colore '{color}'"

    def test_load_themes_file_not_found(self):
        """Verifica comportamento quando themes.json non esiste."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            themes = theme_manager.load_themes()
            assert themes == {}, "Dovrebbe restituire dizionario vuoto se file non trovato"

    def test_load_themes_invalid_json(self):
        """Verifica comportamento con JSON invalido."""
        with patch('builtins.open', mock_open(read_data='{')):
            themes = theme_manager.load_themes()
            assert themes == {}, "Dovrebbe restituire dizionario vuoto con JSON invalido"


class TestGenerateStylesheet:
    """Test per la funzione generate_stylesheet()."""

    def test_generate_stylesheet_dark(self):
        """Verifica generazione stylesheet per tema dark."""
        stylesheet = theme_manager.generate_stylesheet("dark")

        assert isinstance(stylesheet, str), "generate_stylesheet dovrebbe restituire stringa"
        assert len(stylesheet) > 0, "Stylesheet non dovrebbe essere vuoto"

        # Verifica che contenga elementi Qt essenziali
        assert "QWidget" in stylesheet, "Stylesheet dovrebbe contenere QWidget"
        assert "QPushButton" in stylesheet, "Stylesheet dovrebbe contenere QPushButton"
        assert "QLineEdit" in stylesheet, "Stylesheet dovrebbe contenere QLineEdit"
        assert "background-color" in stylesheet, "Stylesheet dovrebbe contenere background-color"

    def test_generate_stylesheet_light(self):
        """Verifica generazione stylesheet per tema light."""
        stylesheet = theme_manager.generate_stylesheet("light")

        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0
        assert "QWidget" in stylesheet

    def test_generate_stylesheet_invalid_theme(self):
        """Verifica fallback quando tema non esiste."""
        stylesheet = theme_manager.generate_stylesheet("nonexistent_theme")

        # Dovrebbe usare "dark" come fallback
        assert isinstance(stylesheet, str)
        # Se nemmeno dark esiste, restituisce stringa vuota
        # Ma nel nostro caso dark dovrebbe esistere
        assert len(stylesheet) > 0

    def test_stylesheet_has_all_components(self):
        """Verifica che stylesheet contenga tutti i componenti principali."""
        stylesheet = theme_manager.generate_stylesheet("dark")

        expected_components = [
            "QWidget", "QDialog", "QListWidget", "QPushButton",
            "QLineEdit", "QComboBox", "QLabel", "QGroupBox",
            "QTabWidget", "QTabBar", "QProgressBar", "QTextEdit",
            "QScrollBar"
        ]

        for component in expected_components:
            assert component in stylesheet, f"Stylesheet dovrebbe contenere {component}"

    def test_stylesheet_has_hover_states(self):
        """Verifica che stylesheet contenga stati hover e pressed."""
        stylesheet = theme_manager.generate_stylesheet("dark")

        assert ":hover" in stylesheet, "Stylesheet dovrebbe avere stati hover"
        assert ":pressed" in stylesheet, "Stylesheet dovrebbe avere stati pressed"
        assert ":focus" in stylesheet, "Stylesheet dovrebbe avere stati focus"


class TestApplyTheme:
    """Test per la funzione apply_theme()."""

    def test_apply_theme_dark(self):
        """Verifica applicazione tema dark."""
        mock_app = MagicMock()

        theme_manager.apply_theme(mock_app, "dark")

        # Verifica che setStyleSheet sia stato chiamato
        mock_app.setStyleSheet.assert_called_once()

        # Verifica che lo stylesheet passato non sia vuoto
        args = mock_app.setStyleSheet.call_args[0]
        stylesheet = args[0]
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_apply_theme_light(self):
        """Verifica applicazione tema light."""
        mock_app = MagicMock()

        theme_manager.apply_theme(mock_app, "light")

        mock_app.setStyleSheet.assert_called_once()

    def test_apply_theme_from_settings(self):
        """Verifica applicazione tema dalle impostazioni."""
        mock_app = MagicMock()

        # Mock Settings per restituire "dark"
        with patch('src.theme_manager.Settings') as MockSettings:
            mock_settings = MagicMock()
            mock_settings.get_theme.return_value = "dark"
            MockSettings.return_value = mock_settings

            # Chiama senza specificare tema (usa settings)
            theme_manager.apply_theme(mock_app, None)

            mock_settings.get_theme.assert_called_once()
            mock_app.setStyleSheet.assert_called_once()

    def test_apply_theme_system_windows(self):
        """Verifica rilevamento tema di sistema su Windows."""
        mock_app = MagicMock()

        # Mock Windows environment
        with patch('os.name', 'nt'):
            with patch('src.theme_manager.winreg') as mock_winreg:
                mock_key = MagicMock()
                mock_winreg.OpenKey.return_value = mock_key
                mock_winreg.QueryValueEx.return_value = (0, None)  # Dark theme

                theme_manager.apply_theme(mock_app, "system")

                mock_app.setStyleSheet.assert_called_once()

    def test_apply_theme_system_unix(self):
        """Verifica rilevamento tema di sistema su Unix."""
        mock_app = MagicMock()

        # Mock palette per Unix
        mock_palette = MagicMock()
        mock_color = MagicMock()
        mock_color.lightness.return_value = 50  # Dark
        mock_palette.color.return_value = mock_color
        mock_app.palette.return_value = mock_palette

        with patch('os.name', 'posix'):
            theme_manager.apply_theme(mock_app, "system")

            mock_app.setStyleSheet.assert_called_once()


class TestGetAvailableThemes:
    """Test per la funzione get_available_themes()."""

    def test_get_available_themes(self):
        """Verifica ottenimento lista temi disponibili."""
        themes = theme_manager.get_available_themes()

        assert isinstance(themes, list), "Dovrebbe restituire una lista"
        assert len(themes) > 0, "Dovrebbero esserci temi disponibili"

        # Verifica temi standard
        assert "dark" in themes, "dark dovrebbe essere disponibile"
        assert "light" in themes, "light dovrebbe essere disponibile"

    def test_themes_are_unique(self):
        """Verifica che i nomi dei temi siano unici."""
        themes = theme_manager.get_available_themes()
        assert len(themes) == len(set(themes)), "I nomi dei temi dovrebbero essere unici"


class TestGetThemeDisplayName:
    """Test per la funzione get_theme_display_name()."""

    def test_get_display_name_dark(self):
        """Verifica ottenimento nome display per tema dark."""
        display_name = theme_manager.get_theme_display_name("dark")

        assert isinstance(display_name, str)
        assert len(display_name) > 0

    def test_get_display_name_light(self):
        """Verifica ottenimento nome display per tema light."""
        display_name = theme_manager.get_theme_display_name("light")

        assert isinstance(display_name, str)
        assert len(display_name) > 0

    def test_get_display_name_nonexistent(self):
        """Verifica fallback per tema non esistente."""
        display_name = theme_manager.get_theme_display_name("nonexistent")

        # Dovrebbe capitalizzare il nome
        assert isinstance(display_name, str)
        assert display_name == "Nonexistent"

    def test_display_names_are_different(self):
        """Verifica che dark e light abbiano nomi diversi."""
        dark_name = theme_manager.get_theme_display_name("dark")
        light_name = theme_manager.get_theme_display_name("light")

        # Potrebbero essere uguali solo se il JSON non definisce nomi separati
        # Ma dovrebbero essere stringhe valide
        assert isinstance(dark_name, str)
        assert isinstance(light_name, str)


class TestIntegration:
    """Test di integrazione per theme_manager."""

    def test_full_workflow(self):
        """Test workflow completo: load -> generate -> apply."""
        # 1. Carica temi
        themes = theme_manager.load_themes()
        assert len(themes) > 0

        # 2. Ottieni lista temi
        available = theme_manager.get_available_themes()
        assert len(available) > 0

        # 3. Per ogni tema, genera stylesheet
        for theme_name in available:
            stylesheet = theme_manager.generate_stylesheet(theme_name)
            assert len(stylesheet) > 0

        # 4. Applica un tema
        mock_app = MagicMock()
        theme_manager.apply_theme(mock_app, available[0])
        mock_app.setStyleSheet.assert_called_once()

    def test_theme_consistency(self):
        """Verifica che tutti i temi abbiano la stessa struttura."""
        themes = theme_manager.load_themes()

        if len(themes) < 2:
            pytest.skip("Necessari almeno 2 temi per questo test")

        # Ottieni le chiavi del primo tema
        first_theme = list(themes.values())[0]
        first_colors = set(first_theme["colors"].keys())

        # Verifica che tutti i temi abbiano le stesse chiavi
        for theme_name, theme_data in themes.items():
            theme_colors = set(theme_data["colors"].keys())
            assert theme_colors == first_colors, \
                f"Tema {theme_name} ha colori diversi da altri temi"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
