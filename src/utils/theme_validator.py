"""
Theme validator con JSON Schema.

Modulo per validazione struttura temi JSON, garantendo che tutti i temi
abbiano la struttura corretta e colori validi.
"""

import json
import re
from typing import Dict, Any, List, Optional
from ..exceptions import ValidationError


# Colori richiesti in ogni tema
REQUIRED_COLOR_FIELDS = [
    "widget_bg", "widget_fg",
    "dialog_bg", "dialog_fg",
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


def is_valid_color(color: str) -> bool:
    """
    Verifica se una stringa è un colore valido.

    Args:
        color: Stringa colore da validare

    Returns:
        True se il colore è valido (hex o 'transparent'), False altrimenti
    """
    if not color or not isinstance(color, str):
        return False

    # Permetti "transparent"
    if color.lower() == "transparent":
        return True

    # Valida hex color (#RGB o #RRGGBB)
    hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    return bool(re.match(hex_pattern, color))


def validate_theme_colors(colors: Dict[str, str], theme_name: str) -> List[str]:
    """
    Valida i colori di un tema.

    Args:
        colors: Dizionario colori del tema
        theme_name: Nome del tema (per error messages)

    Returns:
        Lista di errori (vuota se validazione ok)
    """
    errors = []

    if not isinstance(colors, dict):
        errors.append(f"Theme '{theme_name}': 'colors' deve essere un oggetto")
        return errors

    # Verifica che tutti i campi richiesti siano presenti
    for field in REQUIRED_COLOR_FIELDS:
        if field not in colors:
            errors.append(f"Theme '{theme_name}': campo colore mancante '{field}'")

    # Verifica che tutti i colori siano validi
    for field, color in colors.items():
        if not is_valid_color(color):
            errors.append(
                f"Theme '{theme_name}': colore invalido per '{field}': '{color}' "
                f"(deve essere #RGB, #RRGGBB o 'transparent')"
            )

    return errors


def validate_theme(theme_data: Dict[str, Any], theme_id: str) -> List[str]:
    """
    Valida la struttura di un singolo tema.

    Args:
        theme_data: Dati del tema
        theme_id: ID del tema (chiave nel JSON)

    Returns:
        Lista di errori (vuota se validazione ok)
    """
    errors = []

    if not isinstance(theme_data, dict):
        errors.append(f"Theme '{theme_id}': deve essere un oggetto")
        return errors

    # Verifica campo 'name'
    if "name" not in theme_data:
        errors.append(f"Theme '{theme_id}': campo 'name' mancante")
    elif not isinstance(theme_data["name"], str):
        errors.append(f"Theme '{theme_id}': 'name' deve essere una stringa")
    elif not theme_data["name"].strip():
        errors.append(f"Theme '{theme_id}': 'name' non può essere vuoto")

    # Verifica campo 'colors'
    if "colors" not in theme_data:
        errors.append(f"Theme '{theme_id}': campo 'colors' mancante")
    else:
        # Valida i colori
        color_errors = validate_theme_colors(theme_data["colors"], theme_id)
        errors.extend(color_errors)

    return errors


def validate_themes_json(themes_data: Dict[str, Any]) -> List[str]:
    """
    Valida l'intero file themes.json.

    Args:
        themes_data: Dizionario caricato da themes.json

    Returns:
        Lista di errori (vuota se validazione ok)
    """
    errors = []

    if not isinstance(themes_data, dict):
        errors.append("Il file themes.json deve contenere un oggetto JSON")
        return errors

    if not themes_data:
        errors.append("Il file themes.json non può essere vuoto")
        return errors

    # Valida ogni tema
    for theme_id, theme_data in themes_data.items():
        theme_errors = validate_theme(theme_data, theme_id)
        errors.extend(theme_errors)

    return errors


def validate_themes_file(file_path: str) -> None:
    """
    Carica e valida un file themes.json.

    Args:
        file_path: Percorso al file themes.json

    Raises:
        ValidationError: Se la validazione fallisce
        FileNotFoundError: Se il file non esiste
        json.JSONDecodeError: Se il JSON è malformato
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            themes_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File themes.json non trovato: {file_path}")
    except json.JSONDecodeError as e:
        raise ValidationError(f"JSON malformato in themes.json: {e}")

    errors = validate_themes_json(themes_data)

    if errors:
        error_msg = "Errori di validazione in themes.json:\n" + "\n".join(f"  - {err}" for err in errors)
        raise ValidationError(error_msg)


def get_theme_schema() -> Dict[str, Any]:
    """
    Ritorna lo schema JSON per un tema.

    Returns:
        Schema JSON in formato dict
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "MangaReader Theme",
        "type": "object",
        "patternProperties": {
            "^[a-z_]+$": {
                "type": "object",
                "required": ["name", "colors"],
                "properties": {
                    "name": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Nome visualizzato del tema"
                    },
                    "colors": {
                        "type": "object",
                        "description": "Colori del tema",
                        "patternProperties": {
                            ".*": {
                                "type": "string",
                                "pattern": "^(#[A-Fa-f0-9]{6}|#[A-Fa-f0-9]{3}|transparent)$"
                            }
                        }
                    }
                }
            }
        },
        "minProperties": 1
    }
