"""
Widget per visualizzare statistiche lettura nella LibraryView.
"""

from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
                              QPushButton, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from ..logger import get_logger
from .stats_manager import StatsManager

logger = get_logger(__name__)


class StatsWidget(QWidget):
    """
    Widget compatto per mostrare statistiche nella home.

    Mostra:
    - Totale manga nella libreria
    - Manga completati
    - Manga in corso
    - Ultimo manga letto
    """

    stats_clicked = pyqtSignal()  # Emesso quando si clicca per dettagli

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stats_manager = StatsManager()
        self._setup_ui()

    def _setup_ui(self):
        """Configura l'interfaccia del widget."""
        # Layout principale orizzontale
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(20)

        # Frame contenitore per bordo
        frame = QFrame(self)
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        frame_layout = QHBoxLayout(frame)
        frame_layout.setSpacing(30)

        # Stat 1: Totale manga
        self.total_label = self._create_stat_label("Totale Manga", "0")
        frame_layout.addWidget(self.total_label)

        # Separatore
        frame_layout.addWidget(self._create_separator())

        # Stat 2: Completati
        self.completed_label = self._create_stat_label("Completati", "0")
        frame_layout.addWidget(self.completed_label)

        # Separatore
        frame_layout.addWidget(self._create_separator())

        # Stat 3: In corso
        self.reading_label = self._create_stat_label("In Lettura", "0")
        frame_layout.addWidget(self.reading_label)

        # Separatore
        frame_layout.addWidget(self._create_separator())

        # Stat 4: Da leggere
        self.unread_label = self._create_stat_label("Da Leggere", "0")
        frame_layout.addWidget(self.unread_label)

        # Separatore
        frame_layout.addWidget(self._create_separator())

        # Pulsanti export
        export_container = QWidget()
        export_layout = QVBoxLayout(export_container)
        export_layout.setContentsMargins(0, 0, 0, 0)
        export_layout.setSpacing(5)

        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.setToolTip("Esporta statistiche in formato CSV")
        export_csv_btn.setMaximumWidth(100)
        export_csv_btn.clicked.connect(self.export_stats_csv)
        export_layout.addWidget(export_csv_btn)

        export_json_btn = QPushButton("Export JSON")
        export_json_btn.setToolTip("Esporta statistiche in formato JSON con summary")
        export_json_btn.setMaximumWidth(100)
        export_json_btn.clicked.connect(self.export_stats_json)
        export_layout.addWidget(export_json_btn)

        frame_layout.addWidget(export_container)

        frame_layout.addStretch()
        main_layout.addWidget(frame)

        self.setMaximumHeight(80)

    def _create_stat_label(self, title, value):
        """Crea un label per una statistica."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Valore (numero grande in alto)
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(16)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignCenter)

        # Titolo (nome sotto il numero, con margine superiore)
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(9)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setContentsMargins(0, 10, 0, 0)  # Spazio superiore di 10px

        layout.addWidget(value_label)
        layout.addWidget(title_label)

        # Salva riferimento al value label per aggiornamenti
        container.value_label = value_label

        return container

    def _create_separator(self):
        """Crea un separatore verticale."""
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        return separator

    def update_stats(self, total, completed, reading, unread):
        """
        Aggiorna le statistiche visualizzate.

        Args:
            total: Numero totale manga
            completed: Numero manga completati
            reading: Numero manga in lettura
            unread: Numero manga da leggere
        """
        self.total_label.value_label.setText(str(total))
        self.completed_label.value_label.setText(str(completed))
        self.reading_label.value_label.setText(str(reading))
        self.unread_label.value_label.setText(str(unread))

        logger.debug(f"Stats aggiornate: {total} totali, {completed} completati, {reading} in lettura")

    def export_stats_csv(self):
        """Esporta le statistiche di lettura in formato CSV."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Esporta Statistiche CSV",
            "reading_stats.csv",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            if self.stats_manager.export_to_csv(file_path, include_all=True):
                QMessageBox.information(
                    self,
                    "Export Completato",
                    f"Statistiche esportate con successo in:\n{file_path}"
                )
                logger.info(f"Statistiche esportate in CSV: {file_path}")
            else:
                QMessageBox.warning(
                    self,
                    "Errore Export",
                    "Impossibile esportare le statistiche. Controlla i log per dettagli."
                )

    def export_stats_json(self):
        """Esporta le statistiche di lettura in formato JSON."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Esporta Statistiche JSON",
            "reading_stats.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            if self.stats_manager.export_to_json(file_path, include_summary=True):
                QMessageBox.information(
                    self,
                    "Export Completato",
                    f"Statistiche esportate con successo in:\n{file_path}"
                )
                logger.info(f"Statistiche esportate in JSON: {file_path}")
            else:
                QMessageBox.warning(
                    self,
                    "Errore Export",
                    "Impossibile esportare le statistiche. Controlla i log per dettagli."
                )
