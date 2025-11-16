"""
MangaView - Vista dettagli manga.

Gestisce:
- Visualizzazione dettagli manga (titolo, autore, descrizione, tags, cover)
- Lista volumi
- Navigazione verso VolumeView
- Edit/Delete manga
"""

import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
                              QListWidget, QListWidgetItem, QScrollArea, QFileDialog,
                              QMessageBox, QMenu, QDialog)
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt, QSize, QTimer

from src.paths import get_manga_dir
from src.database import MangaDatabaseManager
from src.logger import get_logger
from src.creator.manga_creator_app import MangaCreatorApp
from src.views.dialogs import BookmarkDialog, StatisticsDialog
from src.views.utils import sanitize_filename

logger = get_logger(__name__)

class MangaView(QWidget):
    def __init__(self, stacked_widget, plugin_manager=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.plugin_manager = plugin_manager  # Plugin manager per gestire plugin
        self.db_conn = None
        self.manga_file = None
        self.cover_data = None  # Per salvare i dati della cover
        self.initUI()

    def initUI(self):
        # Layout principale che conterrà solo la QScrollArea
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # QScrollArea per rendere tutto il contenuto scorrevole
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area)

        # Widget contenitore per tutti gli elementi dell'interfaccia
        container_widget = QWidget()
        self.scroll_area.setWidget(container_widget)
        
        layout = QVBoxLayout(container_widget)

        self.back_button = QPushButton('Back to Library', self)
        self.back_button.setToolTip('Torna alla libreria (Backspace)')
        self.back_button.clicked.connect(self.back_to_library)
        layout.addWidget(self.back_button)

        self.edit_manga_button = QPushButton('Edit Manga', self)
        self.edit_manga_button.setToolTip('Apri l\'editor per modificare questo manga')
        self.edit_manga_button.clicked.connect(self.launch_manga_editor)
        layout.addWidget(self.edit_manga_button)

        self.statistics_button = QPushButton(' View Statistics', self)
        self.statistics_button.setToolTip('Visualizza le tue statistiche di lettura per questo manga')
        self.statistics_button.clicked.connect(self.show_statistics)
        layout.addWidget(self.statistics_button)

        self.cover_label = QLabel(self)
        layout.addWidget(self.cover_label)

        self.download_cover_button = QPushButton('Download Cover', self)
        self.download_cover_button.clicked.connect(self.download_manga_cover)
        self.download_cover_button.setToolTip('Scarica la copertina del manga')
        self.download_cover_button.setMaximumWidth(200)
        layout.addWidget(self.download_cover_button)

        self.title_label = QLabel(self)
        layout.addWidget(self.title_label)

        self.author_label = QLabel(self)
        layout.addWidget(self.author_label)
        self.language_label = QLabel(self)
        layout.addWidget(self.language_label)
        self.year_label = QLabel(self)
        layout.addWidget(self.year_label)
        self.tags_label = QLabel(self)
        layout.addWidget(self.tags_label)

        self.description_label = QLabel(self)
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        # Aggiungi label per i volumi
        volumes_header = QLabel("<h3>Volumi</h3>")
        volumes_header.setToolTip('Trascina i volumi per riordinarli | Doppio click per aprire')
        layout.addWidget(volumes_header)
        self.volume_list = QListWidget(container_widget)
        self.volume_list.setDragDropMode(QListWidget.InternalMove)
        self.volume_list.model().rowsMoved.connect(self.reorder_volumes_on_drop, Qt.QueuedConnection)
        self.volume_list.itemDoubleClicked.connect(self.on_volume_selected)
        layout.addWidget(self.volume_list)

        # Aggiungi sezione segnalibri
        layout.addWidget(QLabel("<h3>Segnalibri</h3>"))
        self.bookmarks_list = QListWidget(self)
        self.bookmarks_list.setMaximumHeight(200)
        self.bookmarks_list.setToolTip('Doppio click per andare al segnalibro | Click destro per gestire')
        self.bookmarks_list.itemDoubleClicked.connect(self.on_bookmark_selected)
        self.bookmarks_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bookmarks_list.customContextMenuRequested.connect(self.show_bookmark_context_menu)
        layout.addWidget(self.bookmarks_list)

        self.setLayout(main_layout)

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

    def load_manga(self, file_name):
        self._cleanup_connection()

        self.manga_file = file_name
        try:
            self.db_conn = sqlite3.connect(file_name)
            self.db_conn.row_factory = sqlite3.Row
            cursor = self.db_conn.cursor()

            cursor.execute("SELECT * FROM metadata")
            metadata = cursor.fetchone()
            if metadata:
                self.title_label.setText(metadata['title'])
                self.author_label.setText(f"Author: {metadata['author']}" if metadata['author'] else "Author: N/A")

                self.language_label.setText(f"Language: {metadata['language']}" if metadata['language'] else "Language: N/A")
                self.year_label.setText(f"Year: {metadata['year']}" if metadata['year'] else "Year: N/A")
                self.tags_label.setText(f"Tags: {metadata['tags']}" if metadata['tags'] else "Tags: N/A")

                self.description_label.setText(metadata['description'])
                if metadata['cover']:
                    self.cover_data = metadata['cover']  # Salva i dati della cover
                    pixmap = QPixmap()
                    pixmap.loadFromData(metadata['cover'])
                    self.cover_label.setPixmap(pixmap.scaledToWidth(500)) # Increased size
                else:
                    self.cover_data = None

            self.volume_list.clear()
            cursor.execute("SELECT * FROM volumes ORDER BY `order`")
            volumes = cursor.fetchall()
            for volume in volumes:
                item = QListWidgetItem(volume['name'])
                item.setData(Qt.UserRole, volume['id'])
                self.volume_list.addItem(item)

            # Carica i segnalibri
            self.load_bookmarks()
        except Exception as e:
            logger.error(f"Error loading manga {file_name}: {e}")
            self._cleanup_connection()
            raise

    def load_bookmarks(self):
        """Carica i segnalibri del manga."""
        self.bookmarks_list.clear()

        if not self.manga_file:
            return

        db_manager = MangaDatabaseManager(self.manga_file)
        bookmarks = db_manager.get_bookmarks()

        if not bookmarks:
            no_bookmarks_item = QListWidgetItem("Nessun segnalibro")
            no_bookmarks_item.setFlags(Qt.NoItemFlags)  # Non selezionabile
            no_bookmarks_item.setForeground(QColor(128, 128, 128))  # Grigio
            self.bookmarks_list.addItem(no_bookmarks_item)
            return

        for bookmark in bookmarks:
            # Formato: "Nome - Volume X, Capitolo Y, Pagina Z"
            display_text = f" {bookmark['name']} - {bookmark['volume_name']}, {bookmark['chapter_name']}, Pag. {bookmark['page_number']}"
            item = QListWidgetItem(display_text)
            # Salva dati bookmark nell'item
            item.setData(Qt.UserRole, bookmark)
            self.bookmarks_list.addItem(item)

    def on_bookmark_selected(self, item):
        """Naviga al segnalibro selezionato."""
        bookmark = item.data(Qt.UserRole)
        if not bookmark:
            return

        # Apri il reader al capitolo e pagina del segnalibro
        self.stacked_widget.setCurrentIndex(3)  # ReaderView
        reader_view = self.stacked_widget.widget(3)
        reader_view.load_chapter(self.manga_file, bookmark['chapter_id'])

        # Scrolla alla pagina del segnalibro
        QTimer.singleShot(200, lambda: reader_view.scroll_to_page_index(bookmark['page_number'] - 1))

    def show_bookmark_context_menu(self, position):
        """Mostra menu contestuale per i segnalibri."""
        item = self.bookmarks_list.itemAt(position)
        if not item:
            return

        bookmark = item.data(Qt.UserRole)
        if not bookmark:
            return

        menu = QMenu(self)

        # Azione: Rinomina
        rename_action = menu.addAction("Rinomina")
        rename_action.triggered.connect(lambda: self.rename_bookmark(bookmark, item))

        # Azione: Elimina
        delete_action = menu.addAction("Elimina")
        delete_action.triggered.connect(lambda: self.delete_bookmark(bookmark))

        menu.exec_(self.bookmarks_list.viewport().mapToGlobal(position))

    def rename_bookmark(self, bookmark, item):
        """Rinomina un segnalibro."""
        dialog = BookmarkDialog(
            title="Rinomina Segnalibro",
            default_name=bookmark['name'],
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            new_name = dialog.get_name()
            if new_name and new_name != bookmark['name']:
                db_manager = MangaDatabaseManager(self.manga_file)
                if db_manager.update_bookmark_name(bookmark['id'], new_name):
                    # Aggiorna visualizzazione
                    self.load_bookmarks()
                    QMessageBox.information(
                        self,
                        "Successo",
                        f"Segnalibro rinominato in '{new_name}'"
                    )

    def delete_bookmark(self, bookmark):
        """Elimina un segnalibro."""
        reply = QMessageBox.question(
            self,
            "Conferma Eliminazione",
            f"Eliminare il segnalibro '{bookmark['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            db_manager = MangaDatabaseManager(self.manga_file)
            if db_manager.delete_bookmark(bookmark['id']):
                self.load_bookmarks()
                QMessageBox.information(self, "Successo", "Segnalibro eliminato")

    def on_volume_selected(self, item):
        """Naviga alla vista del volume per selezionare il capitolo."""
        volume_id = item.data(Qt.UserRole)
        self.stacked_widget.setCurrentIndex(2)  # VolumeView
        self.stacked_widget.widget(2).load_volume(self.manga_file, volume_id)

    def download_manga_cover(self):
        """Scarica la cover del manga sul disco."""
        if not self.cover_data:
            QMessageBox.warning(self, 'Nessuna Cover', 'Questo manga non ha una copertina da scaricare.')
            return

        # Ottieni il titolo del manga per il nome file
        title = self.title_label.text() if self.title_label.text() else "manga_cover"
        # Rimuovi caratteri non validi dal nome file
        safe_title = sanitize_filename(title)

        # Apri dialog per salvare il file
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva Copertina",
            f"{safe_title}_cover.png",
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

    def back_to_library(self):
        self.stacked_widget.setCurrentIndex(0)

    def keyPressEvent(self, event):
        """Torna alla libreria quando viene premuto il tasto Esc."""
        if event.key() == Qt.Key_Escape:
            self.back_to_library()
        else:
            super().keyPressEvent(event)

    def launch_manga_editor(self):
        if not self.manga_file:
            QMessageBox.warning(self, "No Manga Selected", "Please select a manga to edit.")
            return

        from src.creator.manga_creator_app import MangaCreatorApp
        self.editor_app = MangaCreatorApp(self.plugin_manager)
        self.editor_app.showFullScreen()
        self.editor_app.open_manga(self.manga_file) # Pass the current manga file to the editor

        # When the editor app closes, reload the current manga details
        self.editor_app.destroyed.connect(lambda: QTimer.singleShot(0, lambda: self.load_manga(self.manga_file)))

    def show_statistics(self):
        """Mostra il dialog con le statistiche di lettura per questo manga."""
        if not self.manga_file:
            QMessageBox.warning(self, "Nessun Manga Selezionato", "Seleziona un manga per vedere le statistiche.")
            return

        try:
            dialog = StatisticsDialog(self.manga_file, self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing statistics: {e}")
            QMessageBox.critical(self, "Errore", f"Impossibile caricare le statistiche:\n{str(e)}")

    def reorder_volumes(self):
        """Aggiorna l'ordine dei volumi nel database dopo drag-and-drop."""
        if not self.manga_file:
            logger.warning("reorder_volumes called but no manga_file")
            return

        try:
            # Estrai gli ID dei volumi nell'ordine attuale della lista
            all_items = [self.volume_list.item(i) for i in range(self.volume_list.count())]
            volume_ids = [item.data(Qt.UserRole) for item in all_items]

            logger.debug(f"Reordering volumes: {volume_ids}")

            # Aggiorna l'ordine nel database
            db_manager = MangaDatabaseManager(self.manga_file)
            if db_manager.update_volumes_order(volume_ids):
                logger.info(f"Volumes reordered successfully: {volume_ids}")
            else:
                logger.error("update_volumes_order returned False")
                QMessageBox.critical(self, "Errore", "Impossibile aggiornare l'ordine dei volumi nel database.")
        except Exception as e:
            logger.error(f"Error reordering volumes: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Errore", f"Errore durante il riordino dei volumi:\n{str(e)}")

    def reorder_volumes_on_drop(self, parent, start, end, destination, row):
        """Callback chiamato quando i volumi vengono riordinati tramite drag-and-drop."""
        self.reorder_volumes()

