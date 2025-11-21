"""
Test suite per theme validation - Phase 4.2.

Tests JSON schema validation per themes.json.
"""

import sys
import os
import json
import tempfile


def test_color_validation():
    """Test validazione colori individuali."""
    print("Testing color validation...")

    from src.utils.theme_validator import is_valid_color

    # Test colori validi
    valid_colors = [
        "#ffffff",
        "#000000",
        "#FFF",
        "#abc",
        "#123456",
        "#AbCdEf",
        "transparent",
        "TRANSPARENT"
    ]

    for color in valid_colors:
        assert is_valid_color(color), f"Colore valido rifiutato: {color}"
        print(f"  ✓ Valid color accepted: {color}")

    # Test colori invalidi
    invalid_colors = [
        "",
        "red",
        "#gggggg",
        "#12345",
        "#1234567",
        "rgb(255,0,0)",
        None,
        "#",
        "##ffffff"
    ]

    for color in invalid_colors:
        assert not is_valid_color(color), f"Colore invalido accettato: {color}"
        print(f"  ✓ Invalid color rejected: {color}")

    print("✓ Color validation tests passed\n")
    return True


def test_theme_structure_validation():
    """Test validazione struttura tema."""
    print("Testing theme structure validation...")

    from src.utils.theme_validator import validate_theme

    # Test 1: Tema valido
    valid_theme = {
        "name": "Test Theme",
        "colors": {
            "widget_bg": "#ffffff",
            "widget_fg": "#000000",
            "dialog_bg": "#f0f0f0",
            "dialog_fg": "#000000",
            "listwidget_bg": "#ffffff",
            "listwidget_border": "#cccccc",
            "button_bg": "#e0e0e0",
            "button_border": "#999999",
            "button_fg": "#000000",
            "button_hover_bg": "#d0d0d0",
            "button_pressed_bg": "#c0c0c0",
            "lineedit_bg": "#ffffff",
            "lineedit_border": "#cccccc",
            "lineedit_fg": "#000000",
            "lineedit_focus_border": "#0078d7",
            "lineedit_focus_bg": "#ffffff",
            "lineedit_placeholder": "#888888",
            "lineedit_selection_bg": "#0078d7",
            "lineedit_selection_fg": "#ffffff",
            "combobox_bg": "#ffffff",
            "combobox_border": "#cccccc",
            "combobox_fg": "#000000",
            "combobox_focus_border": "#0078d7",
            "combobox_dropdown_bg": "#ffffff",
            "combobox_dropdown_selection_bg": "#0078d7",
            "combobox_dropdown_fg": "#000000",
            "combobox_dropdown_border": "#cccccc",
            "label_bg": "transparent",
            "label_fg": "#000000",
            "groupbox_bg": "#f0f0f0",
            "groupbox_border": "#cccccc",
            "groupbox_fg": "#000000",
            "tabwidget_pane_bg": "#f0f0f0",
            "tabwidget_pane_border": "#cccccc",
            "tabbar_tab_bg": "#e0e0e0",
            "tabbar_tab_fg": "#000000",
            "tabbar_tab_border": "#cccccc",
            "tabbar_tab_hover_bg": "#d0d0d0",
            "tabbar_tab_selected_bg": "#f0f0f0",
            "tabbar_tab_selected_border": "#0078d7",
            "progressbar_bg": "#ffffff",
            "progressbar_border": "#cccccc",
            "progressbar_chunk_bg": "#4a90e2",
            "progressbar_text_fg": "#000000",
            "textedit_bg": "#ffffff",
            "textedit_fg": "#000000",
            "textedit_border": "#cccccc",
            "scrollbar_bg": "#f0f0f0",
            "scrollbar_handle_bg": "#c0c0c0",
            "scrollbar_handle_hover_bg": "#a0a0a0"
        }
    }

    errors = validate_theme(valid_theme, "test")
    assert len(errors) == 0, f"Tema valido rifiutato: {errors}"
    print("  ✓ Valid theme accepted")

    # Test 2: Tema senza 'name'
    theme_no_name = {
        "colors": {"widget_bg": "#ffffff"}
    }
    errors = validate_theme(theme_no_name, "test")
    assert len(errors) > 0, "Tema senza 'name' dovrebbe essere rifiutato"
    assert any("name" in err.lower() for err in errors)
    print("  ✓ Theme without 'name' rejected")

    # Test 3: Tema senza 'colors'
    theme_no_colors = {
        "name": "Test"
    }
    errors = validate_theme(theme_no_colors, "test")
    assert len(errors) > 0, "Tema senza 'colors' dovrebbe essere rifiutato"
    assert any("colors" in err.lower() for err in errors)
    print("  ✓ Theme without 'colors' rejected")

    # Test 4: Tema con colore invalido
    theme_invalid_color = {
        "name": "Test",
        "colors": {
            "widget_bg": "not_a_color"
        }
    }
    errors = validate_theme(theme_invalid_color, "test")
    assert len(errors) > 0, "Tema con colore invalido dovrebbe essere rifiutato"
    print("  ✓ Theme with invalid color rejected")

    # Test 5: Tema con campo mancante
    theme_missing_field = {
        "name": "Test",
        "colors": {
            "widget_bg": "#ffffff"
            # Mancano tutti gli altri campi richiesti
        }
    }
    errors = validate_theme(theme_missing_field, "test")
    assert len(errors) > 0, "Tema con campi mancanti dovrebbe essere rifiutato"
    print(f"  ✓ Theme with missing fields rejected ({len(errors)} missing fields)")

    print("✓ Theme structure validation tests passed\n")
    return True


