"""
Tab impostazioni reader: modalità lettura e sfondo.
"""
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QComboBox, QGroupBox, QPushButton, QLineEdit,
                              QFileDialog, QColorDialog)
from PyQt5.QtGui import QColor
from ..settings import Settings


class ReaderTab(QWidget):
    """Tab per impostazioni reader (direzione lettura + sfondo)."""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.parent_dialog = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Gruppo Modalità Lettura
        reading_group = QGroupBox("Modalità di Lettura")
        reading_layout = QVBoxLayout()

        # Direzione lettura
        direction_layout = QHBoxLayout()
        direction_label = QLabel("Direzione lettura:")
        direction_layout.addWidget(direction_label)

        self.reading_direction_combo = QComboBox()
        self.reading_direction_combo.addItem("Left to Right (LTR)", "ltr")
        self.reading_direction_combo.addItem("Right to Left (RTL)", "rtl")

        # Imposta valore corrente
        current_direction = self.settings.get("reader.reading_direction", "ltr")
        index = self.reading_direction_combo.findData(current_direction)
        if index >= 0:
            self.reading_direction_combo.setCurrentIndex(index)

        direction_layout.addWidget(self.reading_direction_combo)
        direction_layout.addStretch()
        reading_layout.addLayout(direction_layout)

        # Info
        info_label = QLabel("RTL è utilizzato tipicamente per manga giapponesi")
        info_label.setStyleSheet("color: gray; font-size: 10px; font-style: italic;")
        reading_layout.addWidget(info_label)

        reading_group.setLayout(reading_layout)
        layout.addWidget(reading_group)

        # Gruppo Personalizzazione Sfondo READER
        background_group = QGroupBox("Sfondo Reader")
        background_layout = QVBoxLayout()

        # Info importante
        reader_info = QLabel(
            "Personalizza lo sfondo del lettore manga (area di lettura pagine)"
        )
        reader_info.setWordWrap(True)
        reader_info.setStyleSheet("color: gray; font-size: 10px; font-style: italic; padding: 5px;")
        background_layout.addWidget(reader_info)

        # Colore sfondo
        color_layout = QHBoxLayout()
        color_label = QLabel("Colore sfondo:")
        color_layout.addWidget(color_label)

        self.bg_color_button = QPushButton("Seleziona Colore")
        self.current_bg_color = self.settings.get("reader.background_color", "#2b2b2b")
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
        current_bg_image = self.settings.get("reader.background_image", "")
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

    def _select_bg_color(self):
        """Apre il dialog per selezionare il colore di sfondo."""
        color = QColorDialog.getColor(
            QColor(self.current_bg_color),
            self,
            "Seleziona Colore Sfondo Reader"
        )

        if color.isValid():
            self.current_bg_color = color.name()
            self.bg_color_button.setStyleSheet(f"background-color: {self.current_bg_color}; color: white;")
            self.bg_color_label.setText(self.current_bg_color)

    def _select_bg_image(self):
        """Apre il dialog per selezionare l'immagine di sfondo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona Immagine Sfondo Reader",
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
        # Reading direction
        reading_direction = self.reading_direction_combo.currentData()

        # Background settings
        bg_image = self.bg_image_input.text()
        if bg_image == "Nessuna":
            bg_image = ""

        return {
            "reader.reading_direction": reading_direction,
            "reader.background_color": self.current_bg_color,
            "reader.background_image": bg_image
        }
