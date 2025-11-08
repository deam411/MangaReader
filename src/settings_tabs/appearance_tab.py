"""
Tab impostazioni aspetto: tema applicazione e sfondo libreria.
"""
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                              QGroupBox, QPushButton, QLineEdit, QFileDialog, QColorDialog)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor
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

        # Gruppo Personalizzazione Sfondo LIBRERIA
        background_group = QGroupBox("Sfondo Libreria")
        background_layout = QVBoxLayout()

        # Info importante
        library_info = QLabel(
            "Personalizza lo sfondo della schermata principale (LibraryView)"
        )
        library_info.setWordWrap(True)
        library_info.setStyleSheet("color: gray; font-size: 10px; font-style: italic; padding: 5px;")
        background_layout.addWidget(library_info)

        # Colore sfondo
        color_layout = QHBoxLayout()
        color_label = QLabel("Colore sfondo:")
        color_layout.addWidget(color_label)

        self.bg_color_button = QPushButton("Seleziona Colore")
        self.current_bg_color = self.settings.get("library.background_color", "#2b2b2b")
        self.bg_color_button.setStyleSheet(f"background-color: {self.current_bg_color}; color: white;")
        self.bg_color_button.clicked.connect(self._select_bg_color)
        color_layout.addWidget(self.bg_color_button)

        self.bg_color_label = QLabel(self.current_bg_color)
        self.bg_color_label.setStyleSheet("color: gray; font-size: 10px;")
        color_layout.addWidget(self.bg_color_label)
        color_layout.addStretch()
        background_layout.addLayout(color_layout)

        # Immagine sfondo
        image_layout = QHBoxLayout()
        image_label = QLabel("Immagine sfondo:")
        image_layout.addWidget(image_label)

        self.bg_image_input = QLineEdit()
        current_bg_image = self.settings.get("library.background_image", "")
        self.bg_image_input.setText(current_bg_image if current_bg_image else "Nessuna")
        self.bg_image_input.setReadOnly(True)
        image_layout.addWidget(self.bg_image_input)

        select_image_btn = QPushButton("Seleziona")
        select_image_btn.clicked.connect(self._select_bg_image)
        image_layout.addWidget(select_image_btn)

        clear_image_btn = QPushButton("Rimuovi")
        clear_image_btn.clicked.connect(self._clear_bg_image)
        image_layout.addWidget(clear_image_btn)

        background_layout.addLayout(image_layout)

        # Info
        bg_info_label = QLabel(
            "L'immagine di sfondo ha priorità sul colore.\n"
            "Formati supportati: PNG, JPG, JPEG, BMP"
        )
        bg_info_label.setWordWrap(True)
        bg_info_label.setStyleSheet("color: gray; font-size: 10px; font-style: italic;")
        background_layout.addWidget(bg_info_label)

        background_group.setLayout(background_layout)
        layout.addWidget(background_group)

        layout.addStretch()
        self.setLayout(layout)

    def on_theme_changed(self):
        """Handler per cambio tema."""
        self.theme_changed.emit()

    def _select_bg_color(self):
        """Apre il dialog per selezionare il colore di sfondo."""
        color = QColorDialog.getColor(
            QColor(self.current_bg_color),
            self,
            "Seleziona Colore Sfondo Libreria"
        )

        if color.isValid():
            self.current_bg_color = color.name()
            self.bg_color_button.setStyleSheet(f"background-color: {self.current_bg_color}; color: white;")
            self.bg_color_label.setText(self.current_bg_color)

    def _select_bg_image(self):
        """Apre il dialog per selezionare l'immagine di sfondo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona Immagine Sfondo Libreria",
            os.path.expanduser("~"),
            "Immagini (*.png *.jpg *.jpeg *.bmp)"
        )

        if file_path:
            self.bg_image_input.setText(file_path)

    def _clear_bg_image(self):
        """Rimuove l'immagine di sfondo."""
        self.bg_image_input.setText("Nessuna")

    def get_values(self):
        """Ritorna i valori correnti del tab."""
        theme_text = self.theme_combo.currentText()
        if theme_text == "Sistema":
            theme = "system"
        elif theme_text == "Scuro":
            theme = "dark"
        else:
            theme = "light"

        # Background settings
        bg_image = self.bg_image_input.text()
        if bg_image == "Nessuna":
            bg_image = ""

        return {
            "theme": theme,
            "library.background_color": self.current_bg_color,
            "library.background_image": bg_image
        }
