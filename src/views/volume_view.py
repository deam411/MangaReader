"""
VolumeView - Vista selezione capitoli di un volume.

Gestisce:
- Visualizzazione cover volume grande
- Lista capitoli del volume
- Navigazione verso ReaderView
"""

import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
                              QListWidget, QListWidgetItem, QScrollArea, QFileDialog,
                              QMessageBox)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QSize

from src.database import MangaDatabaseManager
from src.logger import get_logger
from src.views.widgets import DeselectableListWidget
from src.views.utils import sanitize_filename

logger = get_logger(__name__)

class VolumeView(QWidget):
    """Vista per mostrare i capitoli di un volume con la sua cover."""
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.db_conn = None
        self.manga_file = None
        self.volume_id = None
        self.cover_data = None  # Per salvare i dati della cover del volume
        self.volume_name = ""  # Per il nome del file
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Pulsante per tornare ai dettagli del manga
        self.back_button = QPushButton('← Back to Manga Details', self)
        self.back_button.setToolTip('Torna ai dettagli del manga (Backspace)')
        self.back_button.clicked.connect(self.back_to_manga)
        layout.addWidget(self.back_button)

        # Layout orizzontale per cover e capitoli
        content_layout = QHBoxLayout()

        # Layout sinistro per la cover del volume
        left_layout = QVBoxLayout()
        left_layout.addStretch()  # Spazio sopra per centrare verticalmente

        self.volume_title = QLabel(self)
        self.volume_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.volume_title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.volume_title)

        self.cover_label = QLabel(self)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setMinimumWidth(500)
        left_layout.addWidget(self.cover_label)

        self.download_cover_button = QPushButton('Download Cover', self)
        self.download_cover_button.clicked.connect(self.download_volume_cover)
        self.download_cover_button.setToolTip('Scarica la copertina del volume')
        self.download_cover_button.setMaximumWidth(200)
        left_layout.addWidget(self.download_cover_button, alignment=Qt.AlignCenter)

        left_layout.addStretch()  # Spazio sotto per centrare verticalmente

        content_layout.addLayout(left_layout, 2)  # Aumentata proporzione da 1 a 2

        # Layout destro per la lista dei capitoli
        right_layout = QVBoxLayout()
        chapters_header = QLabel("<h2>Capitoli</h2>")
        right_layout.addWidget(chapters_header)

        self.chapter_list = QListWidget(self)
        self.chapter_list.setMinimumWidth(400)
        self.chapter_list.setToolTip('Doppio click su un capitolo per iniziare a leggere')
        self.chapter_list.itemDoubleClicked.connect(self.on_chapter_selected)
        right_layout.addWidget(self.chapter_list)

        content_layout.addLayout(right_layout, 2)

        layout.addLayout(content_layout)
        self.setLayout(layout)

    def _cleanup_connection(self):
        """Chiude in modo sicuro la connessione database."""
        if self.db_conn:
            try:
                self.db_conn.close()
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")
            finally:
                self.db_conn = None

    def closeEvent(self, event):
        """Chiudi la connessione database quando il widget viene distrutto."""
        self._cleanup_connection()
        super().closeEvent(event)

    def hideEvent(self, event):
        """Fix: Chiudi la connessione database quando la view viene nascosta."""
        self._cleanup_connection()
        super().hideEvent(event)

    def load_volume(self, manga_file, volume_id):
        """Carica i dati del volume e i suoi capitoli."""
        self._cleanup_connection()

        self.manga_file = manga_file
        self.volume_id = volume_id
        try:
            self.db_conn = sqlite3.connect(manga_file)
            self.db_conn.row_factory = sqlite3.Row
            cursor = self.db_conn.cursor()

            # Carica i dati del volume
            cursor.execute("SELECT * FROM volumes WHERE id = ?", (volume_id,))
            volume = cursor.fetchone()

            if volume:
                self.volume_name = volume['name']
                self.volume_title.setText(volume['name'])

                # Carica la cover del volume se presente
                if volume['cover']:
                    self.cover_data = volume['cover']  # Salva i dati della cover
                    pixmap = QPixmap()
                    pixmap.loadFromData(volume['cover'])
                    self.cover_label.setPixmap(pixmap.scaledToWidth(450, Qt.SmoothTransformation))
                else:
                    # Se non c'è cover del volume, prova a usare quella del manga
                    cursor.execute("SELECT cover FROM metadata")
                    metadata = cursor.fetchone()
                    if metadata and metadata['cover']:
                        self.cover_data = metadata['cover']  # Salva i dati della cover del manga
                        pixmap = QPixmap()
                        pixmap.loadFromData(metadata['cover'])
                        self.cover_label.setPixmap(pixmap.scaledToWidth(450, Qt.SmoothTransformation))
                    else:
                        self.cover_data = None
                        self.cover_label.setText("No cover available")
                        self.cover_label.setStyleSheet("font-size: 16px; color: gray;")

            # Carica i capitoli del volume
            cursor.execute("SELECT id, name FROM chapters WHERE volume_id = ? ORDER BY `order`", (volume_id,))
            chapters = cursor.fetchall()

            self.chapter_list.clear()
            for chapter in chapters:
                item = QListWidgetItem(chapter['name'])
                item.setData(Qt.UserRole, chapter['id'])
                self.chapter_list.addItem(item)
        except Exception as e:
            logger.error(f"Error loading volume {volume_id} from {manga_file}: {e}")
            self._cleanup_connection()
            raise

    def on_chapter_selected(self, item):
        """Apre il reader con il capitolo selezionato."""
        chapter_id = item.data(Qt.UserRole)
        self.stacked_widget.setCurrentIndex(3)  # ReaderView è ora all'index 3
        self.stacked_widget.widget(3).load_chapter(self.manga_file, chapter_id)

    def download_volume_cover(self):
        """Scarica la cover del volume sul disco."""
        if not self.cover_data:
            QMessageBox.warning(self, 'Nessuna Cover', 'Questo volume non ha una copertina da scaricare.')
            return

        # Usa il nome del volume per il nome file
        safe_name = sanitize_filename(self.volume_name)
        if not safe_name:
            safe_name = "volume_cover"

        # Apri dialog per salvare il file
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva Copertina Volume",
            f"{safe_name}_cover.png",
            "PNG Image (*.png);;JPEG Image (*.jpg);;All Files (*)"
        )

        if file_path:
            try:
                # Salva i dati della cover
                with open(file_path, 'wb') as f:
                    f.write(self.cover_data)
                QMessageBox.information(self, 'Successo', f'Copertina salvata in:\n{file_path}')
            except Exception as e:
                QMessageBox.critical(self, 'Errore', f'Errore durante il salvataggio della copertina:\n{str(e)}')

    def back_to_manga(self):
        """Torna alla vista dei dettagli del manga."""
        self.stacked_widget.setCurrentIndex(1)

    def keyPressEvent(self, event):
        """Torna alla vista manga quando viene premuto Esc o Backspace."""
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Backspace:
            self.back_to_manga()
        else:
            super().keyPressEvent(event)

