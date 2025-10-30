import sys
import os
import importlib

# Remove sys.path manipulation here, as it will be handled in main.py
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QInputDialog, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage, QIcon

# Importa il gestore del database che abbiamo creato
from .. import database # New relative import
from ..database import MangaDatabaseManager # New relative import
from ..paths import get_manga_dir # Import centralized path manager

class MangaCreatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_manga_db = None # Percorso al file .manga attualmente aperto
        self.db_manager = None # Istanza del gestore del database
        self.current_volume_id = None # ID del volume attualmente selezionato
        self.current_chapter_id = None # ID del capitolo attualmente selezionato
        self.current_cover_data = None # Dati della copertina principale corrente
        self.is_dirty = False # Flag per indicare se ci sono modifiche non salvate

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Manga Creator')
        self.setGeometry(100, 100, 1600, 900) # Aumento la dimensione della finestra

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout() # Usiamo QHBoxLayout per dividere l'UI in colonne
        self.central_widget.setLayout(self.main_layout)

        # Colonna di sinistra: Metadati e Volumi
        left_column_widget = QWidget()
        left_column_layout = QVBoxLayout()
        left_column_widget.setLayout(left_column_layout)
        self.main_layout.addWidget(left_column_widget, 1) # Proporzione 1

        # Area metadati
        self.metadata_group = QWidget()
        self.metadata_layout = QVBoxLayout()
        self.metadata_group.setLayout(self.metadata_layout)
        left_column_layout.addWidget(self.metadata_group)

        self.metadata_layout.addWidget(QLabel('<h2>Metadati Manga</h2>'))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText('Titolo Manga')
        self.metadata_layout.addWidget(QLabel('Titolo:'))
        self.metadata_layout.addWidget(self.title_input)
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText('Autore Manga')
        self.metadata_layout.addWidget(QLabel('Autore:'))
        self.metadata_layout.addWidget(self.author_input)
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText('Descrizione del Manga')
        self.metadata_layout.addWidget(QLabel('Descrizione:'))
        self.metadata_layout.addWidget(self.description_input)

        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText('Lingua')
        self.metadata_layout.addWidget(QLabel('Lingua:'))
        self.metadata_layout.addWidget(self.language_input)

        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText('Anno')
        self.metadata_layout.addWidget(QLabel('Anno:'))
        self.metadata_layout.addWidget(self.year_input)

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText('Tag (separati da virgola)')
        self.metadata_layout.addWidget(QLabel('Tag:'))
        self.metadata_layout.addWidget(self.tags_input)
        self.metadata_layout.addStretch()

        self.set_main_cover_btn = QPushButton('Imposta Copertina Principale')
        self.set_main_cover_btn.clicked.connect(self.set_main_cover)
        self.metadata_layout.addWidget(self.set_main_cover_btn)

        self.main_cover_preview = QLabel('Nessuna copertina principale')
        self.main_cover_preview.setAlignment(Qt.AlignCenter)
        self.main_cover_preview.setFixedSize(150, 200) # Dimensione fissa per l'anteprima
        self.metadata_layout.addWidget(self.main_cover_preview)

        # Area Volumi
        self.volume_group = QWidget()
        self.volume_layout = QVBoxLayout()
        self.volume_group.setLayout(self.volume_layout)
        left_column_layout.addWidget(self.volume_group)

        self.volume_layout.addWidget(QLabel('<h2>Volumi</h2>'))
        self.volume_list = QListWidget()
        self.volume_layout.addWidget(self.volume_list)
        self.volume_list.currentRowChanged.connect(self.volume_selection_changed)

        volume_buttons_layout = QHBoxLayout()
        self.add_volume_btn = QPushButton('Aggiungi Volume')
        self.add_volume_btn.clicked.connect(self.add_volume)
        self.remove_volume_btn = QPushButton('Rimuovi Volume')
        self.remove_volume_btn.clicked.connect(self.remove_volume)
        self.rename_volume_btn = QPushButton('Rinomina Volume')
        self.rename_volume_btn.clicked.connect(self.rename_volume)
        self.set_volume_cover_btn = QPushButton('Imposta Copertina Volume')
        self.set_volume_cover_btn.clicked.connect(self.set_volume_cover)
        volume_buttons_layout.addWidget(self.add_volume_btn)
        volume_buttons_layout.addWidget(self.remove_volume_btn)
        volume_buttons_layout.addWidget(self.rename_volume_btn)
        volume_buttons_layout.addWidget(self.set_volume_cover_btn)
        self.volume_layout.addLayout(volume_buttons_layout)

        # Colonna centrale: Capitoli
        middle_column_widget = QWidget()
        middle_column_layout = QVBoxLayout()
        middle_column_widget.setLayout(middle_column_layout)
        self.main_layout.addWidget(middle_column_widget, 1) # Proporzione 1

        # Area Capitoli
        self.chapter_group = QWidget()
        self.chapter_layout = QVBoxLayout()
        self.chapter_group.setLayout(self.chapter_layout)
        middle_column_layout.addWidget(self.chapter_group)

        self.chapter_layout.addWidget(QLabel('<h2>Capitoli</h2>'))
        self.chapter_list = QListWidget()
        self.chapter_list.setDragDropMode(QListWidget.InternalMove)
        self.chapter_list.model().rowsMoved.connect(self.reorder_chapters_on_drop, Qt.QueuedConnection)
        self.chapter_layout.addWidget(self.chapter_list)
        self.chapter_list.currentRowChanged.connect(self.chapter_selection_changed)

        chapter_buttons_layout = QHBoxLayout()
        self.add_chapter_btn = QPushButton('Aggiungi Capitolo')
        self.add_chapter_btn.clicked.connect(self.add_chapter)
        self.remove_chapter_btn = QPushButton('Rimuovi Capitolo')
        self.remove_chapter_btn.clicked.connect(self.remove_chapter)
        self.rename_chapter_btn = QPushButton('Rinomina Capitolo')
        self.rename_chapter_btn.clicked.connect(self.rename_chapter)
        chapter_buttons_layout.addWidget(self.add_chapter_btn)
        chapter_buttons_layout.addWidget(self.remove_chapter_btn)
        chapter_buttons_layout.addWidget(self.rename_chapter_btn)
        self.chapter_layout.addLayout(chapter_buttons_layout)

        # Colonna di destra: Pagine e Anteprima
        right_column_widget = QWidget()
        right_column_layout = QVBoxLayout()
        right_column_widget.setLayout(right_column_layout)
        self.main_layout.addWidget(right_column_widget, 2) # Proporzione 2

        # Area Pagine
        self.page_group = QWidget()
        self.page_layout = QVBoxLayout()
        self.page_group.setLayout(self.page_layout)
        right_column_layout.addWidget(self.page_group)

        self.page_layout.addWidget(QLabel('<h2>Pagine del Capitolo Selezionato</h2>'))
        self.page_list = QListWidget()
        self.page_list.setViewMode(QListWidget.IconMode)
        self.page_list.setIconSize(QSize(120, 120))
        self.page_list.setResizeMode(QListWidget.Adjust)
        self.page_list.setDragDropMode(QListWidget.InternalMove)
        self.page_list.model().rowsMoved.connect(self.reorder_pages_on_drop, Qt.QueuedConnection)
        self.page_list.currentRowChanged.connect(self.page_selection_changed)
        self.page_layout.addWidget(self.page_list)

        page_buttons_layout = QHBoxLayout()
        self.add_page_btn = QPushButton('Aggiungi Pagina...')
        self.add_page_btn.clicked.connect(self.add_page)
        self.remove_page_btn = QPushButton('Rimuovi Pagina')
        self.remove_page_btn.clicked.connect(self.remove_page)
        self.move_page_up_btn = QPushButton('Sposta Su')
        self.move_page_down_btn = QPushButton('Sposta Giù')
        self.move_page_up_btn.clicked.connect(self.move_page_up)
        self.move_page_down_btn.clicked.connect(self.move_page_down)
        page_buttons_layout.addWidget(self.add_page_btn)
        page_buttons_layout.addWidget(self.remove_page_btn)
        page_buttons_layout.addWidget(self.move_page_up_btn)
        page_buttons_layout.addWidget(self.move_page_down_btn)
        self.page_layout.addLayout(page_buttons_layout)

        # Area Anteprima Immagine
        self.image_preview_group = QWidget()
        self.image_preview_layout = QVBoxLayout()
        self.image_preview_group.setLayout(self.image_preview_layout)
        right_column_layout.addWidget(self.image_preview_group)

        self.image_preview_layout.addWidget(QLabel('<h2>Anteprima</h2>'))
        self.image_scene = QGraphicsScene()
        self.image_view = QGraphicsView(self.image_scene)
        self.image_preview_layout.addWidget(self.image_view)

        # Menu Bar
        self.create_menu_bar()

        self.update_ui_state(False) # Inizia con l'UI disabilitata

    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')

        new_action = file_menu.addAction('Nuovo Manga...')
        new_action.triggered.connect(self.new_manga)

        open_action = file_menu.addAction('Apri Manga...')
        open_action.triggered.connect(self.open_manga)

        save_action = file_menu.addAction('Salva Manga')
        save_action.triggered.connect(self.save_manga)
        save_action.setShortcut('Ctrl+S')

        file_menu.addSeparator()

        exit_action = file_menu.addAction('Esci')
        exit_action.triggered.connect(self.close)

    def new_manga(self):
        # Use centralized path management
        default_dir = get_manga_dir()

        file_path, _ = QFileDialog.getSaveFileName(self, "Crea Nuovo File .manga", default_dir, "Manga Files (*.manga)")
        if file_path:
            if 'src.database' in sys.modules:
                importlib.reload(sys.modules['src.database'])
            from src import database
            from src.database import MangaDatabaseManager
            self.db_manager = MangaDatabaseManager(self.current_manga_db)
            if self.db_manager.create_manga_db_schema():
                QMessageBox.information(self, "Successo", f"Nuovo file .manga creato: {file_path}")
                self.update_ui_state(True)
                self.clear_metadata_fields()
                self.load_volumes()
                self.set_dirty(True)
            else:
                QMessageBox.critical(self, "Errore", "Impossibile creare lo schema del database.")
                self.current_manga_db = None
                self.db_manager = None
                self.update_ui_state(False)

    def open_manga(self, file_path=None): # Add file_path parameter
        if file_path is None: # If no file_path is provided, open file dialog
            file_path, _ = QFileDialog.getOpenFileName(self, "Apri File .manga", "", "Manga Files (*.manga)")
        
        if file_path:
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "File Non Trovato", "Il file specificato non esiste.")
                return

            self.current_manga_db = file_path
            # ... (rest of the code remains the same) ...
            if 'src.database' in sys.modules:
                importlib.reload(sys.modules['src.database'])
            from src import database
            from src.database import MangaDatabaseManager
            self.db_manager = MangaDatabaseManager(self.current_manga_db)
            if not hasattr(self.db_manager, 'get_metadata'):
                QMessageBox.critical(self, "Errore", "Il database manager non ha il metodo 'get_metadata'. Controllare la versione del file database.py.")
                self.db_manager = None
                self.update_ui_state(False)
                return
            QMessageBox.information(self, "Successo", f"File .manga aperto: {file_path}")
            self.update_ui_state(True)
            self.load_metadata()
            self.load_volumes()

    def save_manga(self):
        if not self.db_manager:
            QMessageBox.warning(self, "Nessun File Aperto", "Nessun file .manga è attualmente aperto per il salvataggio.")
            return

        title = self.title_input.text()
        author = self.author_input.text()
        description = self.description_input.toPlainText()
        language = self.language_input.text()
        year_text = self.year_input.text()
        tags = self.tags_input.text()

        year = None
        if year_text:
            try:
                year = int(year_text)
            except ValueError:
                QMessageBox.warning(self, "Anno non valido", "L'anno deve essere un numero intero.")
                return

        existing_metadata = self.db_manager.get_metadata()

        if existing_metadata:
            if self.db_manager.update_metadata(title, author, description, language, self.current_cover_data, year, tags):
                QMessageBox.information(self, "Salvataggio", "Metadati aggiornati con successo.")
                self.set_dirty(False)
            else:
                QMessageBox.critical(self, "Errore", "Errore durante l'aggiornamento dei metadati.")
        else:
            if self.db_manager.insert_metadata(title, author, description, language, self.current_cover_data, year, tags):
                QMessageBox.information(self, "Salvataggio", "Metadati inseriti con successo.")
                self.set_dirty(False)
            else:
                QMessageBox.critical(self, "Errore", "Errore durante l'inserimento dei metadati.")

    def load_metadata(self):
        if self.db_manager:
            metadata = self.db_manager.get_metadata()
            if metadata:
                self.title_input.setText(metadata['title'] if metadata['title'] else '')
                self.author_input.setText(metadata['author'] if metadata['author'] else '')
                self.description_input.setText(metadata['description'] if metadata['description'] else '')
                self.language_input.setText(metadata['language'] if metadata['language'] else '')
                self.year_input.setText(str(metadata['year']) if metadata['year'] else '')
                self.tags_input.setText(metadata['tags'] if metadata['tags'] else '')
                if metadata['cover']:
                    self.current_cover_data = metadata['cover']
                    pixmap = QPixmap()
                    pixmap.loadFromData(self.current_cover_data)
                    self.main_cover_preview.setPixmap(pixmap.scaled(self.main_cover_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    self.current_cover_data = None
                    self.main_cover_preview.setText('Nessuna copertina principale')
            else:
                self.clear_metadata_fields()
        else:
            self.clear_metadata_fields()

    def clear_metadata_fields(self):
        self.title_input.clear()
        self.author_input.clear()
        self.description_input.clear()
        self.language_input.clear()
        self.year_input.clear()
        self.tags_input.clear()

    def update_ui_state(self, enabled):
        self.metadata_group.setEnabled(enabled)
        self.volume_group.setEnabled(enabled)
        self.chapter_group.setEnabled(enabled)
        self.page_group.setEnabled(enabled)

    def set_dirty(self, dirty):
        self.is_dirty = dirty
        # Potresti voler aggiornare il titolo della finestra per indicare le modifiche non salvate
        # es. self.setWindowTitle('Manga Creator' + ('*' if dirty else ''))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.is_dirty:
            reply = QMessageBox.question(self, 'Salva Modifiche',
                                         "Ci sono modifiche non salvate. Vuoi salvarle prima di uscire?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if reply == QMessageBox.Save:
                self.save_manga()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    # --- Metodi per la gestione Volumi ---
    def load_volumes(self):
        self.volume_list.clear()
        self.chapter_list.clear()
        self.page_list.clear()
        self.image_scene.clear()
        if self.db_manager:
            volumes = self.db_manager.get_volumes()
            for volume in volumes:
                item = QListWidgetItem(volume['name'])
                item.setData(Qt.UserRole, volume['id']) # Memorizza l'ID del volume nell'elemento
                if volume['cover']:
                    pixmap = QPixmap()
                    pixmap.loadFromData(volume['cover'])
                    # Scala l'immagine per adattarla all'icona della lista
                    scaled_pixmap = pixmap.scaled(QSize(60, 80), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    item.setIcon(QIcon(scaled_pixmap))
                self.volume_list.addItem(item)
        self.current_volume_id = None

    def add_volume(self):
        if not self.db_manager:
            QMessageBox.warning(self, "Errore", "Nessun file .manga aperto.")
            return

        volume_name, ok = QInputDialog.getText(self, 'Nuovo Volume', 'Inserisci il nome del volume:')
        if ok and volume_name:
            current_volumes = self.db_manager.get_volumes()
            if current_volumes:
                new_order = max([v['order'] for v in current_volumes]) + 1
            else:
                new_order = 1

            volume_id = self.db_manager.insert_volume(volume_name, new_order)
            if volume_id:
                self.load_volumes()
                QMessageBox.information(self, "Successo", f"Volume '{volume_name}' aggiunto.")
                self.set_dirty(True)
            else:
                QMessageBox.critical(self, "Errore", "Impossibile aggiungere il volume.")

    def remove_volume(self):
        if not self.db_manager:
            QMessageBox.warning(self, "Errore", "Nessun file .manga aperto.")
            return

        selected_item = self.volume_list.currentItem()
        if selected_item:
            volume_id = selected_item.data(Qt.UserRole)
            volume_name = selected_item.text()
            reply = QMessageBox.question(self, 'Conferma Rimozione',
                                         f"Sei sicuro di voler rimuovere il volume '{volume_name}' e tutti i suoi capitoli e pagine?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                if self.db_manager.delete_volume(volume_id):
                    QMessageBox.information(self, "Successo", f"Volume '{volume_name}' rimosso.")
                    self.load_volumes()
                    self.set_dirty(True)
                else:
                    QMessageBox.critical(self, "Errore", f"Impossibile rimuovere il volume '{volume_name}'.")
        else:
            QMessageBox.warning(self, "Selezione", "Seleziona un volume da rimuovere.")

    def rename_volume(self):
        if not self.db_manager:
            QMessageBox.warning(self, "Errore", "Nessun file .manga aperto.")
            return

        selected_item = self.volume_list.currentItem()
        if selected_item:
            volume_id = selected_item.data(Qt.UserRole)
            old_name = selected_item.text()
            new_name, ok = QInputDialog.getText(self, 'Rinomina Volume', 'Inserisci il nuovo nome per il volume:', QLineEdit.Normal, old_name)
            if ok and new_name:
                # Recupera l'ordine corrente del volume
                current_volumes = self.db_manager.get_volumes()
                current_order = None
                for v in current_volumes:
                    if v['id'] == volume_id:
                        current_order = v['order']
                        break

                if current_order is not None and self.db_manager.update_volume(volume_id, new_name, current_order, None): # Cover non ancora gestita
                    QMessageBox.information(self, "Successo", f"Volume rinominato in '{new_name}'.")
                    selected_item.setText(new_name) # Aggiorna subito la UI
                    self.set_dirty(True)
                else:
                    QMessageBox.critical(self, "Errore", "Impossibile rinominare il volume.")
        else:
            QMessageBox.warning(self, "Selezione", "Seleziona un volume da rinominare.")

    def set_volume_cover(self):
        if not self.db_manager:
            QMessageBox.warning(self, "Errore", "Nessun file .manga aperto.")
            return

        selected_item = self.volume_list.currentItem()
        if selected_item:
            volume_id = selected_item.data(Qt.UserRole)
            file_path, _ = QFileDialog.getOpenFileName(self, "Seleziona Copertina Volume", "", "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)")
            if file_path:
                try:
                    with open(file_path, 'rb') as f:
                        cover_data = f.read()
                    
                    # Recupera nome e ordine corrente del volume
                    current_volumes = self.db_manager.get_volumes()
                    current_name = None
                    current_order = None
                    for v in current_volumes:
                        if v['id'] == volume_id:
                            current_name = v['name']
                            current_order = v['order']
                            break

                    if current_name and current_order is not None and self.db_manager.update_volume(volume_id, current_name, current_order, cover_data):
                        QMessageBox.information(self, "Successo", "Copertina volume aggiornata.")
                        self.load_volumes() # Ricarica per aggiornare l'icona se necessario
                        self.set_dirty(True)
                    else:
                        QMessageBox.critical(self, "Errore", "Impossibile aggiornare la copertina del volume nel database.")
                except Exception as e:
                    QMessageBox.critical(self, "Errore", f"Errore durante la lettura del file di copertina: {e}")
        else:
            QMessageBox.warning(self, "Selezione", "Seleziona un volume per impostare la copertina.")

    def volume_selection_changed(self, current_row):
        if current_row >= 0:
            selected_item = self.volume_list.item(current_row)
            self.current_volume_id = selected_item.data(Qt.UserRole)
            self.load_chapters(self.current_volume_id)
        else:
            self.current_volume_id = None
            self.chapter_list.clear()
            self.page_list.clear()
            self.image_scene.clear()

    def set_main_cover(self):
        if not self.db_manager:
            QMessageBox.warning(self, "Errore", "Nessun file .manga aperto.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Seleziona Copertina Principale", "", "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)")
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    cover_data = f.read()
                
                # Recupera i metadati esistenti per aggiornare solo la copertina
                metadata = self.db_manager.get_metadata()
                if metadata:
                    if self.db_manager.update_metadata(
                        metadata['title'], metadata['author'], metadata['description'],
                        metadata['language'], cover_data, metadata['year'], metadata['tags']
                    ):
                        QMessageBox.information(self, "Successo", "Copertina principale aggiornata.")
                        self.current_cover_data = cover_data # Aggiorna la variabile di istanza
                        # Aggiorna l'anteprima
                        pixmap = QPixmap()
                        pixmap.loadFromData(self.current_cover_data)
                        self.main_cover_preview.setPixmap(pixmap.scaled(self.main_cover_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        self.set_dirty(True)
                    else:
                        QMessageBox.critical(self, "Errore", "Impossibile aggiornare la copertina principale.")
                else:
                    QMessageBox.critical(self, "Errore", "Nessun metadato trovato per aggiornare la copertina.")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante la lettura del file di copertina: {e}")

    # --- Metodi per la gestione Capitoli ---
    def load_chapters(self, volume_id):
        self.chapter_list.clear()
        self.page_list.clear()
        self.image_scene.clear()
        if self.db_manager and volume_id is not None:
            chapters = self.db_manager.get_chapters_for_volume(volume_id)
            for chapter in chapters:
                item = QListWidgetItem(chapter['name'])
                item.setData(Qt.UserRole, chapter['id']) # Memorizza l'ID del capitolo nell'elemento
                self.chapter_list.addItem(item)
        self.current_chapter_id = None

    def add_chapter(self):
        if not self.db_manager or self.current_volume_id is None:
            QMessageBox.warning(self, "Errore", "Seleziona prima un volume per aggiungere capitoli.")
            return

        chapter_name, ok = QInputDialog.getText(self, 'Nuovo Capitolo', 'Inserisci il nome del capitolo:')
        if ok and chapter_name:
            # Determinare l'ordine del nuovo capitolo all'interno del volume corrente
            current_chapters = self.db_manager.get_chapters_for_volume(self.current_volume_id)
            if current_chapters:
                new_order = max([c['order'] for c in current_chapters]) + 1
            else:
                new_order = 1

            chapter_id = self.db_manager.insert_chapter(chapter_name, new_order, self.current_volume_id)
            if chapter_id:
                self.load_chapters(self.current_volume_id)
                QMessageBox.information(self, "Successo", f"Capitolo '{chapter_name}' aggiunto al volume ID {self.current_volume_id}.")
                self.set_dirty(True)
            else:
                QMessageBox.critical(self, "Errore", "Impossibile aggiungere il capitolo.")

    def remove_chapter(self):
        if not self.db_manager:
            QMessageBox.warning(self, "Errore", "Nessun file .manga aperto.")
            return

        selected_item = self.chapter_list.currentItem()
        if selected_item:
            chapter_id = selected_item.data(Qt.UserRole)
            chapter_name = selected_item.text()
            reply = QMessageBox.question(self, 'Conferma Rimozione',
                                         f"Sei sicuro di voler rimuovere il capitolo '{chapter_name}' e tutte le sue pagine?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                if self.db_manager.delete_chapter_and_pages(chapter_id):
                    QMessageBox.information(self, "Successo", f"Capitolo '{chapter_name}' rimosso.")
                    self.load_chapters(self.current_volume_id) # Ricarica per aggiornare la lista
                    self.reorder_chapters()
                    self.set_dirty(True)
                else:
                    QMessageBox.critical(self, "Errore", f"Impossibile rimuovere il capitolo '{chapter_name}'.")
        else:
            QMessageBox.warning(self, "Selezione", "Seleziona un capitolo da rimuovere.")

    def rename_chapter(self):
        if not self.db_manager:
            QMessageBox.warning(self, "Errore", "Nessun file .manga aperto.")
            return

        selected_item = self.chapter_list.currentItem()
        if selected_item:
            chapter_id = selected_item.data(Qt.UserRole)
            old_name = selected_item.text()
            new_name, ok = QInputDialog.getText(self, 'Rinomina Capitolo', 'Inserisci il nuovo nome per il capitolo:', QLineEdit.Normal, old_name)
            if ok and new_name:
                if self.db_manager.update_chapter_name(chapter_id, new_name):
                    QMessageBox.information(self, "Successo", f"Capitolo rinominato in '{new_name}'.")
                    selected_item.setText(new_name) # Aggiorna subito la UI
                    self.set_dirty(True)
                else:
                    QMessageBox.critical(self, "Errore", "Impossibile rinominare il capitolo.")
        else:
            QMessageBox.warning(self, "Selezione", "Seleziona un capitolo da rinominare.")

    def reorder_chapters(self):
        if not self.db_manager:
            return
        all_items = [self.chapter_list.item(i) for i in range(self.chapter_list.count())]
        chapter_ids = [item.data(Qt.UserRole) for item in all_items]
        if not self.db_manager.update_chapters_order(chapter_ids):
            QMessageBox.critical(self, "Errore", "Impossibile aggiornare l'ordine dei capitoli nel database.")
        else:
            self.set_dirty(True)

    def reorder_chapters_on_drop(self, parent, start, end, destination, row):
        self.reorder_chapters()

    def chapter_selection_changed(self, current_row):
        if current_row >= 0:
            selected_item = self.chapter_list.item(current_row)
            self.current_chapter_id = selected_item.data(Qt.UserRole)
            self.load_pages(self.current_chapter_id)
        else:
            self.current_chapter_id = None
            self.page_list.clear()
            self.image_scene.clear()

    # --- Metodi per la gestione Pagine ---
    def load_pages(self, chapter_id):
        self.page_list.clear()
        self.image_scene.clear()
        if self.db_manager and chapter_id is not None:
            pages = self.db_manager.get_pages_for_chapter(chapter_id)
            for page in pages:
                print(f"DEBUG: Page {page['page_number']} image_data length: {len(page['image_data'])} bytes") # DEBUG PRINT
                pixmap = QPixmap()
                pixmap.loadFromData(page['image_data'])
                pixmap = pixmap.scaled(QSize(100,100), Qt.KeepAspectRatio, Qt.SmoothTransformation) # Scala per l'icona
                item = QListWidgetItem(QIcon(pixmap), f"Pagina {page['page_number']}")
                item.setData(Qt.UserRole, page['page_number']) # Memorizza il numero della pagina
                item.setData(Qt.UserRole + 1, page['image_data']) # Memorizza i dati completi dell'immagine
                self.page_list.addItem(item)

    def add_page(self):
        if not self.db_manager or self.current_chapter_id is None:
            QMessageBox.warning(self, "Errore", "Seleziona prima un capitolo per aggiungere pagine.")
            return

        file_paths, _ = QFileDialog.getOpenFileNames(self, "Aggiungi Pagine", "", "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)")
        if file_paths:
            current_pages = self.db_manager.get_pages_for_chapter(self.current_chapter_id)
            if current_pages:
                next_page_number = max([p['page_number'] for p in current_pages]) + 1
            else:
                next_page_number = 1

            for file_path in file_paths:
                print(f"DEBUG: Methods available on db_manager: {dir(self.db_manager)}") # DEBUG PRINT
                if self.db_manager.insert_page(self.current_chapter_id, next_page_number, file_path):
                    QMessageBox.information(self, "Successo", f"Pagina '{os.path.basename(file_path)}' aggiunta al capitolo ID {self.current_chapter_id}.")
                    next_page_number += 1
                    self.set_dirty(True)
                else:
                    QMessageBox.critical(self, "Errore", f"Impossibile aggiungere la pagina '{os.path.basename(file_path)}'.")
            self.load_pages(self.current_chapter_id) # Ricarica le pagine dopo l'aggiunta

    def remove_page(self):
        if not self.db_manager or self.current_chapter_id is None:
            QMessageBox.warning(self, "Errore", "Nessun capitolo selezionato.")
            return

        selected_item = self.page_list.currentItem()
        if selected_item:
            page_number = selected_item.data(Qt.UserRole)
            reply = QMessageBox.question(self, 'Conferma Rimozione',
                                         f"Sei sicuro di voler rimuovere la pagina {page_number}?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                if self.db_manager.delete_page(self.current_chapter_id, page_number):
                    QMessageBox.information(self, "Successo", f"Pagina {page_number} rimossa.")
                    self.load_pages(self.current_chapter_id) # Ricarica per aggiornare la lista
                    self.reorder_pages_after_delete(self.current_chapter_id)
                    self.set_dirty(True)
                else:
                    QMessageBox.critical(self, "Errore", f"Impossibile rimuovere la pagina {page_number}.")
        else:
            QMessageBox.warning(self, "Selezione", "Seleziona una pagina da rimuovere.")

    def reorder_pages_after_delete(self, chapter_id):
        self.reorder_pages(chapter_id)

    def reorder_pages(self, chapter_id):
        if not self.db_manager:
            return
        
        all_items = [self.page_list.item(i) for i in range(self.page_list.count())]
        ordered_pages_data = [item.data(Qt.UserRole + 1) for item in all_items]

        if self.db_manager.update_page_order(chapter_id, ordered_pages_data):
            self.load_pages(chapter_id)
            self.set_dirty(True)
        else:
            QMessageBox.critical(self, "Errore", "Impossibile aggiornare l'ordine delle pagine nel database.")

    def reorder_pages_on_drop(self):
        if self.current_chapter_id is not None:
            self.reorder_pages(self.current_chapter_id)

    def page_selection_changed(self, current_row):
        if current_row >= 0:
            selected_item = self.page_list.item(current_row)
            image_data = selected_item.data(Qt.UserRole + 1) # Recupera i dati completi dell'immagine
            self.display_image(image_data)
        else:
            self.image_scene.clear()

    def move_page_up(self):
        if not self.db_manager or self.current_chapter_id is None:
            QMessageBox.warning(self, "Errore", "Nessun capitolo selezionato.")
            return
        current_row = self.page_list.currentRow()
        if current_row > 0:
            current_item = self.page_list.item(current_row)
            prev_item = self.page_list.item(current_row - 1)
            current_page_number = current_item.data(Qt.UserRole)
            prev_page_number = prev_item.data(Qt.UserRole)

            if self.db_manager.swap_page_order(self.current_chapter_id, current_page_number, prev_page_number):
                # Swap the items in the list widget
                current_item_clone = current_item.clone()
                prev_item_clone = prev_item.clone()
                self.page_list.takeItem(current_row)
                self.page_list.takeItem(current_row - 1)
                self.page_list.insertItem(current_row - 1, current_item_clone)
                self.page_list.insertItem(current_row, prev_item_clone)
                self.page_list.setCurrentRow(current_row - 1)
                self.load_pages(self.current_chapter_id)
                self.set_dirty(True)
            else:
                QMessageBox.critical(self, "Errore", "Impossibile spostare la pagina.")

    def move_page_down(self):
        if not self.db_manager or self.current_chapter_id is None:
            QMessageBox.warning(self, "Errore", "Nessun capitolo selezionato.")
            return
        current_row = self.page_list.currentRow()
        if current_row < self.page_list.count() - 1:
            current_item = self.page_list.item(current_row)
            next_item = self.page_list.item(current_row + 1)
            current_page_number = current_item.data(Qt.UserRole)
            next_page_number = next_item.data(Qt.UserRole)

            if self.db_manager.swap_page_order(self.current_chapter_id, current_page_number, next_page_number):
                # Swap the items in the list widget
                current_item_clone = current_item.clone()
                next_item_clone = next_item.clone()
                self.page_list.takeItem(current_row + 1)
                self.page_list.takeItem(current_row)
                self.page_list.insertItem(current_row, next_item_clone)
                self.page_list.insertItem(current_row + 1, current_item_clone)
                self.page_list.setCurrentRow(current_row + 1)
                self.load_pages(self.current_chapter_id)
                self.set_dirty(True)
            else:
                QMessageBox.critical(self, "Errore", "Impossibile spostare la pagina.")

    def display_image(self, image_data):
        self.image_scene.clear()
        if image_data:
            image = QImage()
            if image.loadFromData(image_data):
                pixmap = QPixmap.fromImage(image)
                self.image_scene.addPixmap(pixmap)
                self.image_view.fitInView(self.image_scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            else:
                print("Errore: Impossibile caricare l'immagine dai dati.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MangaCreatorApp()
    ex.showFullScreen()
    sys.exit(app.exec_())


        