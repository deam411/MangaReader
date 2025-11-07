"""
Modulo per la gestione centralizzata dei temi dell'applicazione.

Carica le definizioni dei temi da themes.json e genera dinamicamente
gli stylesheet Qt per l'applicazione.
"""

import json
import os
from typing import Dict, Optional
from .logger import get_logger

logger = get_logger(__name__)


def load_themes() -> Dict:
    """
    Carica le definizioni dei temi dal file themes.json.

    Returns:
        Dizionario con le definizioni dei temi
    """
    try:
        themes_path = os.path.join(os.path.dirname(__file__), 'themes.json')
        with open(themes_path, 'r', encoding='utf-8') as f:
            themes = json.load(f)
        logger.debug(f"Temi caricati con successo da {themes_path}")
        return themes
    except FileNotFoundError:
        logger.error(f"File themes.json non trovato in {os.path.dirname(__file__)}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Errore nel parsing di themes.json: {e}")
        return {}
    except Exception as e:
        logger.error(f"Errore nel caricamento dei temi: {e}")
        return {}


def generate_stylesheet(theme_name: str) -> str:
    """
    Genera lo stylesheet Qt per il tema specificato.

    Args:
        theme_name: Nome del tema (es. "dark", "light")

    Returns:
        Stringa contenente lo stylesheet Qt
    """
    themes = load_themes()

    if theme_name not in themes:
        logger.warning(f"Tema '{theme_name}' non trovato, uso 'dark' come fallback")
        theme_name = "dark"
        if theme_name not in themes:
            logger.error("Nessun tema disponibile")
            return ""

    colors = themes[theme_name]["colors"]
    logger.info(f"Generazione stylesheet per tema: {theme_name}")

    # Genera lo stylesheet usando i colori dal JSON
    stylesheet = f"""
        QWidget {{
            background-color: {colors['widget_bg']};
            color: {colors['widget_fg']};
        }}
        QDialog {{
            background-color: {colors['dialog_bg']};
            color: {colors['dialog_fg']};
        }}
        QListWidget {{
            background-color: {colors['listwidget_bg']};
            border: 1px solid {colors['listwidget_border']};
        }}
        QPushButton {{
            background-color: {colors['button_bg']};
            border: 1px solid {colors['button_border']};
            padding: 5px;
            border-radius: 3px;
            color: {colors['button_fg']};
        }}
        QPushButton:hover {{
            background-color: {colors['button_hover_bg']};
        }}
        QPushButton:pressed {{
            background-color: {colors['button_pressed_bg']};
        }}
        QLineEdit {{
            background-color: {colors['lineedit_bg']};
            border: 2px solid {colors['lineedit_border']};
            padding: 8px;
            border-radius: 4px;
            color: {colors['lineedit_fg']};
            selection-background-color: {colors['lineedit_selection_bg']};
            selection-color: {colors['lineedit_selection_fg']};
        }}
        QLineEdit:focus {{
            border: 2px solid {colors['lineedit_focus_border']};
            background-color: {colors['lineedit_focus_bg']};
        }}
        QLineEdit::placeholder {{
            color: {colors['lineedit_placeholder']};
        }}
        QComboBox {{
            background-color: {colors['combobox_bg']};
            border: 2px solid {colors['combobox_border']};
            padding: 6px;
            padding-right: 25px;
            border-radius: 4px;
            color: {colors['combobox_fg']};
        }}
        QComboBox:focus {{
            border: 2px solid {colors['combobox_focus_border']};
        }}
        QComboBox QAbstractItemView {{
            background-color: {colors['combobox_dropdown_bg']};
            selection-background-color: {colors['combobox_dropdown_selection_bg']};
            color: {colors['combobox_dropdown_fg']};
            border: 1px solid {colors['combobox_dropdown_border']};
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QLabel {{
            background-color: {colors['label_bg']};
            color: {colors['label_fg']};
        }}
        QGroupBox {{
            background-color: {colors['groupbox_bg']};
            border: 1px solid {colors['groupbox_border']};
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            color: {colors['groupbox_fg']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            color: {colors['groupbox_fg']};
        }}
        QTabWidget::pane {{
            border: 1px solid {colors['tabwidget_pane_border']};
            background-color: {colors['tabwidget_pane_bg']};
        }}
        QTabBar::tab {{
            background-color: {colors['tabbar_tab_bg']};
            border: 1px solid {colors['tabbar_tab_border']};
            padding: 8px 20px;
            color: {colors['tabbar_tab_fg']};
        }}
        QTabBar::tab:hover {{
            background-color: {colors['tabbar_tab_hover_bg']};
        }}
        QTabBar::tab:selected {{
            background-color: {colors['tabbar_tab_selected_bg']};
            border-bottom-color: {colors['tabbar_tab_selected_border']};
            border-bottom-width: 2px;
        }}
        QProgressBar {{
            background-color: {colors['progressbar_bg']};
            border: 1px solid {colors['progressbar_border']};
            border-radius: 5px;
            text-align: center;
            color: {colors['progressbar_text_fg']};
        }}
        QProgressBar::chunk {{
            background-color: {colors['progressbar_chunk_bg']};
            border-radius: 5px;
        }}
        QTextEdit {{
            background-color: {colors['textedit_bg']};
            color: {colors['textedit_fg']};
            border: 1px solid {colors['textedit_border']};
        }}
        QScrollBar:vertical {{
            background-color: {colors['scrollbar_bg']};
            width: 12px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {colors['scrollbar_handle_bg']};
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {colors['scrollbar_handle_hover_bg']};
        }}
    """

    return stylesheet