def test_themes_json_validation():
    """Test validazione completo file themes.json."""
    print("Testing complete themes.json validation...")

    from src.utils.theme_validator import validate_themes_json

    # Test 1: File valido con due temi
    valid_themes = {
        "dark": {
            "name": "Dark Theme",
            "colors": {
                "widget_bg": "#2b2b2b",
                "widget_fg": "#ffffff",
                "dialog_bg": "#2b2b2b",
                "dialog_fg": "#ffffff",
                "listwidget_bg": "#1e1e1e",
                "listwidget_border": "#3d3d3d",
                "button_bg": "#3d3d3d",
                "button_border": "#555555",
                "button_fg": "#ffffff",
                "button_hover_bg": "#4a4a4a",
                "button_pressed_bg": "#555555",
                "lineedit_bg": "#3d3d3d",
                "lineedit_border": "#555555",
                "lineedit_fg": "#ffffff",
                "lineedit_focus_border": "#6a6a6a",
                "lineedit_focus_bg": "#454545",
                "lineedit_placeholder": "#aaaaaa",
                "lineedit_selection_bg": "#4a4a4a",
                "lineedit_selection_fg": "#ffffff",
                "combobox_bg": "#3d3d3d",
                "combobox_border": "#555555",
                "combobox_fg": "#ffffff",
                "combobox_focus_border": "#6a6a6a",
                "combobox_dropdown_bg": "#2b2b2b",
                "combobox_dropdown_selection_bg": "#4a4a4a",
                "combobox_dropdown_fg": "#ffffff",
                "combobox_dropdown_border": "#555555",
                "label_bg": "transparent",
                "label_fg": "#ffffff",
                "groupbox_bg": "#2b2b2b",
                "groupbox_border": "#3d3d3d",
                "groupbox_fg": "#ffffff",
                "tabwidget_pane_bg": "#2b2b2b",
                "tabwidget_pane_border": "#3d3d3d",
                "tabbar_tab_bg": "#3d3d3d",
                "tabbar_tab_fg": "#ffffff",
                "tabbar_tab_border": "#555555",
                "tabbar_tab_hover_bg": "#4a4a4a",
                "tabbar_tab_selected_bg": "#2b2b2b",
                "tabbar_tab_selected_border": "#6a6a6a",
                "progressbar_bg": "#1e1e1e",
                "progressbar_border": "#3d3d3d",
                "progressbar_chunk_bg": "#4a90e2",
                "progressbar_text_fg": "#ffffff",
                "textedit_bg": "#1e1e1e",
                "textedit_fg": "#ffffff",
                "textedit_border": "#3d3d3d",
                "scrollbar_bg": "#1e1e1e",
                "scrollbar_handle_bg": "#4a4a4a",
                "scrollbar_handle_hover_bg": "#555555"
            }
        },
        "light": {
            "name": "Light Theme",
            "colors": {
                "widget_bg": "#f0f0f0",
                "widget_fg": "#000000",
                "dialog_bg": "#f0f0f0",
                "dialog_fg": "#000000",
                "listwidget_bg": "#ffffff",
                "listwidget_border": "#cccccc",
                "button_bg": "#e0e0e0",
                "button_border": "#999999",
                "button_fg": "#000000",
                "button_hover_bg": "#d0d0d0",
                "button_pressed_bg": "#c0c0c0",
                "lineedit_bg": "#ffffff",
                "lineedit_border": "#cccccc",
                "lineedit_fg": "#000000",
                "lineedit_focus_border": "#0078d7",
                "lineedit_focus_bg": "#ffffff",
                "lineedit_placeholder": "#888888",
                "lineedit_selection_bg": "#0078d7",
                "lineedit_selection_fg": "#ffffff",
                "combobox_bg": "#ffffff",
                "combobox_border": "#cccccc",
                "combobox_fg": "#000000",
                "combobox_focus_border": "#0078d7",
                "combobox_dropdown_bg": "#ffffff",
                "combobox_dropdown_selection_bg": "#0078d7",
                "combobox_dropdown_fg": "#000000",
                "combobox_dropdown_border": "#cccccc",
                "label_bg": "transparent",
                "label_fg": "#000000",
                "groupbox_bg": "#f0f0f0",
                "groupbox_border": "#cccccc",
                "groupbox_fg": "#000000",
                "tabwidget_pane_bg": "#f0f0f0",
                "tabwidget_pane_border": "#cccccc",
                "tabbar_tab_bg": "#e0e0e0",
                "tabbar_tab_fg": "#000000",
                "tabbar_tab_border": "#cccccc",
                "tabbar_tab_hover_bg": "#d0d0d0",
                "tabbar_tab_selected_bg": "#f0f0f0",
                "tabbar_tab_selected_border": "#0078d7",
                "progressbar_bg": "#ffffff",
                "progressbar_border": "#cccccc",
                "progressbar_chunk_bg": "#4a90e2",
                "progressbar_text_fg": "#000000",
                "textedit_bg": "#ffffff",
                "textedit_fg": "#000000",
                "textedit_border": "#cccccc",
                "scrollbar_bg": "#f0f0f0",
                "scrollbar_handle_bg": "#c0c0c0",
                "scrollbar_handle_hover_bg": "#a0a0a0"
            }
        }
    }

    errors = validate_themes_json(valid_themes)
    assert len(errors) == 0, f"File valido rifiutato: {errors}"
    print("  ✓ Valid themes.json accepted")

    # Test 2: File vuoto
    errors = validate_themes_json({})
    assert len(errors) > 0, "File vuoto dovrebbe essere rifiutato"
    print("  ✓ Empty themes.json rejected")

    # Test 3: Non è un oggetto
    errors = validate_themes_json("not an object")
    assert len(errors) > 0, "Non-oggetto dovrebbe essere rifiutato"
    print("  ✓ Non-object rejected")

    print("✓ Complete themes.json validation tests passed\n")
    return True


