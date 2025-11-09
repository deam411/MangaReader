"""
Test suite per la validazione dei temi con JSON Schema.

Testa il modulo theme_validator e lo schema JSON creato per
garantire che i temi siano validati correttamente.
"""

import json
import os
import pytest
from src.utils.theme_validator import (
    validate_themes_json,
    validate_theme,
    validate_theme_colors,
    is_valid_color
)


class TestColorValidation:
    """Test per la validazione dei colori."""

    def test_valid_hex_colors(self):
        """Testa colori esadecimali validi."""
        assert is_valid_color("#ffffff")
        assert is_valid_color("#000000")
        assert is_valid_color("#abc123")
        assert is_valid_color("#ABC123")
        assert is_valid_color("#FfFfFf")

    def test_valid_transparent(self):
        """Testa la parola chiave 'transparent'."""
        assert is_valid_color("transparent")
        assert is_valid_color("TRANSPARENT")
        assert is_valid_color("Transparent")

    def test_invalid_colors(self):
        """Testa colori invalidi."""
        assert not is_valid_color("")
        assert not is_valid_color("red")
        assert not is_valid_color("rgb(255,255,255)")
        assert not is_valid_color("#ff")  # Troppo corto
        assert not is_valid_color("#ggg")  # Caratteri invalidi
        assert not is_valid_color("ffffff")  # Manca #
        assert not is_valid_color(None)
        assert not is_valid_color(123)


class TestThemeValidation:
    """Test per la validazione di singoli temi."""

    def test_valid_theme(self):
        """Testa un tema valido."""
        theme = {
            "name": "Test Theme",
            "colors": {
                field: "#ffffff"
                for field in [
                    "widget_bg", "widget_fg", "dialog_bg", "dialog_fg",
                    "listwidget_bg", "listwidget_border",
                    "button_bg", "button_border", "button_fg",
                    "button_hover_bg", "button_pressed_bg",
                    "lineedit_bg", "lineedit_border", "lineedit_fg",
                    "lineedit_focus_border", "lineedit_focus_bg",
                    "lineedit_placeholder", "lineedit_selection_bg", "lineedit_selection_fg",
                    "combobox_bg", "combobox_border", "combobox_fg",
                    "combobox_focus_border", "combobox_dropdown_bg",
                    "combobox_dropdown_selection_bg", "combobox_dropdown_fg", "combobox_dropdown_border",
                    "label_bg", "label_fg",
                    "groupbox_bg", "groupbox_border", "groupbox_fg",
                    "tabwidget_pane_bg", "tabwidget_pane_border",
                    "tabbar_tab_bg", "tabbar_tab_fg", "tabbar_tab_border",
                    "tabbar_tab_hover_bg", "tabbar_tab_selected_bg", "tabbar_tab_selected_border",
                    "progressbar_bg", "progressbar_border", "progressbar_chunk_bg", "progressbar_text_fg",
                    "textedit_bg", "textedit_fg", "textedit_border",
                    "scrollbar_bg", "scrollbar_handle_bg", "scrollbar_handle_hover_bg"
                ]
            }
        }
        errors = validate_theme(theme, "test")
        assert len(errors) == 0

    def test_missing_name(self):
        """Testa tema senza campo 'name'."""
        theme = {
            "colors": {"widget_bg": "#ffffff"}
        }
        errors = validate_theme(theme, "test")
        assert any("name" in err.lower() and "mancante" in err.lower() for err in errors)

    def test_missing_colors(self):
        """Testa tema senza campo 'colors'."""
        theme = {
            "name": "Test"
        }
        errors = validate_theme(theme, "test")
        assert any("colors" in err.lower() and "mancante" in err.lower() for err in errors)

    def test_empty_name(self):
        """Testa tema con nome vuoto."""
        theme = {
            "name": "   ",
            "colors": {"widget_bg": "#ffffff"}
        }
        errors = validate_theme(theme, "test")
        assert any("name" in err.lower() and "vuoto" in err.lower() for err in errors)

    def test_invalid_color_values(self):
        """Testa tema con colori invalidi."""
        theme = {
            "name": "Test",
            "colors": {
                "widget_bg": "invalid_color",
                "widget_fg": "#ffffff"
            }
        }
        errors = validate_theme(theme, "test")
        assert any("invalid_color" in err for err in errors)

    def test_missing_color_fields(self):
        """Testa tema con campi colore mancanti."""
        theme = {
            "name": "Test",
            "colors": {
                "widget_bg": "#ffffff"
                # Mancano molti campi richiesti
            }
        }
        errors = validate_theme(theme, "test")
        assert len(errors) > 0
        assert any("mancante" in err.lower() for err in errors)


