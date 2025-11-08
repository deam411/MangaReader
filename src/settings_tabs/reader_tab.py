"""
Tab impostazioni reader: modalità lettura.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QComboBox, QGroupBox)
from ..settings import Settings


class ReaderTab(QWidget):
    """Tab per impostazioni reader (direzione lettura, ecc.)."""

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

        layout.addStretch()
        self.setLayout(layout)

    def get_values(self):
        """Ritorna i valori correnti del tab."""
        # Reading direction
        reading_direction = self.reading_direction_combo.currentData()

        return {
            "reader.reading_direction": reading_direction
        }