def test_actual_themes_file():
    """Test validazione del file themes.json reale."""
    print("Testing actual themes.json file...")

    from src.utils.theme_validator import validate_themes_file

    themes_path = os.path.join("src", "themes.json")

    if not os.path.exists(themes_path):
        print(f"  ⊘ Themes file not found: {themes_path}")
        return True

    try:
        validate_themes_file(themes_path)
        print(f"  ✓ Actual themes.json is valid")
    except Exception as e:
        print(f"  ✗ Actual themes.json validation failed: {e}")
        return False

    print("✓ Actual themes.json validation passed\n")
    return True


def test_schema_generation():
    """Test generazione schema JSON."""
    print("Testing JSON schema generation...")

    from src.utils.theme_validator import get_theme_schema

    schema = get_theme_schema()

    # Verifica che lo schema abbia la struttura base
    assert "$schema" in schema
    assert "type" in schema
    assert schema["type"] == "object"
    print("  ✓ Schema has correct base structure")

    # Verifica che abbia pattern properties
    assert "patternProperties" in schema
    print("  ✓ Schema has pattern properties")

    # Verifica minProperties
    assert "minProperties" in schema
    assert schema["minProperties"] == 1
    print("  ✓ Schema requires at least one theme")

    print("✓ JSON schema generation tests passed\n")
    return True


def main():
    """Run all theme validation tests."""
    print("=" * 70)
    print("THEME VALIDATION TESTS - Phase 4.2")
    print("=" * 70)
    print()

    tests = [
        test_color_validation,
        test_theme_structure_validation,
        test_themes_json_validation,
        test_actual_themes_file,
        test_schema_generation,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()

    print("=" * 70)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed > 0:
        print(f"WARNING: {failed} tests failed")
        return 1
    else:
        print("ALL TESTS PASSED ✓")
        return 0


if __name__ == "__main__":
    sys.exit(main())
