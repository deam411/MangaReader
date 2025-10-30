import os
import sqlite3
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QScrollArea, QListView, QStyledItemDelegate, QApplication, QStyle, QLineEdit, QComboBox, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QPainter, QStandardItemModel, QStandardItem, QIcon, QPalette, QColor # Added QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, QSize, QSortFilterProxyModel, QTimer, QRect
from src.chapter_reader_window import ChapterReaderWindow
from src.paths import get_manga_dir
from src.settings import Settings
from src.settings_dialog import SettingsDialog

# App version
APP_VERSION = "0.0.4"

class MangaItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_grid_view = True

    def setViewMode(self, is_grid):
        self.is_grid_view = is_grid

    def paint(self, painter, option, index):
        painter.save()

        # Get data from model
        title = index.data(Qt.DisplayRole)
        cover_data = index.data(Qt.DecorationRole)
        description = index.data(Qt.UserRole + 1)

        # Draw background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, option.palette.base())

        # Draw cover
        if cover_data:
            pixmap = QPixmap()
            pixmap.loadFromData(cover_data)
            scaled_pixmap = pixmap.scaled(QSize(250, 375), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(option.rect.x() + 5, option.rect.y() + 5, scaled_pixmap)

        if self.is_grid_view:
            # Draw title
            text_rect = option.rect.adjusted(5, 320, -5, -5)
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

        # Search Bar
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search manga...")
        self.search_input.textChanged.connect(self.filter_manga)
        layout.addWidget(self.search_input)

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

        self.import_button = QPushButton('↓', self)
        self.import_button.setFixedSize(30, 30)
        self.import_button.setToolTip('Importa file .manga (Ctrl+I)')
        self.import_button.clicked.connect(self.import_manga)
        controls_layout.addWidget(self.import_button)

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
        self.manga_grid_view = QListWidget()
        self.manga_grid_view.setItemDelegate(self.delegate)
        self.manga_grid_view.setViewMode(QListWidget.IconMode)
        self.manga_grid_view.setFlow(QListWidget.LeftToRight)
        self.manga_grid_view.setResizeMode(QListWidget.Adjust)
        self.manga_grid_view.setGridSize(QSize(280, 420))
        self.manga_grid_view.itemDoubleClicked.connect(self.on_manga_selected)
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
            self.view_mode_button.setText('☰')
        else:
            self.manga_grid_view.setViewMode(QListWidget.ListMode)
            self.manga_grid_view.setFlow(QListWidget.TopToBottom)
            self.manga_grid_view.setResizeMode(QListWidget.Adjust)
            self.manga_grid_view.setGridSize(QSize())
            self.view_mode_button.setText('▦')
        self.manga_grid_view.update()

    def load_library(self):
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

        corrupted_files = []

        for file_name in os.listdir(manga_dir):
            if file_name.endswith('.manga'):
                full_path = os.path.join(manga_dir, file_name)
                try:
                    conn = sqlite3.connect(full_path)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM metadata")
                    metadata = cursor.fetchone()
                    if metadata:
                        manga_info = {
                            'file_name': full_path,
                            'title': metadata['title'] if metadata['title'] else file_name,
                            'cover': metadata['cover'],
                            'author': metadata['author'] if metadata['author'] else 'Sconosciuto',
                            'description': metadata['description'] if metadata['description'] else ''
                        }
                        self.all_manga_data.append(manga_info)
                    else:
                        corrupted_files.append(file_name)
                    conn.close()
                except sqlite3.DatabaseError as e:
                    print(f"Database error loading manga {full_path}: {e}")
                    corrupted_files.append(file_name)
                except Exception as e:
                    print(f"Error loading manga {full_path}: {e}")
                    corrupted_files.append(file_name)

        if corrupted_files:
            QMessageBox.warning(
                self,
                'File corrotti',
                f'I seguenti file .manga non possono essere caricati:\n\n' +
                '\n'.join(corrupted_files) +
                '\n\nPotrebbero essere corrotti o non validi.'
            )

        self._populate_view(self.all_manga_data)
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
                f'Directory corrente: {manga_dir}'
            )

    def _populate_view(self, data_list):
        self.manga_grid_view.clear()
        for manga_info in data_list:
            item = QListWidgetItem(manga_info['title'])
            item.setData(Qt.UserRole, manga_info['file_name'])
            item.setData(Qt.UserRole + 1, manga_info['description'])
            if manga_info['cover']:
                item.setData(Qt.DecorationRole, manga_info['cover'])
            self.manga_grid_view.addItem(item)

    def filter_manga(self, text):
        for i in range(self.manga_grid_view.count()):
            item = self.manga_grid_view.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

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
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.back_button = QPushButton('Back to Library', self)
        self.back_button.clicked.connect(self.back_to_library)
        layout.addWidget(self.back_button)

        # Edit Manga Button
        self.edit_manga_button = QPushButton('Edit Manga', self)
        self.edit_manga_button.clicked.connect(self.launch_manga_editor)
        layout.addWidget(self.edit_manga_button)

        self.cover_label = QLabel(self)
        layout.addWidget(self.cover_label)

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

        self.volume_list = QListWidget(self)
        self.volume_list.itemClicked.connect(self.on_volume_selected)
        layout.addWidget(self.volume_list)

        self.setLayout(layout)

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
                pixmap = QPixmap()
                pixmap.loadFromData(metadata['cover'])
                self.cover_label.setPixmap(pixmap.scaledToWidth(500)) # Increased size

        self.volume_list.clear()
        cursor.execute("SELECT * FROM volumes ORDER BY `order`")
        volumes = cursor.fetchall()
        for volume in volumes:
            item = QListWidgetItem(volume['name'])
            item.setData(Qt.UserRole, volume['id'])
            self.volume_list.addItem(item)

    def on_volume_selected(self, item):
        volume_id = item.data(Qt.UserRole)
        self.stacked_widget.setCurrentIndex(2)
        self.stacked_widget.widget(2).load_volume(self.manga_file, volume_id)

    def back_to_library(self):
        self.stacked_widget.setCurrentIndex(0)

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

