import os
import sqlite3
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QScrollArea, QListView, QStyledItemDelegate, QApplication, QStyle, QLineEdit, QComboBox, QFileDialog, QMessageBox, QProgressBar, QMenu, QDialog, QFormLayout, QDialogButtonBox
from PyQt5.QtGui import QPixmap, QPainter, QStandardItemModel, QStandardItem, QIcon, QPalette, QColor # Added QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, QSize, QSortFilterProxyModel, QTimer, QRect, QThread, pyqtSignal, QBuffer, QByteArray, QIODevice
from src.chapter_reader_window import PageDisplayWidget, LRUCache # Importa il widget di visualizzazione pagine e LRU cache
from src.paths import get_manga_dir
from src.settings import Settings
from src.settings_dialog import SettingsDialog
from src.constants import APP_VERSION, APP_NAME
from src.database import MangaDatabaseManager
from src.importers import ArchiveImporter
from src.cache_manager import CacheManager
from src.logger import get_logger

logger = get_logger(__name__)


class ArchiveImportDialog(QDialog):
    """Dialog per raccogliere metadata durante import di archivi CBZ/CBR."""

    def __init__(self, archive_path, parent=None):
        super().__init__(parent)
        self.archive_path = archive_path
        self.setWindowTitle('Import Archivio - Metadata')
        self.setMinimumWidth(400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Info file
        import os
        file_name = os.path.basename(self.archive_path)
        info_label = QLabel(f"Importazione: {file_name}")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Form per metadata
        form_layout = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setText(os.path.splitext(file_name)[0])  # Default: nome file
        form_layout.addRow("Titolo:", self.title_input)

        self.author_input = QLineEdit()
        form_layout.addRow("Autore:", self.author_input)

        self.volume_input = QLineEdit()
        self.volume_input.setText("Volume 1")
        form_layout.addRow("Nome Volume:", self.volume_input)

        self.chapter_input = QLineEdit()
        self.chapter_input.setText("Chapter 1")
        form_layout.addRow("Nome Capitolo:", self.chapter_input)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_metadata(self):
        """Restituisce i metadata inseriti."""
        return {
            'title': self.title_input.text() or None,
            'author': self.author_input.text() or None,
            'volume_name': self.volume_input.text() or "Volume 1",
            'chapter_name': self.chapter_input.text() or "Chapter 1"
        }


class BookmarkDialog(QDialog):
    """Dialog per aggiungere o rinominare un segnalibro."""

    def __init__(self, title="Nuovo Segnalibro", default_name="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        self.initUI(default_name)

    def initUI(self, default_name):
        layout = QVBoxLayout(self)

        # Label istruzioni
        info_label = QLabel("Inserisci un nome per il segnalibro:")
        layout.addWidget(info_label)

        # Input nome
        self.name_input = QLineEdit()
        self.name_input.setText(default_name)
        self.name_input.selectAll()
        layout.addWidget(self.name_input)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Focus sull'input
        self.name_input.setFocus()

    def get_name(self):
        """Restituisce il nome inserito."""
        return self.name_input.text().strip()


class ShortcutsDialog(QDialog):
    """Dialog che mostra tutte le scorciatoie da tastiera disponibili."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scorciatoie da Tastiera")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Titolo
        title = QLabel("<h2>📋 Scorciatoie da Tastiera</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Scroll area per le scorciatoie
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Widget contenitore
        container = QWidget()
        scroll.setWidget(container)
        shortcuts_layout = QVBoxLayout(container)

        # Definisci tutte le scorciatoie organizzate per categoria
        shortcuts_data = {
            "🌐 Navigazione Generale": [
                ("Esc", "Chiudi applicazione / Esci dalla schermata"),
                ("Backspace", "Torna alla schermata precedente"),
                ("F11", "Toggle fullscreen"),
            ],
            "📚 Libreria": [
                ("Ctrl+F", "Focus sulla barra di ricerca"),
                ("Ctrl+I", "Importa manga (.manga)"),
                ("Ctrl+E", "Esporta manga selezionato"),
                ("Ctrl+N", "Crea nuovo manga (apri editor)"),
                ("F5", "Aggiorna libreria"),
                ("Z", "Importa archivio CBZ/CBR"),
            ],
            "📖 Lettore": [
                ("↑", "Zoom in (10%)"),
                ("↓", "Zoom out (10%)"),
                ("Mouse Drag", "Pan/sposta immagine (tenere click sinistro)"),
                ("Scroll", "Scorri pagine verticalmente"),
                ("Ctrl+D", "Toggle vista doppia pagina"),
                ("Ctrl+B", "Aggiungi segnalibro alla pagina corrente"),
            ],
            "⚙️ Impostazioni": [
                ("Icona ⚙", "Apri pannello impostazioni"),
                ("Ctrl+?", "Mostra questo pannello scorciatoie"),
            ],
        }

        # Crea sezioni per ogni categoria
        for category, shortcuts in shortcuts_data.items():
            # Titolo categoria
            category_label = QLabel(f"<h3>{category}</h3>")
            shortcuts_layout.addWidget(category_label)

            # Tabella scorciatoie
            for key, description in shortcuts:
                shortcut_widget = QWidget()
                shortcut_layout = QHBoxLayout(shortcut_widget)
                shortcut_layout.setContentsMargins(20, 5, 20, 5)

                # Tasto/combinazione
                key_label = QLabel(f"<b>{key}</b>")
                key_label.setMinimumWidth(150)
                key_label.setStyleSheet("""
                    QLabel {
                        background-color: #404040;
                        padding: 5px 10px;
                        border-radius: 5px;
                        color: white;
                    }
                """)
                shortcut_layout.addWidget(key_label)

                # Descrizione
                desc_label = QLabel(description)
                desc_label.setWordWrap(True)
                shortcut_layout.addWidget(desc_label, 1)

                shortcuts_layout.addWidget(shortcut_widget)

            # Spaziatore tra categorie
            shortcuts_layout.addSpacing(10)

        shortcuts_layout.addStretch()

        # Pulsante Chiudi
        close_button = QPushButton("Chiudi")
        close_button.clicked.connect(self.accept)
        close_button.setMaximumWidth(100)
        layout.addWidget(close_button, alignment=Qt.AlignCenter)


class LibraryLoaderThread(QThread):
    """Thread per caricare i manga della libreria in background."""
    manga_loaded = pyqtSignal(dict)  # Emette un manga alla volta
    loading_complete = pyqtSignal(list)  # Lista di file corrotti
    progress_update = pyqtSignal(int, int)  # current, total

    def __init__(self, manga_dir):
        super().__init__()
        self.manga_dir = manga_dir

    def run(self):
        corrupted_files = []
        manga_files = [f for f in os.listdir(self.manga_dir) if f.endswith('.manga')]
        total = len(manga_files)

        for idx, file_name in enumerate(manga_files):
            full_path = os.path.join(self.manga_dir, file_name)
            try:
                conn = sqlite3.connect(full_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Carica solo i campi necessari
                cursor.execute("SELECT title, author, description, cover, tags FROM metadata")
                metadata = cursor.fetchone()

                if metadata:
                    # Calcola progresso di lettura usando database manager
                    db_manager = MangaDatabaseManager(full_path)
                    progress = db_manager.get_reading_progress()

                    # Fix: sqlite3.Row supporta accesso con [] ma non ha .get()
                    # Usa try-except per gestire campi mancanti
                    try:
                        manga_info = {
                            'file_name': full_path,
                            'title': metadata['title'] if metadata['title'] else file_name,
                            'cover': metadata['cover'],
                            'author': metadata['author'] if metadata['author'] else 'Sconosciuto',
                            'description': metadata['description'] if metadata['description'] else '',
                            'tags': metadata['tags'] if metadata['tags'] else '',
                            'progress': progress  # Aggiunto: progresso di lettura
                        }
                        self.manga_loaded.emit(manga_info)
                    except (KeyError, IndexError) as e:
                        logger.error(f"Metadata incompleti per {full_path}: {e}")
                        corrupted_files.append(file_name)
                else:
                    corrupted_files.append(file_name)

                conn.close()
            except sqlite3.DatabaseError as e:
                # Fix: Usa logger invece di print
                logger.error(f"Database error loading manga {full_path}: {e}")
                corrupted_files.append(file_name)
            except Exception as e:
                # Fix: Usa logger invece di print
                logger.error(f"Error loading manga {full_path}: {e}")
                corrupted_files.append(file_name)

            self.progress_update.emit(idx + 1, total)

        self.loading_complete.emit(corrupted_files)

class DeselectableListWidget(QListWidget):
    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item is None:
            self.clearSelection()
        super().mousePressEvent(event)


class MangaItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_grid_view = True
        # Fix: Usa LRUCache con limite per prevenire memory leak
        self.cover_cache = LRUCache(capacity=100)  # Cache in-memory per le cover ridimensionate (max 100)
        self.cache_manager = CacheManager()  # Cache persistent su disco

    def setViewMode(self, is_grid):
        self.is_grid_view = is_grid
        self.cover_cache.clear()  # Pulisce la cache quando cambia il view mode

    def paint(self, painter, option, index):
        painter.save()

        # Get data from model
        title = index.data(Qt.DisplayRole)
        cover_data = index.data(Qt.DecorationRole)
        description = index.data(Qt.UserRole + 1)
        progress = index.data(Qt.UserRole + 2)  # Progresso di lettura
        file_path = index.data(Qt.UserRole)  # Percorso file manga

        # Draw background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, option.palette.base())

        # Draw cover
        if cover_data:
            # Usa un hash dei dati come chiave di cache in-memory
            cache_key = (id(cover_data), option.rect.width(), option.rect.height())

            # Fix: Usa metodo get() della LRUCache
            target_pixmap = self.cover_cache.get(cache_key)
            if target_pixmap is None:
                # Dimensione fissa per le copertine
                fixed_size = QSize(250, 375)

                # Prova a caricare dalla cache persistent
                cached_path = None
                if file_path:
                    cached_path = self.cache_manager.get_cached(file_path, fixed_size.width())

                if cached_path:
                    # Carica dalla cache persistent
                    target_pixmap = QPixmap(cached_path)
                else:
                    # Crea e cacha la cover
                    pixmap = QPixmap()
                    pixmap.loadFromData(cover_data)

                    # Crea una pixmap della dimensione fissa desiderata
                    target_pixmap = QPixmap(fixed_size)
                    target_pixmap.fill(option.palette.alternateBase().color())

                    # Scala la pixmap originale per adattarla alla dimensione fissa
                    scaled_pixmap = pixmap.scaled(fixed_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                    # Calcola la posizione per centrare la pixmap scalata
                    x = (fixed_size.width() - scaled_pixmap.width()) // 2
                    y = (fixed_size.height() - scaled_pixmap.height()) // 2

                    # Disegna la pixmap scalata sulla pixmap target
                    target_painter = QPainter(target_pixmap)
                    target_painter.drawPixmap(x, y, scaled_pixmap)
                    target_painter.end()

                    # Salva nella cache persistent
                    if file_path:
                        self.cache_manager.save_to_cache(file_path, fixed_size.width(), target_pixmap)

                # Fix: Usa metodo put() della LRUCache
                self.cover_cache.put(cache_key, target_pixmap)

            # Disegna la pixmap target sulla vista
            cover_x = option.rect.x() + 5
            cover_y = option.rect.y() + 5
            painter.drawPixmap(cover_x, cover_y, target_pixmap)

            # Disegna overlay progresso di lettura
            if progress and progress['percentage'] > 0:
                self._draw_progress_overlay(painter, cover_x, cover_y, target_pixmap.width(), target_pixmap.height(), progress)

        if self.is_grid_view:
            # Draw title
            text_rect = option.rect.adjusted(5, 380, -5, -5)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, title)
        else:
            # List view painting
            # Draw text
            text_left = 250 + 15 # icon width + padding
            text_rect = QRect(text_left, option.rect.top() + 5, option.rect.width() - text_left - 5, option.rect.height() - 10)

            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop, title)

            if description:
                font.setBold(False)
                painter.setFont(font)
                font_metrics = painter.fontMetrics()
                title_height = font_metrics.height()
                description_rect = text_rect.adjusted(0, title_height + 5, 0, 0)
                
                painter.drawText(description_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, description)

        painter.restore()

    def _draw_progress_overlay(self, painter, x, y, width, height, progress):
        """Disegna overlay con percentuale di completamento sulla copertina."""
        percentage = progress['percentage']

        # Overlay semi-trasparente in basso
        overlay_height = 40
        overlay_rect = QRect(x, y + height - overlay_height, width, overlay_height)

        # Sfondo semi-trasparente
        painter.setOpacity(0.8)
        if percentage >= 100:
            # Verde per completati
            painter.fillRect(overlay_rect, QColor(46, 125, 50))
        elif percentage > 0:
            # Blu per in corso
            painter.fillRect(overlay_rect, QColor(25, 118, 210))

        # Reset opacità per testo
        painter.setOpacity(1.0)

        # Testo percentuale
        font = painter.font()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))

        if percentage >= 100:
            text = "✓ Completato"
        else:
            text = f"{percentage:.0f}%"

        painter.drawText(overlay_rect, Qt.AlignCenter, text)

        # Badge "In corso" nell'angolo superiore
        if 0 < percentage < 100:
            badge_width = 80
            badge_height = 25
            badge_rect = QRect(x + width - badge_width - 5, y + 5, badge_width, badge_height)

            # Sfondo badge
            painter.setOpacity(0.9)
            painter.fillRect(badge_rect, QColor(255, 152, 0))

            # Testo badge
            painter.setOpacity(1.0)
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(badge_rect, Qt.AlignCenter, "In corso")

    def sizeHint(self, option, index):
        if self.is_grid_view:
            return QSize(280, 420)
        else:
            return QSize(650, 400)

class LibraryView(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.all_manga_data = []
        self.is_grid_view = True
        self.delegate = MangaItemDelegate(self)
        self.first_load = True  # Per mostrare il messaggio solo al primo caricamento
        self.initUI()
        self.load_library()

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

        layout.addLayout(search_layout)

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
        from PyQt5.QtGui import QPalette
        palette = self.progress_bar.palette()
        palette.setColor(QPalette.Highlight, QColor(74, 158, 255))
        self.progress_bar.setPalette(palette)
        layout.addWidget(self.progress_bar)

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
        self.manga_grid_view.setGridSize(QSize(280, 420))
        # Fix: Disabilita drag and drop per prevenire duplicazione icone
        self.manga_grid_view.setDragEnabled(False)
        self.manga_grid_view.setAcceptDrops(False)
        self.manga_grid_view.itemDoubleClicked.connect(self.on_manga_selected)
        self.manga_grid_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.manga_grid_view.customContextMenuRequested.connect(self.show_manga_context_menu)
        layout.addWidget(self.manga_grid_view)

        # Info bar at bottom
        info_layout = QHBoxLayout()

        # Shortcuts help
        self.shortcuts_label = QLabel("Scorciatoie: F5=Aggiorna | F11=Fullscreen | Esc=Esci")
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
            self.manga_grid_view.setGridSize(QSize(280, 420))
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
        self.manga_grid_view.clear()
        self.all_manga_data = []

        try:
            manga_dir = get_manga_dir()
        except Exception as e:
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
        """Popola la combobox tag con tutti i tag unici dalla libreria."""
        all_tags = set()

        for manga in self.all_manga_data:
            if 'tags' in manga and manga['tags']:
                tags = [t.strip() for t in manga['tags'].split(',') if t.strip()]
                all_tags.update(tags)

        # Salva selezione corrente
        current_selection = self.tag_filter_combo.currentText()

        # Aggiorna la combobox
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem("All Tags")

        for tag in sorted(all_tags):
            self.tag_filter_combo.addItem(tag)

        # Ripristina selezione se possibile
        index = self.tag_filter_combo.findText(current_selection)
        if index >= 0:
            self.tag_filter_combo.setCurrentIndex(index)

    def on_loading_complete(self, corrupted_files):
        """Callback quando il caricamento è completato."""
        # Fix: Pulisci il thread per prevenire memory leak
        if hasattr(self, 'loader_thread') and self.loader_thread:
            self.loader_thread.deleteLater()
            self.loader_thread = None

        self.progress_bar.setVisible(False)

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
                '• Cambiare la directory della libreria nelle Impostazioni (⚙)\n\n'
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
        """Filtra i manga per testo di ricerca e tag selezionato."""
        search_text = self.search_input.text().lower()
        selected_tag = self.tag_filter_combo.currentText()

        for i in range(self.manga_grid_view.count()):
            item = self.manga_grid_view.item(i)
            manga_title = item.text().lower()

            # Ottieni i tags del manga dai dati
            manga_data = None
            for manga in self.all_manga_data:
                if manga['file_name'] == item.data(Qt.UserRole):
                    manga_data = manga
                    break

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

            # Mostra solo se entrambi i filtri passano
            item.setHidden(not (text_match and tag_match))

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
        """Mostra il menu contestuale per un manga."""
        item = self.manga_grid_view.itemAt(position)
        if not item:
            return

        manga_file = item.data(Qt.UserRole)

        # Crea il menu
        menu = QMenu(self)

        # Azione per cancellare la cronologia
        clear_history_action = menu.addAction("Cancella cronologia")

        # Mostra il menu e ottieni l'azione selezionata
        action = menu.exec_(self.manga_grid_view.mapToGlobal(position))

        if action == clear_history_action:
            self.clear_manga_history(manga_file, item)

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
            # Rimuovi caratteri non validi
            output_name = "".join(c for c in output_name if c.isalnum() or c in (' ', '-', '_')).strip()
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
        # Applica il tema usando la funzione centralizzata
        self.apply_theme()

    def apply_theme(self):
        """Applica il tema corrente all'applicazione usando la funzione di main.py"""
        import main
        main.apply_theme_to_app(QApplication.instance())

class MangaView(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
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
        layout.addWidget(QLabel("<h3>Volumi</h3>"))
        self.volume_list = QListWidget(self)
        self.volume_list.setToolTip('Doppio click su un volume per vedere i capitoli')
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

    def hideEvent(self, event):
        """Fix: Chiudi la connessione database quando la view viene nascosta."""
        if self.db_conn:
            self.db_conn.close()
            self.db_conn = None
        super().hideEvent(event)

    def load_manga(self, file_name):
        if self.db_conn:
            self.db_conn.close()

        self.manga_file = file_name
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
            display_text = f"📑 {bookmark['name']} - {bookmark['volume_name']}, {bookmark['chapter_name']}, Pag. {bookmark['page_number']}"
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
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()

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
        self.editor_app = MangaCreatorApp()
        self.editor_app.showFullScreen()
        self.editor_app.open_manga(self.manga_file) # Pass the current manga file to the editor

        # When the editor app closes, reload the current manga details
        self.editor_app.destroyed.connect(lambda: QTimer.singleShot(0, lambda: self.load_manga(self.manga_file)))

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

    def hideEvent(self, event):
        """Fix: Chiudi la connessione database quando la view viene nascosta."""
        if self.db_conn:
            self.db_conn.close()
            self.db_conn = None
        super().hideEvent(event)

    def load_volume(self, manga_file, volume_id):
        """Carica i dati del volume e i suoi capitoli."""
        if self.db_conn:
            self.db_conn.close()

        self.manga_file = manga_file
        self.volume_id = volume_id
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
        safe_name = "".join(c for c in self.volume_name if c.isalnum() or c in (' ', '-', '_')).strip()
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

class ReaderView(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.db_conn = None
        self.manga_file = None
        self.current_chapter_id = None
        self.db_manager = None

        # Timer per auto-save posizione lettura ogni 30 secondi
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave_reading_position)
        self.autosave_timer.setInterval(30000)  # 30 secondi

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Progress bar per il caricamento
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
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
        from PyQt5.QtGui import QPalette
        palette = self.progress_bar.palette()
        palette.setColor(QPalette.Highlight, QColor(74, 158, 255))
        self.progress_bar.setPalette(palette)
        main_layout.addWidget(self.progress_bar)

        self.scroll_area = QScrollArea(self)
        main_layout.addWidget(self.scroll_area)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.verticalScrollBar().setFocusPolicy(Qt.NoFocus)
        self.scroll_area.horizontalScrollBar().setFocusPolicy(Qt.NoFocus)
        self.scroll_area.installEventFilter(self)

        self.page_display_widget = PageDisplayWidget()
        self.scroll_area.setWidget(self.page_display_widget)

    def hideEvent(self, event):
        """Fix: Chiudi le connessioni database e ferma il timer quando la view viene nascosta."""
        self.autosave_timer.stop()
        if self.db_conn:
            self.db_conn.close()
            self.db_conn = None
        if self.db_manager:
            self.db_manager.close()
            self.db_manager = None
        super().hideEvent(event)

    def load_chapter(self, manga_file, chapter_id):
        """Carica i metadati del volume per caricamento on-demand."""
        if self.db_conn:
            self.db_conn.close()

        self.manga_file = manga_file
        self.current_chapter_id = chapter_id
        self.db_conn = sqlite3.connect(manga_file)
        self.db_conn.row_factory = sqlite3.Row

        # Inizializza database manager per storia lettura
        self.db_manager = MangaDatabaseManager(manga_file)

        # Avvia timer auto-save
        self.autosave_timer.start()

        cursor = self.db_conn.cursor()

        # Trova il volume_id del capitolo selezionato
        cursor.execute("SELECT volume_id FROM chapters WHERE id = ?", (chapter_id,))
        chapter_info = cursor.fetchone()

        if not chapter_info:
            return

        volume_id = chapter_info['volume_id']

        # Carica tutti i capitoli del volume in ordine
        cursor.execute("SELECT id, name FROM chapters WHERE volume_id = ? ORDER BY `order`", (volume_id,))
        all_chapters = cursor.fetchall()

        # Trova l'indice del capitolo selezionato
        # Converti entrambi a int per garantire il match corretto
        chapter_ids = [int(ch['id']) for ch in all_chapters]
        try:
            start_index = chapter_ids.index(int(chapter_id))
        except ValueError:
            print(f"WARNING: Chapter ID {chapter_id} not found in volume chapters {chapter_ids}")
            start_index = 0

        # Crea una lista di metadati per ogni pagina (tutti i capitoli del volume)
        page_metadata = []
        selected_chapter_page_index = 0  # Indice della prima pagina del capitolo selezionato

        for i in range(0, len(all_chapters)):  # Carica TUTTI i capitoli dall'inizio
            chapter = all_chapters[i]

            # Aggiungi separatore (tranne per il primo capitolo)
            if i > 0:
                page_metadata.append({
                    'type': 'separator',
                    'chapter_name': chapter['name'],
                    'chapter_id': None,
                    'page_number': None
                })

            # Se questo è il capitolo selezionato, salva l'indice della sua prima pagina
            if i == start_index:
                selected_chapter_page_index = len(page_metadata)

            # Conta le pagine del capitolo
            cursor.execute("SELECT COUNT(*) as count FROM pages WHERE chapter_id = ?", (chapter['id'],))
            page_count = cursor.fetchone()['count']

            # Aggiungi metadati per ogni pagina
            for page_num in range(1, page_count + 1):
                page_metadata.append({
                    'type': 'page',
                    'chapter_id': chapter['id'],
                    'page_number': page_num,
                    'chapter_name': chapter['name']
                })

        # Passa i metadati al widget con il database
        self.page_display_widget.set_pages_metadata(page_metadata, self.db_conn)

        # Scrolla alla prima pagina del capitolo selezionato
        if selected_chapter_page_index > 0:
            QTimer.singleShot(100, lambda: self.scroll_to_page_index(selected_chapter_page_index))

        self.progress_bar.setVisible(False)

    def scroll_to_page_index(self, page_index):
        """Scrolla la scroll area alla pagina specificata."""
        # Verifica che l'indice sia valido
        if page_index < 0 or page_index >= len(self.page_display_widget.page_positions):
            return

        # Ottieni la posizione della pagina
        page_rect = self.page_display_widget.page_positions[page_index]

        # Scrolla alla posizione Y della pagina
        self.scroll_area.verticalScrollBar().setValue(page_rect.y())

    def autosave_reading_position(self):
        """Salva automaticamente la posizione di lettura corrente."""
        if not self.db_manager or not self.current_chapter_id:
            return

        # Calcola la pagina corrente basandosi sulla posizione di scroll
        current_page = self.get_current_page_number()

        if current_page > 0:
            self.db_manager.save_reading_position(self.current_chapter_id, current_page)

    def get_current_page_number(self):
        """Determina il numero della pagina attualmente visibile."""
        if not self.page_display_widget or not self.page_display_widget.page_positions:
            return 1

        # Ottieni la posizione di scroll corrente
        scroll_pos = self.scroll_area.verticalScrollBar().value()

        # Trova la pagina più vicina alla posizione di scroll corrente
        page_positions = self.page_display_widget.page_positions
        for page_index, page_rect in enumerate(page_positions):
            # page_rect è un QRect, quindi usiamo .y() per ottenere la posizione Y
            if page_rect.y() > scroll_pos:
                # Restituisci la pagina precedente (quella attualmente visibile)
                return max(1, page_index)

        # Se siamo oltre l'ultima pagina, restituisci l'ultima
        return len(page_positions)

    def back_to_manga_details(self):
        # Salva posizione prima di uscire
        self.autosave_reading_position()

        # Ferma timer auto-save
        self.autosave_timer.stop()

        # Pulisce la cache del widget
        self.page_display_widget.loaded_pages_cache.clear()
        self.page_display_widget.image_cache.clear()
        self.stacked_widget.setCurrentIndex(2)  # Torna alla VolumeView

    def eventFilter(self, obj, event):
        """Intercetta gli eventi della scroll area per gestire ESC."""
        if event.type() == event.KeyPress:
            if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Backspace:
                self.back_to_manga_details()
                return True
        return super().eventFilter(obj, event)

    def toggle_view_mode(self):
        """Alterna tra vista singola e doppia pagina."""
        if hasattr(self.page_display_widget, 'toggle_view_mode'):
            new_mode = self.page_display_widget.toggle_view_mode()
            # Opzionale: mostra messaggio temporaneo all'utente
            mode_text = "Doppia Pagina" if new_mode == "double" else "Singola Pagina"
            print(f"Modalità vista cambiata: {mode_text}")

    def add_bookmark(self):
        """Aggiunge un segnalibro alla posizione corrente."""
        if not self.db_manager or not self.current_chapter_id:
            QMessageBox.warning(self, "Errore", "Impossibile aggiungere segnalibro: nessun capitolo caricato.")
            return

        # Ottieni pagina corrente
        current_page = self.get_current_page_number()

        # Genera nome default con timestamp
        import datetime
        default_name = f"Segnalibro {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"

        # Mostra dialog per nome
        dialog = BookmarkDialog(title="Nuovo Segnalibro", default_name=default_name, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            bookmark_name = dialog.get_name()
            if bookmark_name:
                bookmark_id = self.db_manager.add_bookmark(
                    self.current_chapter_id,
                    current_page,
                    bookmark_name
                )
                if bookmark_id > 0:
                    QMessageBox.information(
                        self,
                        "Segnalibro Aggiunto",
                        f"Segnalibro '{bookmark_name}' aggiunto alla pagina {current_page}"
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Errore",
                        "Impossibile aggiungere il segnalibro. Controlla i log per dettagli."
                    )

    def keyPressEvent(self, event):
        """Gestisce ESC e Backspace per tornare alla selezione capitoli."""
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Backspace:
            self.back_to_manga_details()
        else:
            super().keyPressEvent(event)
