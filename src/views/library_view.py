"""
LibraryView - Vista principale della libreria manga.

Gestisce:
- Visualizzazione griglia/lista manga
- Ricerca e filtri
- Import/Export manga
- Navigazione verso dettagli manga
"""

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
                              QListView, QListWidget, QListWidgetItem, QLineEdit, QComboBox,
                              QFileDialog, QMessageBox, QProgressBar, QMenu, QApplication, QDialog)
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem, QPalette, QColor, QPainter
from PyQt5.QtCore import Qt, QSize, QSortFilterProxyModel, QTimer, QRect

from src.paths import get_manga_dir
from src.settings import Settings
from src.settings_dialog import SettingsDialog
from src.constants import APP_VERSION, APP_NAME, DIALOG_MIN_WIDTH, GRID_ITEM_WIDTH, GRID_ITEM_HEIGHT
from src.database import MangaDatabaseManager
from src.importers import ArchiveImporter
from src.logger import get_logger
from src.views.dialogs import ArchiveImportDialog
from src.views.widgets import LibraryLoaderThread, MangaItemDelegate, DeselectableListWidget
from src.creator.manga_creator_app import MangaCreatorApp
from src.updater import check_for_updates, download_update, install_update, get_update_info_text
from src.views.utils import sanitize_filename
from src.stats.stats_widget import StatsWidget
from src.collections import CollectionManager

logger = get_logger(__name__)

