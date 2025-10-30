import sqlite3
from collections import OrderedDict
from PyQt5.QtWidgets import QMainWindow, QScrollArea, QVBoxLayout, QLabel, QWidget
from PyQt5.QtGui import QPainter, QPixmap, QImage
from PyQt5.QtCore import Qt, QSize, QTimer, QRect, QRunnable, QThreadPool, pyqtSignal, QObject
from .settings import Settings

class LRUCache:
    """Cache LRU (Least Recently Used) per le immagini."""
    def __init__(self, capacity=50):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self.cache:
            return None
        # Sposta l'elemento alla fine (più recente)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            # Aggiorna e sposta alla fine
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            # Rimuovi il primo elemento (meno usato)
            self.cache.popitem(last=False)

    def clear(self):
        self.cache.clear()

class ImageLoaderSignals(QObject):
    image_loaded = pyqtSignal(int, QPixmap) # page_index, pixmap

class ImageLoaderRunnable(QRunnable):
    def __init__(self, page_index, image_data, target_width, signals):
        super().__init__()
        self.page_index = page_index
        self.image_data = image_data
        self.target_width = target_width
        self.signals = signals

    def run(self):
        image = QImage()
        if image.loadFromData(self.image_data):
            pixmap = QPixmap.fromImage(image)
            scaled_pixmap = pixmap.scaledToWidth(self.target_width, Qt.SmoothTransformation)
            self.signals.image_loaded.emit(self.page_index, scaled_pixmap)

class PageDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Carica impostazioni performance
        settings = Settings()
        cache_size = settings.get("performance.image_cache_size", 50)
        self.preload_pages = settings.get("performance.preload_pages", 2)
        self.lazy_loading = settings.get("performance.lazy_loading", True)

        self.pages_data = [] # List of image_data
        self.image_cache = LRUCache(capacity=cache_size)  # Cache LRU per i pixmap
        self.page_positions = [] # List of (x, y, width, height) for each page
        self.total_height = 0
        self.current_width = 0
        self.page_spacing = 10 # Add 10px spacing between pages
        self.thread_pool = QThreadPool()
        self.image_loader_signals = ImageLoaderSignals()
        self.image_loader_signals.image_loaded.connect(self.handle_image_loaded)
        self.loading_pages = set()  # Traccia le pagine in caricamento

    def handle_image_loaded(self, page_index, pixmap):
        if 0 <= page_index < len(self.pages_data):
            self.image_cache.put(page_index, pixmap)  # Salva nella cache LRU
            self.loading_pages.discard(page_index)  # Rimuovi dal set di loading
            self.update() # Request repaint

    def set_pages_data(self, pages_data_list):
        self.pages_data = pages_data_list  # Solo i dati raw
        self.image_cache.clear()  # Pulisce la cache
        self.loading_pages.clear()
        self.update_layout()

    def update_layout(self):
        self.page_positions = []
        self.total_height = 0
        self.current_width = self.width() # Use current widget width for scaling

        if self.current_width <= 0:
            return

        y_offset = 0
        for i, image_data in enumerate(self.pages_data):
            if image_data:
                # Load a temporary pixmap to get original size for aspect ratio calculation
                temp_image = QImage()
                temp_image.loadFromData(image_data)
                if not temp_image.isNull():
                    original_size = temp_image.size()
                    scaled_height = int(original_size.height() * (self.current_width / original_size.width()))

                    self.page_positions.append(QRect(0, y_offset, self.current_width, scaled_height))
                    y_offset += scaled_height + self.page_spacing
                else:
                    self.page_positions.append(QRect(0, y_offset, self.current_width, 100)) # Placeholder height
                    y_offset += 100 + self.page_spacing
            else:
                self.page_positions.append(QRect(0, y_offset, self.current_width, 100)) # Placeholder height
                y_offset += 100 + self.page_spacing

        self.total_height = y_offset
        self.setMinimumSize(self.current_width, self.total_height)
        self.update() # Request a repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black) # Background for the widget

        visible_rect = event.rect() # The visible area of the widget (viewport)

        # Lista delle pagine da precaricare
        pages_to_preload = []

        for i, image_data in enumerate(self.pages_data):
            if i >= len(self.page_positions):
                continue

            page_rect = self.page_positions[i]

            if page_rect.intersects(visible_rect): # Only draw visible pages
                cached_pixmap = self.image_cache.get(i)

                if cached_pixmap is None:
                    # Image not in cache
                    if i not in self.loading_pages:
                        # Inizia il caricamento
                        self.loading_pages.add(i)
                        runnable = ImageLoaderRunnable(i, image_data, self.current_width, self.image_loader_signals)
                        self.thread_pool.start(runnable)

                    # Draw a placeholder while loading
                    painter.fillRect(page_rect, Qt.darkGray)
                    painter.drawText(page_rect, Qt.AlignCenter, "Caricamento...")
                else:
                    # Image is cached, draw it
                    painter.drawPixmap(page_rect.topLeft(), cached_pixmap)

                # Aggiungi pagine successive da precaricare
                for j in range(1, self.preload_pages + 1):
                    next_page = i + j
                    if next_page < len(self.pages_data):
                        pages_to_preload.append(next_page)

        # Precarica le pagine successive se non sono già in cache o in loading
        if self.lazy_loading:
            for page_idx in pages_to_preload:
                if self.image_cache.get(page_idx) is None and page_idx not in self.loading_pages:
                    self.loading_pages.add(page_idx)
                    runnable = ImageLoaderRunnable(page_idx, self.pages_data[page_idx],
                                                   self.current_width, self.image_loader_signals)
                    self.thread_pool.start(runnable)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() != self.current_width: # Only update layout if width changes
            self.update_layout()

class ChapterReaderWindow(QMainWindow):
    def __init__(self, manga_file, chapter_id, parent=None):
        super().__init__(parent)
        self.manga_file = manga_file
        self.chapter_id = chapter_id
        self.db_conn = sqlite3.connect(manga_file)
        self.db_conn.row_factory = sqlite3.Row
        self.setWindowTitle("Lettore Capitolo")
        self.setGeometry(100, 100, 800, 1000) # Default size, will adjust to content
        self.setCursor(Qt.BlankCursor)

        self.scroll_area = QScrollArea(self)
        self.setCentralWidget(self.scroll_area)
        self.scroll_area.setWidgetResizable(True)

        self.page_display_widget = PageDisplayWidget()
        self.scroll_area.setWidget(self.page_display_widget)
        self.scroll_area.verticalScrollBar().setSingleStep(100) # Aumenta la velocità di scorrimento
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.page_display_widget.update)

        QTimer.singleShot(0, self.load_chapter_pages)

    def load_chapter_pages(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT image_data FROM pages WHERE chapter_id = ? ORDER BY page_number", (self.chapter_id,))
        pages = cursor.fetchall()

        image_data_list = [page_data['image_data'] for page_data in pages]
        self.page_display_widget.set_pages_data(image_data_list)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.db_conn:
            self.db_conn.close()
        super().closeEvent(event)


