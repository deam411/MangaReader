"""
Widget condivisi per le view di MangaReader.

Contiene:
- LibraryLoaderThread: Thread per caricamento asincrono manga
- DeselectableListWidget: QListWidget con deselect click su sfondo
- MangaItemDelegate: Custom delegate per rendering manga items con cache
"""

import os
import sqlite3
from PyQt5.QtWidgets import QListWidget, QStyledItemDelegate, QApplication, QStyle
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, QSize, QRect, QThread, pyqtSignal

from src.chapter_reader_window import LRUCache
from src.cache_manager import CacheManager
from src.constants import (
    COVER_CACHE_MAX,
    GRID_ITEM_WIDTH,
    GRID_ITEM_HEIGHT,
    DELEGATE_COVER_WIDTH,
    DELEGATE_COVER_HEIGHT
)
from src.logger import get_logger
from src.views.utils import calculate_reading_progress_fast

logger = get_logger(__name__)


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
                with sqlite3.connect(full_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()

                    # Carica solo i campi necessari
                    cursor.execute("SELECT title, author, description, cover, tags FROM metadata")
                    metadata = cursor.fetchone()

                    if metadata:
                        # Calcola progresso di lettura con query ottimizzata (no MangaDatabaseManager)
                        # Questo evita di creare schema/indici/migrations per ogni manga
                        progress = calculate_reading_progress_fast(cursor)

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

            except sqlite3.DatabaseError as e:
                logger.error(f"Database error loading manga {full_path}: {e}")
                corrupted_files.append(file_name)
            except Exception as e:
                logger.error(f"Error loading manga {full_path}: {e}")
                corrupted_files.append(file_name)

            self.progress_update.emit(idx + 1, total)

        self.loading_complete.emit(corrupted_files)


class DeselectableListWidget(QListWidget):
    """QListWidget che deseleziona quando si clicca sullo sfondo."""

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item is None:
            self.clearSelection()
        super().mousePressEvent(event)


class MangaItemDelegate(QStyledItemDelegate):
    """
    Custom delegate per rendering manga items.

    Supporta:
    - Grid view e List view
    - Cache a 2 livelli (in-memory LRU + persistent disk)
    - Progress overlay su copertine
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_grid_view = True
        self.has_custom_background = False  # Flag per sapere se c'è uno sfondo personalizzato
        # Fix: Usa LRUCache con limite per prevenire memory leak
        self.cover_cache = LRUCache(capacity=COVER_CACHE_MAX)  # Cache in-memory per le cover ridimensionate
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
        # Se c'è uno sfondo personalizzato, usa trasparenza per item non selezionati
        if option.state & QStyle.State_Selected:
            # Item selezionato: usa colore semi-trasparente per evidenziare
            if self.has_custom_background:
                painter.fillRect(option.rect, QColor(74, 158, 255, 80))
            else:
                painter.fillRect(option.rect, option.palette.highlight())
        else:
            # Item normale: trasparente se c'è sfondo custom, altrimenti usa tema
            if not self.has_custom_background:
                painter.fillRect(option.rect, option.palette.base())

        # Draw cover
        if cover_data:
            # Usa file_path come chiave di cache stabile (invece di id(cover_data) che cambia)
            # Dimensione fissa per le copertine, quindi non serve includerla nella key
            cache_key = file_path if file_path else id(cover_data)

            # Fix: Usa metodo get() della LRUCache
            target_pixmap = self.cover_cache.get(cache_key)
            if target_pixmap is None:
                # Dimensione fissa per le copertine (da constants)
                fixed_size = QSize(DELEGATE_COVER_WIDTH, DELEGATE_COVER_HEIGHT)

                # Prova a caricare dalla cache persistent
                cached_path = None
                if file_path:
                    cached_path = self.cache_manager.get_cached(file_path, fixed_size.width())

                # Con sfondo custom, skippa la cache persistent per avere sempre trasparenza
                if cached_path and not self.has_custom_background:
                    # Carica dalla cache persistent solo se non c'è sfondo custom
                    target_pixmap = QPixmap(cached_path)
                else:
                    # Crea e cacha la cover
                    pixmap = QPixmap()
                    pixmap.loadFromData(cover_data)

                    # Scala la pixmap originale per adattarla alla dimensione fissa
                    scaled_pixmap = pixmap.scaled(fixed_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                    if self.has_custom_background:
                        # Con sfondo custom, usa direttamente la cover scalata senza padding
                        # Questo permette allo sfondo di essere visibile attorno alle cover
                        target_pixmap = scaled_pixmap
                    else:
                        # Senza sfondo custom, crea un pixmap con padding centrato
                        target_pixmap = QPixmap(fixed_size)
                        target_pixmap.fill(option.palette.alternateBase().color())

                        # Calcola la posizione per centrare la pixmap scalata
                        x = (fixed_size.width() - scaled_pixmap.width()) // 2
                        y = (fixed_size.height() - scaled_pixmap.height()) // 2

                        # Disegna la pixmap scalata sulla pixmap target
                        target_painter = QPainter(target_pixmap)
                        target_painter.drawPixmap(x, y, scaled_pixmap)
                        target_painter.end()

                        # Salva nella cache persistent solo se non c'è sfondo custom
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
            # Usa palette consistente dall'applicazione invece di option.palette
            # per evitare colori inconsistenti tra diversi item
            from PyQt5.QtWidgets import QApplication
            app_palette = QApplication.instance().palette()

            if option.state & QStyle.State_Selected:
                # Item selezionato: usa highlightedText (bianco)
                painter.setPen(app_palette.highlightedText().color())
            else:
                # Item normale: usa text color del tema
                painter.setPen(app_palette.text().color())

            text_rect = option.rect.adjusted(5, 380, -5, -5)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, title)
        else:
            # List view painting
            # Usa palette consistente dall'applicazione invece di option.palette
            # per evitare colori inconsistenti tra diversi item
            from PyQt5.QtWidgets import QApplication
            app_palette = QApplication.instance().palette()

            if option.state & QStyle.State_Selected:
                # Item selezionato: usa highlightedText (bianco)
                painter.setPen(app_palette.highlightedText().color())
            else:
                # Item normale: usa text color del tema
                painter.setPen(app_palette.text().color())

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
            return QSize(GRID_ITEM_WIDTH, GRID_ITEM_HEIGHT)
        else:
            return QSize(650, 400)