class LibraryView(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.all_manga_data = []
        self.is_grid_view = True
        self.delegate = MangaItemDelegate(self)
        self.first_load = True  # Per mostrare il messaggio solo al primo caricamento
        self.is_loading = False  # Flag per prevenire caricamenti multipli simultanei
        self.settings = Settings()  # Per accedere alle impostazioni di sfondo
        self.background_pixmap = None  # Pixmap per lo sfondo personalizzato
        self.collection_manager = CollectionManager()  # Gestore collections (v0.3.0)

        # Imposta attributi per permettere custom painting dello sfondo
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setAutoFillBackground(False)

        self.initUI()
        self.load_library()
        self.apply_background_settings()  # Applica sfondo personalizzato home

    def initUI(self):
        layout = QVBoxLayout()

        # Search and Filter section
        search_layout = QHBoxLayout()

        # Search Bar
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search manga...")
        # Fix: Aggiungi shortcut al tooltip
        self.search_input.setToolTip('Cerca manga per titolo o autore (Ctrl+F per focus)')
        self.search_input.textChanged.connect(self.filter_manga)
        search_layout.addWidget(self.search_input, 3)  # 3/4 width

        # Tag Filter
        self.tag_filter_combo = QComboBox(self)
        self.tag_filter_combo.addItem("All Tags")
        self.tag_filter_combo.currentTextChanged.connect(self.filter_manga)
        self.tag_filter_combo.setMinimumWidth(150)
        search_layout.addWidget(self.tag_filter_combo, 1)  # 1/4 width

        # Advanced Search Toggle (v0.3.0)
        self.advanced_search_button = QPushButton('▼', self)
        self.advanced_search_button.setFixedSize(30, 30)
        self.advanced_search_button.setToolTip('Mostra/Nascondi filtri avanzati')
        self.advanced_search_button.setCheckable(True)
        self.advanced_search_button.clicked.connect(self._toggle_advanced_search)
        search_layout.addWidget(self.advanced_search_button)

        layout.addLayout(search_layout)

        # Advanced Search Panel (v0.3.0) - Initially hidden
        self.advanced_search_panel = QWidget()
        advanced_layout = QHBoxLayout(self.advanced_search_panel)
        advanced_layout.setContentsMargins(0, 5, 0, 5)

        # Reading Status Filter
        status_label = QLabel("Stato:")
        advanced_layout.addWidget(status_label)

        self.status_filter_combo = QComboBox(self)
        self.status_filter_combo.addItems([
            "Tutti",
            "Non letti",
            "In lettura",
            "Completati"
        ])
        self.status_filter_combo.currentTextChanged.connect(self.filter_manga)
        self.status_filter_combo.setMinimumWidth(120)
        advanced_layout.addWidget(self.status_filter_combo)

        # Author Filter
        author_label = QLabel("Autore:")
        advanced_layout.addWidget(author_label)

        self.author_filter_combo = QComboBox(self)
        self.author_filter_combo.addItem("Tutti gli autori")
        self.author_filter_combo.currentTextChanged.connect(self.filter_manga)
        self.author_filter_combo.setMinimumWidth(150)
        advanced_layout.addWidget(self.author_filter_combo)

        advanced_layout.addStretch()

        self.advanced_search_panel.setVisible(False)
        layout.addWidget(self.advanced_search_panel)

        # Progress bar per il caricamento
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(10)  # Rendi la barra più sottile
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center;
                background-color: #2b2b2b;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #4a9eff !important;
                border-radius: 4px;
            }
        """)
        # Forza il colore resettando la palette
        palette = self.progress_bar.palette()
        palette.setColor(QPalette.Highlight, QColor(74, 158, 255))
        self.progress_bar.setPalette(palette)
        layout.addWidget(self.progress_bar)

        # Stats Widget (v0.3.0)
        self.stats_widget = StatsWidget(self)
        layout.addWidget(self.stats_widget)

        # Sort Options and Add button
        controls_layout = QHBoxLayout()
        sort_label = QLabel("Sort by:")
        controls_layout.addWidget(sort_label)
        self.sort_combo = QComboBox(self)
        self.sort_combo.addItems(["Title A-Z", "Title Z-A", "Author A-Z", "Author Z-A"])
        self.sort_combo.currentIndexChanged.connect(self.sort_manga)
        controls_layout.addWidget(self.sort_combo)
        controls_layout.addStretch()

        self.view_mode_button = QPushButton('☰', self)
        self.view_mode_button.setFixedSize(30, 30)
        self.view_mode_button.setToolTip('Cambia visualizzazione (Griglia/Lista)')
        self.view_mode_button.clicked.connect(self.toggle_view_mode)
        controls_layout.addWidget(self.view_mode_button)

        # Pulsante Riprendi Lettura
        self.resume_button = QPushButton('▶', self)
        self.resume_button.setFixedSize(40, 30)
        self.resume_button.setToolTip('Riprendi Lettura')
        self.resume_button.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.resume_button.clicked.connect(self.resume_reading)
        self.resume_button.setVisible(False)  # Nascosto finché non c'è un manga da riprendere
        controls_layout.addWidget(self.resume_button)

        self.import_button = QPushButton('↓', self)
        self.import_button.setFixedSize(30, 30)
        self.import_button.setToolTip('Importa file .manga (Ctrl+I)')
        self.import_button.clicked.connect(self.import_manga)
        controls_layout.addWidget(self.import_button)

        self.import_archive_button = QPushButton('Z', self)
        self.import_archive_button.setFixedSize(30, 30)
        self.import_archive_button.setToolTip('Importa archivio CBZ/CBR')
        self.import_archive_button.setStyleSheet("font-weight: bold;")
        self.import_archive_button.clicked.connect(self.import_archive)
        controls_layout.addWidget(self.import_archive_button)

        self.export_button = QPushButton('↑', self)
        self.export_button.setFixedSize(30, 30)
        self.export_button.setToolTip('Esporta manga selezionato (Ctrl+E)')
        self.export_button.clicked.connect(self.export_manga)
        controls_layout.addWidget(self.export_button)

        self.add_manga_button = QPushButton('+', self)
        self.add_manga_button.setFixedSize(30, 30)
        self.add_manga_button.setToolTip('Crea nuovo manga (Ctrl+N)')
        self.add_manga_button.clicked.connect(self.launch_manga_creator)
        controls_layout.addWidget(self.add_manga_button)

        # Theme Switcher (v0.3.0)
        self.theme_combo = QComboBox(self)
        self.theme_combo.setToolTip('Cambia tema rapidamente')
        self.theme_combo.setMinimumWidth(100)
        self._populate_theme_combo()
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        controls_layout.addWidget(self.theme_combo)

        self.settings_button = QPushButton('⚙', self)
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.setStyleSheet("font-size: 20px;")
        self.settings_button.setToolTip('Impostazioni (Temi, Libreria, Performance)')
        self.settings_button.clicked.connect(self.open_settings)
        controls_layout.addWidget(self.settings_button)

        layout.addLayout(controls_layout)

        # Change to QListWidget for grid view
        self.manga_grid_view = DeselectableListWidget()
        self.manga_grid_view.setItemDelegate(self.delegate)
        self.manga_grid_view.setViewMode(QListWidget.IconMode)
        self.manga_grid_view.setFlow(QListWidget.LeftToRight)
        self.manga_grid_view.setResizeMode(QListWidget.Adjust)
        self.manga_grid_view.setGridSize(QSize(GRID_ITEM_WIDTH, GRID_ITEM_HEIGHT))
        # Fix: Disabilita drag and drop per prevenire duplicazione icone
        self.manga_grid_view.setDragEnabled(False)
        self.manga_grid_view.setAcceptDrops(False)
        self.manga_grid_view.itemDoubleClicked.connect(self.on_manga_selected)
        self.manga_grid_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.manga_grid_view.customContextMenuRequested.connect(self.show_manga_context_menu)
        layout.addWidget(self.manga_grid_view)

        # Info bar at bottom
        info_layout = QHBoxLayout()

        # Commands help
        self.shortcuts_label = QLabel("Premi F1 per vedere tutti i comandi")
        self.shortcuts_label.setStyleSheet("color: gray; font-size: 9px;")
        info_layout.addWidget(self.shortcuts_label)

        info_layout.addStretch()

        # Version label
        version_label = QLabel(f"Manga Reader v{APP_VERSION}")
        version_label.setStyleSheet("color: gray; font-size: 10px;")
        info_layout.addWidget(version_label)

        layout.addLayout(info_layout)

        self.setLayout(layout)

    def toggle_view_mode(self):
        self.is_grid_view = not self.is_grid_view
        self.update_view_mode()

    def update_view_mode(self):
        self.delegate.setViewMode(self.is_grid_view)
        if self.is_grid_view:
            self.manga_grid_view.setViewMode(QListWidget.IconMode)
            self.manga_grid_view.setFlow(QListWidget.LeftToRight)
            self.manga_grid_view.setResizeMode(QListWidget.Adjust)
            self.manga_grid_view.setGridSize(QSize(GRID_ITEM_WIDTH, GRID_ITEM_HEIGHT))
            # Fix: Assicura che drag drop sia disabilitato anche in IconMode
            self.manga_grid_view.setDragEnabled(False)
            self.manga_grid_view.setAcceptDrops(False)
            self.view_mode_button.setText('☰')
        else:
            self.manga_grid_view.setViewMode(QListWidget.ListMode)
            self.manga_grid_view.setFlow(QListWidget.TopToBottom)
            self.manga_grid_view.setResizeMode(QListWidget.Adjust)
            self.manga_grid_view.setGridSize(QSize())
            # Fix: Assicura che drag drop sia disabilitato anche in ListMode
            self.manga_grid_view.setDragEnabled(False)
            self.manga_grid_view.setAcceptDrops(False)
            self.view_mode_button.setText('▦')
        self.manga_grid_view.update()

    def load_library(self):
        """Carica la libreria usando un thread in background."""
        # Previeni caricamenti multipli simultanei (es. F5 premuto ripetutamente)
        if self.is_loading:
            logger.debug("Caricamento già in corso, ignorando richiesta")
            return

        self.is_loading = True
        self.manga_grid_view.clear()
        self.all_manga_data = []

        try:
            manga_dir = get_manga_dir()
        except Exception as e:
            self.is_loading = False  # Reset flag in caso di errore
            QMessageBox.critical(
                self,
                'Errore Directory',
                f'Impossibile accedere alla directory della libreria:\n{str(e)}\n\n'
                'Controlla le impostazioni e assicurati che la directory esista.'
            )
            return

        if not os.path.exists(manga_dir):
            QMessageBox.warning(
                self,
                'Directory non trovata',
                f'La directory della libreria non esiste:\n{manga_dir}\n\n'
                'Verrà creata automaticamente.'
            )
            try:
                os.makedirs(manga_dir, exist_ok=True)
            except Exception as e:
                self.is_loading = False  # Reset flag in caso di errore
                QMessageBox.critical(
                    self,
                    'Errore',
                    f'Impossibile creare la directory:\n{str(e)}'
                )
                return

        # Mostra la progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # Avvia il thread di caricamento
        self.loader_thread = LibraryLoaderThread(manga_dir)
        self.loader_thread.manga_loaded.connect(self.on_manga_loaded)
        self.loader_thread.progress_update.connect(self.on_progress_update)
        self.loader_thread.loading_complete.connect(self.on_loading_complete)
        self.loader_thread.start()

    def on_manga_loaded(self, manga_info):
        """Callback quando un manga viene caricato."""
        self.all_manga_data.append(manga_info)
        self._add_manga_to_view(manga_info)

    def on_progress_update(self, current, total):
        """Aggiorna la progress bar."""
        if total > 0:
            self.progress_bar.setValue(int((current / total) * 100))

    def populate_tag_filter(self):
        """Popola la combobox tag e autori con tutti i valori unici dalla libreria (v0.3.0)."""
        all_tags = set()
        all_authors = set()

        for manga in self.all_manga_data:
            if 'tags' in manga and manga['tags']:
                tags = [t.strip() for t in manga['tags'].split(',') if t.strip()]
                all_tags.update(tags)

            if 'author' in manga and manga['author'] and manga['author'] != 'Sconosciuto':
                all_authors.add(manga['author'])

        # Salva selezioni correnti
        current_tag_selection = self.tag_filter_combo.currentText()
        current_author_selection = self.author_filter_combo.currentText()

        # Aggiorna la combobox tag
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem("All Tags")

        for tag in sorted(all_tags):
            self.tag_filter_combo.addItem(tag)

        # Ripristina selezione tag se possibile
        index = self.tag_filter_combo.findText(current_tag_selection)
        if index >= 0:
            self.tag_filter_combo.setCurrentIndex(index)

        # Aggiorna la combobox autori (v0.3.0)
        self.author_filter_combo.clear()
        self.author_filter_combo.addItem("Tutti gli autori")

        for author in sorted(all_authors):
            self.author_filter_combo.addItem(author)

        # Ripristina selezione autore se possibile
        index = self.author_filter_combo.findText(current_author_selection)
        if index >= 0:
            self.author_filter_combo.setCurrentIndex(index)

    def on_loading_complete(self, corrupted_files):
        """Callback quando il caricamento è completato."""
        # Fix: Pulisci il thread per prevenire memory leak
        if hasattr(self, 'loader_thread') and self.loader_thread:
            self.loader_thread.deleteLater()
            self.loader_thread = None

        # Reset flag per permettere un nuovo caricamento
        self.is_loading = False

        self.progress_bar.setVisible(False)

        # Aggiorna stats widget (v0.3.0)
        self._update_stats()

        # Ottimizzazione: Crea dizionario per lookup O(1) in filter_manga
        self.manga_data_map = {manga['file_name']: manga for manga in self.all_manga_data}

        # Mostra pulsante Riprendi se c'è almeno un manga in corso
        has_in_progress = any(
            manga.get('progress') and 0 < manga['progress']['percentage'] < 100
            for manga in self.all_manga_data
        )
        self.resume_button.setVisible(has_in_progress)

        # Popola combobox tag con tutti i tag unici
        self.populate_tag_filter()

        if corrupted_files:
            QMessageBox.warning(
                self,
                'File corrotti',
                f'I seguenti file .manga non possono essere caricati:\n\n' +
                '\n'.join(corrupted_files) +
                '\n\nPotrebbero essere corrotti o non validi.'
            )

        self.sort_manga(self.sort_combo.currentIndex())

        # Mostra un messaggio se la libreria è vuota (solo al primo caricamento)
        if len(self.all_manga_data) == 0 and self.first_load:
            self.first_load = False
            QMessageBox.information(
                self,
                'Libreria vuota',
                'La libreria è vuota!\n\n'
                'Puoi:\n'
                '• Importare file .manga esistenti (pulsante ↓ o Ctrl+I)\n'
                '• Creare un nuovo manga (pulsante + o Ctrl+N)\n'
                '• Cambiare la directory della libreria nelle Impostazioni\n\n'
                f'Directory corrente: {get_manga_dir()}'
            )

    def _add_manga_to_view(self, manga_info):
        """Aggiunge un singolo manga alla vista."""
        item = QListWidgetItem(manga_info['title'])
        item.setData(Qt.UserRole, manga_info['file_name'])
        item.setData(Qt.UserRole + 1, manga_info['description'])
        item.setData(Qt.UserRole + 2, manga_info.get('progress'))  # Progresso di lettura
        if manga_info['cover']:
            item.setData(Qt.DecorationRole, manga_info['cover'])
        self.manga_grid_view.addItem(item)

    def _populate_view(self, data_list):
        """Popola la vista con una lista di manga."""
        self.manga_grid_view.clear()
        for manga_info in data_list:
            self._add_manga_to_view(manga_info)

    def filter_manga(self, text=None):
        """Filtra i manga per testo, tag, stato e autore (v0.3.0 enhanced)."""
        search_text = self.search_input.text().lower()
        selected_tag = self.tag_filter_combo.currentText()
        selected_status = self.status_filter_combo.currentText() if hasattr(self, 'status_filter_combo') else "Tutti"
        selected_author = self.author_filter_combo.currentText() if hasattr(self, 'author_filter_combo') else "Tutti gli autori"

        # Ottimizzazione: Usa il dizionario per lookup O(1) invece di loop O(n)
        if not hasattr(self, 'manga_data_map'):
            self.manga_data_map = {manga['file_name']: manga for manga in self.all_manga_data}

        for i in range(self.manga_grid_view.count()):
            item = self.manga_grid_view.item(i)
            manga_title = item.text().lower()
            file_name = item.data(Qt.UserRole)

            # Ottieni i dati del manga con lookup O(1)
            manga_data = self.manga_data_map.get(file_name)

            # Filtro testo
            text_match = search_text in manga_title
            if manga_data and 'author' in manga_data:
                text_match = text_match or search_text in manga_data['author'].lower()

            # Filtro tag
            tag_match = True
            if selected_tag and selected_tag != "All Tags":
                if manga_data and 'tags' in manga_data:
                    manga_tags = [t.strip() for t in manga_data['tags'].split(',') if t.strip()]
                    tag_match = selected_tag in manga_tags
                else:
                    tag_match = False

            # Filtro stato lettura (v0.3.0)
            status_match = True
            if selected_status != "Tutti":
                progress = manga_data.get('progress') if manga_data else None
                if selected_status == "Non letti":
                    status_match = not progress or progress['percentage'] == 0
                elif selected_status == "In lettura":
                    status_match = progress and 0 < progress['percentage'] < 100
                elif selected_status == "Completati":
                    status_match = progress and progress['percentage'] >= 100

            # Filtro autore (v0.3.0)
            author_match = True
            if selected_author and selected_author != "Tutti gli autori":
                if manga_data and 'author' in manga_data:
                    author_match = manga_data['author'] == selected_author
                else:
                    author_match = False

            # Mostra solo se tutti i filtri passano
            item.setHidden(not (text_match and tag_match and status_match and author_match))

    def sort_manga(self, index):
        if index == 0:
            self.all_manga_data.sort(key=lambda x: x['title'] if x['title'] else '', reverse=False)
        elif index == 1:
            self.all_manga_data.sort(key=lambda x: x['title'] if x['title'] else '', reverse=True)
        elif index == 2:
            self.all_manga_data.sort(key=lambda x: x['author'] if x['author'] else '', reverse=False)
        elif index == 3:
            self.all_manga_data.sort(key=lambda x: x['author'] if x['author'] else '', reverse=True)
        self._populate_view(self.all_manga_data)

    def on_manga_selected(self, item):
        manga_file = item.data(Qt.UserRole)
        self.stacked_widget.setCurrentIndex(1)
        self.stacked_widget.widget(1).load_manga(manga_file)

    def resume_reading(self):
        """Apre il manga letto più recentemente alla posizione salvata."""
        if not self.all_manga_data:
            return

        # Trova il manga con la lettura più recente
        most_recent_manga = None
        most_recent_position = None
        latest_timestamp = 0

        for manga_info in self.all_manga_data:
            progress = manga_info.get('progress')

            # Considera solo manga con progresso tra 0 e 100% (esclusi)
            if not progress or progress['percentage'] <= 0 or progress['percentage'] >= 100:
                continue

            # Ottieni la posizione di lettura dal database
            manga_file = manga_info['file_name']
            try:
                db_manager = MangaDatabaseManager(manga_file)
                position = db_manager.get_last_reading_position()

                if position and position.get('timestamp', 0) > latest_timestamp:
                    latest_timestamp = position['timestamp']
                    most_recent_manga = manga_file
                    most_recent_position = position
            except Exception as e:
                print(f"Errore caricamento posizione per {manga_file}: {e}")
                continue

        if not most_recent_manga or not most_recent_position:
            QMessageBox.information(
                self,
                'Nessun manga in corso',
                'Non ci sono manga in corso di lettura.'
            )
            return

        # Naviga direttamente al reader con il capitolo salvato
        chapter_id = most_recent_position['chapter_id']
        page_number = most_recent_position['page_number']

        # Carica il capitolo nel reader
        self.stacked_widget.setCurrentIndex(3)  # ReaderView
        reader_view = self.stacked_widget.widget(3)
        reader_view.load_chapter(most_recent_manga, chapter_id)

        # Scrolla alla pagina salvata dopo che il reader ha caricato
        # page_number è 1-based, page_index è 0-based
        page_index = page_number - 1
        QTimer.singleShot(200, lambda: reader_view.scroll_to_page_index(page_index))

    def show_manga_context_menu(self, position):
        """Mostra il menu contestuale per un manga (v0.3.0 con collections)."""
        item = self.manga_grid_view.itemAt(position)
        if not item:
            return

        manga_file = item.data(Qt.UserRole)

        # Seleziona l'item per mostrare visivamente cosa si sta selezionando
        self.manga_grid_view.setCurrentItem(item)

        # Forza l'evidenziazione dell'item anche durante il menu
        item.setSelected(True)

        # Crea il menu con stile migliorato per visibilità
        menu = QMenu(self)

        # Applica stylesheet per rendere più visibile l'hover
        menu.setStyleSheet("""
            QMenu {
                background-color: palette(window);
                border: 1px solid palette(dark);
            }
            QMenu::item {
                padding: 5px 20px 5px 20px;
            }
            QMenu::item:selected {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)

        # Azione per cancellare la cronologia
        clear_history_action = menu.addAction("Cancella cronologia")

        # Submenu Collections (v0.3.0)
        collections_menu = menu.addMenu("Collections")

        # Applica stesso stile al submenu
        collections_menu.setStyleSheet(menu.styleSheet())

        # Crea nuova collection
        new_collection_action = collections_menu.addAction("Nuova Collection...")

        collections_menu.addSeparator()

        # Aggiungi collection esistenti
        existing_collections = self.collection_manager.get_all_collections()
        collection_actions = {}

        if existing_collections:
            for collection_name in existing_collections:
                action = collections_menu.addAction(collection_name)
                collection_actions[action] = collection_name
        else:
            no_collections_action = collections_menu.addAction("(Nessuna collection)")
            no_collections_action.setEnabled(False)

        # Mostra il menu e ottieni l'azione selezionata
        action = menu.exec_(self.manga_grid_view.mapToGlobal(position))

        if action == clear_history_action:
            self.clear_manga_history(manga_file, item)
        elif action == new_collection_action:
            self._create_new_collection(manga_file)
        elif action in collection_actions:
            collection_name = collection_actions[action]
            self._add_to_collection(manga_file, collection_name)

    def clear_manga_history(self, manga_file, item):
        """Cancella la cronologia di lettura per un manga."""
        try:
            db_manager = MangaDatabaseManager(manga_file)
            db_manager.clear_reading_history()

            # Aggiorna i dati del manga nella lista
            # Rimuovi il progresso
            for manga_info in self.all_manga_data:
                if manga_info['file_name'] == manga_file:
                    manga_info['progress'] = None
                    break

            # Aggiorna l'item nella vista
            item.setData(Qt.UserRole + 2, None)

            # Forza il ridisegno dell'item
            self.manga_grid_view.update(self.manga_grid_view.indexFromItem(item))

            # Aggiorna la visibilità del pulsante Riprendi
            has_in_progress = any(
                manga.get('progress') and 0 < manga['progress']['percentage'] < 100
                for manga in self.all_manga_data
            )
            self.resume_button.setVisible(has_in_progress)

            QMessageBox.information(
                self,
                'Cronologia cancellata',
                'La cronologia di lettura è stata cancellata con successo.'
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                'Errore',
                f'Errore durante la cancellazione della cronologia: {str(e)}'
            )

    def launch_manga_creator(self):
        from src.creator.manga_creator_app import MangaCreatorApp
        self.creator_app = MangaCreatorApp()
        self.creator_app.showFullScreen()
        self.creator_app.destroyed.connect(self.load_library)

    def import_manga(self):
        """Import a .manga file into the library."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import .manga file",
            "",
            "Manga Files (*.manga);;All Files (*)"
        )

        if not file_path:
            return

        try:
            manga_dir = get_manga_dir()
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(manga_dir, file_name)

            # Check if file already exists
            if os.path.exists(dest_path):
                reply = QMessageBox.question(
                    self,
                    'File exists',
                    f'A file named "{file_name}" already exists. Do you want to overwrite it?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            # Copy the file
            import shutil
            shutil.copy2(file_path, dest_path)

            QMessageBox.information(self, 'Success', f'Successfully imported {file_name}')
            self.load_library()

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to import manga: {str(e)}')

    def import_archive(self):
        """Import archivio CBZ/CBR e convertilo in formato .manga."""
        # Verifica formati supportati
        importer = ArchiveImporter()
        supported_formats = importer.get_supported_formats()
        formats_str = ' '.join([f'*{ext}' for ext in supported_formats])

        # File dialog per selezionare archivio
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Archivio CBZ/CBR",
            "",
            f"Comic Archives ({formats_str});;All Files (*)"
        )

        if not file_path:
            return

        # Mostra dialog per metadata
        dialog = ArchiveImportDialog(file_path, self)
        if dialog.exec_() != QDialog.Accepted:
            return

        metadata = dialog.get_metadata()

        # Mostra progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        QApplication.processEvents()

        try:
            # Determina percorso output
            manga_dir = get_manga_dir()
            output_name = metadata['title'] or os.path.splitext(os.path.basename(file_path))[0]
            # Sanitizza il nome file
            output_name = sanitize_filename(output_name)
            output_path = os.path.join(manga_dir, f"{output_name}.manga")

            # Controlla se esiste già
            if os.path.exists(output_path):
                reply = QMessageBox.question(
                    self,
                    'File exists',
                    f'Un file "{output_name}.manga" esiste già. Vuoi sovrascriverlo?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    self.progress_bar.setVisible(False)
                    return

            # Esegui import
            success = importer.import_archive(
                archive_path=file_path,
                output_path=output_path,
                title=metadata['title'],
                author=metadata['author'],
                volume_name=metadata['volume_name'],
                chapter_name=metadata['chapter_name']
            )

            self.progress_bar.setVisible(False)

            if success:
                QMessageBox.information(
                    self,
                    'Import completato',
                    f'Archivio importato con successo come "{output_name}.manga"'
                )
                self.load_library()
            else:
                QMessageBox.critical(
                    self,
                    'Errore Import',
                    'Errore durante l\'importazione dell\'archivio. Verifica il file e riprova.'
                )

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(
                self,
                'Errore',
                f'Errore durante l\'import: {str(e)}'
            )

    def export_manga(self):
        """Export the selected .manga file to a chosen location."""
        current_item = self.manga_grid_view.currentItem()

        if not current_item:
            QMessageBox.warning(self, 'No selection', 'Please select a manga to export.')
            return

        manga_file = current_item.data(Qt.UserRole)

        if not manga_file or not os.path.exists(manga_file):
            QMessageBox.warning(self, 'Error', 'Selected manga file not found.')
            return

        try:
            file_name = os.path.basename(manga_file)
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export .manga file",
                file_name,
                "Manga Files (*.manga);;All Files (*)"
            )

            if not save_path:
                return

            # Copy the file
            import shutil
            shutil.copy2(manga_file, save_path)

            QMessageBox.information(self, 'Success', f'Successfully exported to {save_path}')

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to export manga: {str(e)}')

    def open_settings(self):
        """Apre il dialog delle impostazioni."""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.on_settings_changed)
        if dialog.exec_():
            # Ricarica la libreria se il percorso è cambiato
            self.load_library()

    def on_settings_changed(self):
        """Callback quando le impostazioni cambiano."""
        # Il tema viene già applicato dal SettingsDialog prima di emettere questo segnale

        # BLOCCA tutti i rendering durante il cambio tema per evitare flickering
        self.manga_grid_view.setUpdatesEnabled(False)

        # Forza Qt a processare tutti gli eventi pendenti per applicare completamente il tema
        QApplication.instance().processEvents()

        # Pulisci ENTRAMBE le cache (in-memory e persistent) per applicare i nuovi colori del tema
        self.delegate.cover_cache.clear()  # Cache LRU in memoria
        self.delegate.cache_manager.clear_all_cache()  # Cache persistent su disco

        # Attendi che la pulizia della cache sia completata
        QApplication.instance().processEvents()

        # RICREA il delegate completamente per assicurarsi che abbia il palette aggiornato
        old_delegate = self.delegate
        self.delegate = MangaItemDelegate(self)
        self.manga_grid_view.setItemDelegate(self.delegate)
        old_delegate.deleteLater()  # Pulisci il vecchio delegate

        # Forza il refresh del palette della grid view e del viewport
        self.manga_grid_view.setPalette(QApplication.instance().palette())
        self.manga_grid_view.viewport().setPalette(QApplication.instance().palette())

        # IMPORTANTE: Aspetta che il delegate sia completamente inizializzato con il nuovo palette
        # prima di iniziare a renderizzare le cover. Questo previene il ritardo visibile.
        QApplication.instance().processEvents()
        QApplication.instance().processEvents()  # Due volte per essere sicuri

        # Riapplica lo sfondo personalizzato della libreria
        self.apply_background_settings()

        # Ri-popola la vista con i dati già caricati invece di ricaricare dal disco
        self._populate_view(self.all_manga_data)

        # RIABILITA i rendering - ora tutte le cover appariranno insieme con il colore corretto
        self.manga_grid_view.setUpdatesEnabled(True)

    def paintEvent(self, event):
        """
        Disegna lo sfondo personalizzato prima di disegnare i widget figli.

        Questo metodo viene chiamato automaticamente da Qt quando il widget
        deve essere ridisegnato. Disegnando qui l'immagine di sfondo, ci assicuriamo
        che appaia DIETRO tutti i widget figli.
        """
        # Disegna lo sfondo PRIMA di chiamare super().paintEvent()
        if self.background_pixmap and not self.background_pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            # Disegna l'immagine centrata senza ripetizione
            widget_rect = self.rect()
            pixmap_rect = self.background_pixmap.rect()

            # Centra l'immagine
            x = (widget_rect.width() - pixmap_rect.width()) // 2
            y = (widget_rect.height() - pixmap_rect.height()) // 2

            # Disegna il pixmap centrato
            painter.drawPixmap(x, y, self.background_pixmap)
            painter.end()

        # Ora disegna il resto del widget (inclusi i figli)
        super().paintEvent(event)

    def apply_background_settings(self):
        """
        Applica le impostazioni di sfondo personalizzato alla LibraryView.

        Legge da library.background_image e carica il pixmap per lo sfondo
        della home/libreria.
        """
        # Leggi impostazione sfondo immagine
        bg_image = self.settings.get("library.background_image", None)

        # Applica immagine di sfondo se presente e valida
        if bg_image and os.path.exists(bg_image):
            # Carica il pixmap dall'immagine
            self.background_pixmap = QPixmap(bg_image)

            if self.background_pixmap.isNull():
                logger.warning(f"Failed to load background image: {bg_image}")
                self.background_pixmap = None
            else:
                logger.info(f"Loaded library background image: {bg_image}")
                # Abilita auto-fill per assicurarsi che paintEvent venga chiamato
                self.setAutoFillBackground(False)

                # Informa il delegate che c'è uno sfondo personalizzato
                self.delegate.has_custom_background = True

                # Pulisci la cache del delegate per forzare il ridisegno con trasparenza
                self.delegate.cover_cache.clear()

                # Rendi trasparente il QListWidget e i suoi item per mostrare lo sfondo
                # Applica DOPO aver caricato l'immagine per sovrascrivere il tema
                self.manga_grid_view.setStyleSheet("""
                    QListWidget {
                        background-color: transparent;
                        border: none;
                    }
                    QListWidget::item {
                        background-color: transparent;
                    }
                    QListWidget::item:hover {
                        background-color: rgba(255, 255, 255, 30);
                    }
                    QListWidget::item:selected {
                        background-color: rgba(74, 158, 255, 80);
                    }
                """)

            # Forza il ridisegno del widget e della lista
            self.update()
            self.manga_grid_view.viewport().update()
        else:
            # Reset pixmap e stylesheet se non c'è immagine
            self.background_pixmap = None

            # Informa il delegate che NON c'è più uno sfondo personalizzato
            self.delegate.has_custom_background = False

            # Rimuovi trasparenza se non c'è sfondo personalizzato
            self.manga_grid_view.setStyleSheet("")

            # Pulisci la cache del delegate per forzare il ridisegno con il tema normale
            self.delegate.cover_cache.clear()

            self.update()
            self.manga_grid_view.viewport().update()
            logger.debug("No library background image set")

    def _update_stats(self):
        """Aggiorna il widget statistiche con i dati correnti (v0.3.0)."""
        total = len(self.all_manga_data)
        completed = sum(1 for m in self.all_manga_data
                       if m.get('progress') and m['progress']['percentage'] >= 100)
        reading = sum(1 for m in self.all_manga_data
                     if m.get('progress') and 0 < m['progress']['percentage'] < 100)
        unread = total - completed - reading

        self.stats_widget.update_stats(total, completed, reading, unread)

    def _populate_theme_combo(self):
        """Popola la combobox con i temi disponibili (v0.3.0)."""
        from src.theme_manager import load_themes

        themes = load_themes()
        current_theme = self.settings.get_theme()

        # Blocca i segnali durante il popolamento per evitare trigger indesiderati
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()

        for theme_name in themes.keys():
            # Capitalizza il nome del tema per visualizzazione migliore
            display_name = theme_name.capitalize()
            self.theme_combo.addItem(display_name, theme_name)

        # Seleziona il tema corrente
        index = self.theme_combo.findData(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self.theme_combo.blockSignals(False)

    def _on_theme_changed(self, display_name):
        """Applica il tema selezionato (v0.3.0)."""
        if not display_name:
            return

        # Ottieni il nome reale del tema dai dati dell'item corrente
        theme_name = self.theme_combo.currentData()
        if not theme_name:
            return

        # Salva nelle impostazioni
        self.settings.set("theme", theme_name)
        self.settings.save()

        # BLOCCA tutti i rendering durante il cambio tema per evitare flickering
        self.manga_grid_view.setUpdatesEnabled(False)

        # Applica il tema immediatamente
        from src.theme_manager import apply_theme
        apply_theme(QApplication.instance())

        # Forza Qt a processare tutti gli eventi pendenti per applicare completamente il tema
        QApplication.instance().processEvents()

        # Pulisci ENTRAMBE le cache (in-memory e persistent) per applicare i nuovi colori del tema
        self.delegate.cover_cache.clear()  # Cache LRU in memoria
        self.delegate.cache_manager.clear_all_cache()  # Cache persistent su disco

        # Attendi che la pulizia della cache sia completata
        QApplication.instance().processEvents()

        # RICREA il delegate completamente per assicurarsi che abbia il palette aggiornato
        # Questo risolve il problema dove il delegate usa il vecchio palette durante il render
        old_delegate = self.delegate
        self.delegate = MangaItemDelegate(self)
        self.manga_grid_view.setItemDelegate(self.delegate)
        old_delegate.deleteLater()  # Pulisci il vecchio delegate

        # Forza il refresh del palette della grid view e del viewport
        self.manga_grid_view.setPalette(QApplication.instance().palette())
        self.manga_grid_view.viewport().setPalette(QApplication.instance().palette())

        # IMPORTANTE: Aspetta che il delegate sia completamente inizializzato con il nuovo palette
        # prima di iniziare a renderizzare le cover. Questo previene il ritardo visibile.
        QApplication.instance().processEvents()
        QApplication.instance().processEvents()  # Due volte per essere sicuri

        # Ri-popola la vista con i dati già caricati invece di ricaricare dal disco
        # Questo è molto più veloce e forza comunque la rigenerazione delle cover
        self._populate_view(self.all_manga_data)

        # RIABILITA i rendering - ora tutte le cover appariranno insieme con il colore corretto
        self.manga_grid_view.setUpdatesEnabled(True)

        logger.info(f"Tema cambiato a: {theme_name}")

    def _create_new_collection(self, manga_file):
        """Crea una nuova collection e aggiunge il manga (v0.3.0)."""
        from PyQt5.QtWidgets import QInputDialog

        collection_name, ok = QInputDialog.getText(
            self,
            "Nuova Collection",
            "Nome della collection:"
        )

        if not ok or not collection_name.strip():
            return

        collection_name = collection_name.strip()

        # Crea la collection
        if self.collection_manager.create_collection(collection_name):
            # Aggiungi il manga alla collection
            self.collection_manager.add_to_collection(collection_name, manga_file)

            QMessageBox.information(
                self,
                "Collection Creata",
                f"Collection '{collection_name}' creata e manga aggiunto!"
            )
            logger.info(f"Collection '{collection_name}' creata con manga: {manga_file}")
        else:
            QMessageBox.warning(
                self,
                "Errore",
                f"Collection '{collection_name}' già esistente!"
            )

    def _add_to_collection(self, manga_file, collection_name):
        """Aggiunge il manga a una collection esistente (v0.3.0)."""
        self.collection_manager.add_to_collection(collection_name, manga_file)

        QMessageBox.information(
            self,
            "Manga Aggiunto",
            f"Manga aggiunto alla collection '{collection_name}'!"
        )
        logger.info(f"Manga {manga_file} aggiunto a collection: {collection_name}")

    def _toggle_advanced_search(self):
        """Mostra/nascondi il pannello di ricerca avanzata (v0.3.0)."""
        is_visible = not self.advanced_search_panel.isVisible()
        self.advanced_search_panel.setVisible(is_visible)

        # Aggiorna il pulsante
        if is_visible:
            self.advanced_search_button.setText('▲')
        else:
            self.advanced_search_button.setText('▼')

        logger.debug(f"Advanced search panel {'shown' if is_visible else 'hidden'}")