class ReaderView(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.db_conn = None
        self.manga_file = None
        self.current_chapter_id = None
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()

        self.back_button = QPushButton('Back to Manga Details', self)
        self.back_button.clicked.connect(self.back_to_manga_details)
        left_layout.addWidget(self.back_button)

        # New horizontal layout for cover and chapter list
        cover_chapter_layout = QHBoxLayout()

        self.volume_cover_label = QLabel(self)
        cover_chapter_layout.addWidget(self.volume_cover_label)

        self.chapter_list = QListWidget(self)
        self.chapter_list.itemClicked.connect(self.on_chapter_selected)
        cover_chapter_layout.addWidget(self.chapter_list)

        left_layout.addLayout(cover_chapter_layout) # Add the new horizontal layout to the left_layout

        main_layout.addLayout(left_layout, 1)

        self.setLayout(main_layout)

    def load_volume(self, manga_file, volume_id):
        if self.db_conn:
            self.db_conn.close()
        self.manga_file = manga_file
        self.db_conn = sqlite3.connect(manga_file)
        self.db_conn.row_factory = sqlite3.Row
        cursor = self.db_conn.cursor()

        # Load volume cover
        cursor.execute("SELECT cover FROM volumes WHERE id = ?", (volume_id,))
        volume = cursor.fetchone()
        if volume and volume['cover']:
            pixmap = QPixmap()
            pixmap.loadFromData(volume['cover'])
            self.volume_cover_label.setPixmap(pixmap.scaledToWidth(500)) # Increased size

        # Load chapters for the selected volume
        self.chapter_list.clear()
        cursor.execute("SELECT * FROM chapters WHERE volume_id = ? ORDER BY `order`", (volume_id,))
        chapters = cursor.fetchall()
        for chapter in chapters:
            item = QListWidgetItem(chapter['name'])
            item.setData(Qt.UserRole, chapter['id'])
            self.chapter_list.addItem(item)

        self.current_chapter_id = None

    def on_chapter_selected(self, item):
        self.current_chapter_id = item.data(Qt.UserRole)
        chapter_name = item.text()
        self.chapter_reader_window = ChapterReaderWindow(self.manga_file, self.current_chapter_id)
        self.chapter_reader_window.showFullScreen() # Show maximized

    def back_to_manga_details(self):
        self.stacked_widget.setCurrentIndex(1)