class TestThemesFileValidation:
    """Test per la validazione completa del file themes.json."""

    def test_valid_themes_file(self):
        """Testa validazione file themes.json reale."""
        # Carica il file themes.json del progetto
        themes_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'src',
            'themes.json'
        )

        with open(themes_path, 'r', encoding='utf-8') as f:
            themes = json.load(f)

        errors = validate_themes_json(themes)
        if errors:
            print("\nErrori validazione themes.json:")
            for err in errors:
                print(f"  - {err}")
        assert len(errors) == 0, f"themes.json ha {len(errors)} errori di validazione"

    def test_empty_themes_file(self):
        """Testa file themes vuoto."""
        themes = {}
        errors = validate_themes_json(themes)
        assert any("vuoto" in err.lower() for err in errors)

    def test_invalid_themes_structure(self):
        """Testa struttura themes invalida."""
        themes = []  # Deve essere un dict, non una lista
        errors = validate_themes_json(themes)
        assert any("oggetto" in err.lower() for err in errors)

    def test_multiple_themes(self):
        """Testa validazione con più temi."""
        themes = {
            "dark": {
                "name": "Dark",
                "colors": {field: "#000000" for field in get_all_required_fields()}
            },
            "light": {
                "name": "Light",
                "colors": {field: "#ffffff" for field in get_all_required_fields()}
            }
        }
        errors = validate_themes_json(themes)
        assert len(errors) == 0


class TestJSONSchemaFile:
    """Test per il file JSON Schema."""

    def test_schema_file_exists(self):
        """Verifica che il file schema esista."""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'src',
            'schemas',
            'theme_schema.json'
        )
        assert os.path.exists(schema_path), "File theme_schema.json non trovato"

    def test_schema_is_valid_json(self):
        """Verifica che lo schema sia JSON valido."""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'src',
            'schemas',
            'theme_schema.json'
        )

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert "title" in schema
        assert "type" in schema

    def test_schema_has_required_definitions(self):
        """Verifica che lo schema abbia le definizioni necessarie."""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'src',
            'schemas',
            'theme_schema.json'
        )

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        assert "definitions" in schema
        assert "color" in schema["definitions"]
        assert "pattern" in schema["definitions"]["color"]


# Helper functions
def get_all_required_fields():
    """Ritorna tutti i campi colore richiesti."""
    return [
        "widget_bg", "widget_fg", "dialog_bg", "dialog_fg",
        "listwidget_bg", "listwidget_border",
        "button_bg", "button_border", "button_fg",
        "button_hover_bg", "button_pressed_bg",
        "lineedit_bg", "lineedit_border", "lineedit_fg",
        "lineedit_focus_border", "lineedit_focus_bg",
        "lineedit_placeholder", "lineedit_selection_bg", "lineedit_selection_fg",
        "combobox_bg", "combobox_border", "combobox_fg",
        "combobox_focus_border", "combobox_dropdown_bg",
        "combobox_dropdown_selection_bg", "combobox_dropdown_fg", "combobox_dropdown_border",
        "label_bg", "label_fg",
        "groupbox_bg", "groupbox_border", "groupbox_fg",
        "tabwidget_pane_bg", "tabwidget_pane_border",
        "tabbar_tab_bg", "tabbar_tab_fg", "tabbar_tab_border",
        "tabbar_tab_hover_bg", "tabbar_tab_selected_bg", "tabbar_tab_selected_border",
        "progressbar_bg", "progressbar_border", "progressbar_chunk_bg", "progressbar_text_fg",
        "textedit_bg", "textedit_fg", "textedit_border",
        "scrollbar_bg", "scrollbar_handle_bg", "scrollbar_handle_hover_bg"
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
