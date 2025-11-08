"""
Tab impostazioni scorciatoie tastiera personalizzabili.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QGroupBox, QMessageBox)
from ..settings import Settings


class ShortcutsTab(QWidget):
    """Tab per impostazioni scorciatoie tastiera."""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.parent_dialog = parent
        self.shortcut_inputs = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Info header
        info_label = QLabel(
            "Personalizza le scorciatoie tastiera. Usa formati come: Ctrl+K, Alt+F, F11, ecc.\n"
            "Lascia vuoto per disabilitare una scorciatoia."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 10px; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

        # Ottieni tutte le scorciatoie
        shortcuts = self.settings.get_all_shortcuts()

        # Gruppo Navigazione
        nav_group = QGroupBox("Navigazione")
        nav_layout = QVBoxLayout()

        nav_shortcuts = {
            "next_page": "Pagina successiva",
            "prev_page": "Pagina precedente",
            "back": "Indietro",
            "quit": "Esci"
        }

        for key, label in nav_shortcuts.items():
            if key in shortcuts:
                row = QHBoxLayout()
                row.addWidget(QLabel(label + ":"))

                input_field = QLineEdit()
                input_field.setText(shortcuts.get(key, ""))
                input_field.setPlaceholderText("Es: Ctrl+N, F5, etc.")
                self.shortcut_inputs[key] = input_field

                row.addWidget(input_field)
                nav_layout.addLayout(row)

        nav_group.setLayout(nav_layout)
        layout.addWidget(nav_group)

        # Gruppo Interfaccia
        ui_group = QGroupBox("Interfaccia")
        ui_layout = QVBoxLayout()

        ui_shortcuts = {
            "fullscreen": "Schermo intero",
            "settings": "Impostazioni",
            "help": "Aiuto",
            "search": "Cerca",
            "bookmarks": "Segnalibri"
        }

        for key, label in ui_shortcuts.items():
            if key in shortcuts:
                row = QHBoxLayout()
                row.addWidget(QLabel(label + ":"))

                input_field = QLineEdit()
                input_field.setText(shortcuts.get(key, ""))
                input_field.setPlaceholderText("Es: F11, Ctrl+F, etc.")
                self.shortcut_inputs[key] = input_field

                row.addWidget(input_field)
                ui_layout.addLayout(row)

        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)

        # Gruppo Manga
        manga_group = QGroupBox("Gestione Manga")
        manga_layout = QVBoxLayout()

        manga_shortcuts = {
            "new_manga": "Nuovo Manga",
            "import": "Importa",
            "export": "Esporta",
            "refresh": "Aggiorna"
        }

        for key, label in manga_shortcuts.items():
            if key in shortcuts:
                row = QHBoxLayout()
                row.addWidget(QLabel(label + ":"))

                input_field = QLineEdit()
                input_field.setText(shortcuts.get(key, ""))
                input_field.setPlaceholderText("Es: Ctrl+N, F5, etc.")
                self.shortcut_inputs[key] = input_field

                row.addWidget(input_field)
                manga_layout.addLayout(row)

        manga_group.setLayout(manga_layout)
        layout.addWidget(manga_group)

        # Pulsante ripristina default scorciatoie
        reset_shortcuts_btn = QPushButton("Ripristina Scorciatoie Default")
        reset_shortcuts_btn.clicked.connect(self._reset_shortcuts_to_default)
        layout.addWidget(reset_shortcuts_btn)

        layout.addStretch()
        self.setLayout(layout)

    def _reset_shortcuts_to_default(self):
        """Ripristina le scorciatoie ai valori di default."""
        reply = QMessageBox.question(
            self,
            "Ripristina scorciatoie",
            "Ripristinare tutte le scorciatoie ai valori di default?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Ottieni shortcuts default
            default_settings = self.settings._get_default_settings()
            default_shortcuts = default_settings.get("shortcuts", {})

            # Aggiorna i campi input
            for key, value in default_shortcuts.items():
                if key in self.shortcut_inputs:
                    self.shortcut_inputs[key].setText(value)

            QMessageBox.information(
                self,
                "Scorciatoie Ripristinate",
                "Le scorciatoie sono state ripristinate ai valori di default."
            )

    def get_values(self):
        """Ritorna i valori correnti del tab."""
        shortcuts = {}
        for key, input_field in self.shortcut_inputs.items():
            shortcuts[f"shortcuts.{key}"] = input_field.text()

        return shortcuts