def apply_theme(app, theme_name: Optional[str] = None) -> None:
    """
    Applica un tema all'applicazione Qt.

    Args:
        app: Istanza di QApplication
        theme_name: Nome del tema da applicare. Se None, usa il tema salvato nelle impostazioni.
    """
    try:
        # Se non è specificato un tema, carica dalle impostazioni
        if theme_name is None:
            from .settings import Settings
            settings = Settings()
            theme_name = settings.get_theme()
            logger.debug(f"Tema dalle impostazioni: {theme_name}")

        # Se il tema è "system", rileva il tema del sistema
        if theme_name == "system":
            if os.name == 'nt':
                # Windows: rileva tema dal registro
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                        r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    theme_name = "light" if value == 1 else "dark"
                    logger.debug(f"Tema rilevato da Windows: {theme_name}")
                except Exception as e:
                    logger.warning(f"Impossibile rilevare tema di sistema Windows: {e}")
                    theme_name = "dark"
            else:
                # Unix/Mac: usa Qt palette come fallback
                from PyQt5.QtWidgets import QApplication
                from PyQt5.QtGui import QPalette
                palette = app.palette()
                bg_color = palette.color(QPalette.Window)
                # Se il colore di sfondo è chiaro, usa tema light
                theme_name = "light" if bg_color.lightness() > 128 else "dark"
                logger.debug(f"Tema rilevato da palette Qt: {theme_name}")

        # Genera e applica lo stylesheet
        stylesheet = generate_stylesheet(theme_name)
        if stylesheet:
            app.setStyleSheet(stylesheet)
            logger.info(f"Tema '{theme_name}' applicato con successo")
        else:
            logger.error("Impossibile generare stylesheet")

    except Exception as e:
        logger.error(f"Errore nell'applicazione del tema: {e}")


def get_available_themes() -> list:
    """
    Restituisce la lista dei temi disponibili.

    Returns:
        Lista di nomi di temi disponibili
    """
    themes = load_themes()
    return list(themes.keys())


def get_theme_display_name(theme_name: str) -> str:
    """
    Restituisce il nome visualizzato per un tema.

    Args:
        theme_name: Nome interno del tema

    Returns:
        Nome visualizzato del tema
    """
    themes = load_themes()
    if theme_name in themes:
        return themes[theme_name].get("name", theme_name.capitalize())
    return theme_name.capitalize()
