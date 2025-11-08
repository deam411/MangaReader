"""
Tab impostazioni aspetto: tema applicazione e sfondo home.
"""
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                              QGroupBox, QPushButton, QLineEdit, QFileDialog)
from PyQt5.QtCore import pyqtSignal
from ..settings import Settings


class AppearanceTab(QWidget):
    """Tab per impostazioni aspetto (tema + sfondo home)."""

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

        # Gruppo Sfondo Home
        background_group = QGroupBox("Sfondo Home (Libreria)")
        background_layout = QVBoxLayout()

        # Info
        home_info = QLabel(
            "Personalizza lo sfondo della schermata home (LibraryView)"
        )
        home_info.setWordWrap(True)
        home_info.setStyleSheet("color: gray; font-size: 10px; font-style: italic; padding: 5px;")
        background_layout.addWidget(home_info)

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

        # Info formati
        bg_info_label = QLabel("Formati supportati: PNG, JPG, JPEG, BMP, WebP")
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

    def _select_bg_image(self):
        """Apre il dialog per selezionare l'immagine di sfondo home."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona Immagine Sfondo Home",
            os.path.expanduser("~"),
            "Immagini (*.png *.jpg *.jpeg *.bmp *.webp)"
        )

        if file_path:
            self.bg_image_input.setText(file_path)

    def _clear_bg_image(self):
        """Rimuove l'immagine di sfondo home."""
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

        # Background image per home
        bg_image = self.bg_image_input.text()
        if bg_image == "Nessuna":
            bg_image = ""

        return {
            "theme": theme,
            "library.background_image": bg_image
        }
