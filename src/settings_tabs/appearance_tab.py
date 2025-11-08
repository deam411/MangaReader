"""
Tab impostazioni aspetto: tema applicazione.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox,
                              QGroupBox)
from PyQt5.QtCore import pyqtSignal
from ..settings import Settings


class AppearanceTab(QWidget):
    """Tab per impostazioni aspetto (tema)."""

    theme_changed = pyqtSignal()  # Segnale emesso quando il tema cambia

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.parent_dialog = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Gruppo Tema
        theme_group = QGroupBox("Tema")
        theme_layout = QVBoxLayout()

        theme_label = QLabel("Seleziona tema:")
        theme_layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Sistema", "Scuro", "Chiaro"])
        current_theme = self.settings.get_theme()
        if current_theme == "system":
            self.theme_combo.setCurrentText("Sistema")
        elif current_theme == "dark":
            self.theme_combo.setCurrentText("Scuro")
        else:
            self.theme_combo.setCurrentText("Chiaro")
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)

        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        layout.addStretch()
        self.setLayout(layout)

    def on_theme_changed(self):
        """Handler per cambio tema."""
        self.theme_changed.emit()

    def get_values(self):
        """Ritorna i valori correnti del tab."""
        theme_text = self.theme_combo.currentText()
        if theme_text == "Sistema":
            theme = "system"
        elif theme_text == "Scuro":
            theme = "dark"
        else:
            theme = "light"

        return {
            "theme": theme
        }
