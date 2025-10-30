import sqlite3
from collections import OrderedDict
from PyQt5.QtWidgets import QMainWindow, QScrollArea, QVBoxLayout, QLabel, QWidget
from PyQt5.QtGui import QPainter, QPixmap, QImage, QCursor
from PyQt5.QtCore import Qt, QSize, QTimer, QRect, QRunnable, QThreadPool, pyqtSignal, QObject, QPoint
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

        # Zoom and Pan support
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.is_panning = False
        self.last_pan_point = QPoint()
        self.setMouseTracking(True)

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
        parent_width = self.parent().width() if self.parent() else 800
        self.current_width = int(parent_width * self.zoom_factor)

        if self.current_width <= 0:
            return

        # Calcola l'offset X per centrare le pagine
        scroll_area_width = self.parent().parent().viewport().width() if self.parent() and self.parent().parent() else parent_width
        x_offset = max(0, (scroll_area_width - self.current_width) // 2)

        y_offset = 0
        for i, image_data in enumerate(self.pages_data):
            if image_data:
                # Load a temporary pixmap to get original size for aspect ratio calculation
                temp_image = QImage()
                temp_image.loadFromData(image_data)
                if not temp_image.isNull():
                    original_size = temp_image.size()
                    scaled_height = int(original_size.height() * (self.current_width / original_size.width()))

                    self.page_positions.append(QRect(x_offset, y_offset, self.current_width, scaled_height))
                    y_offset += scaled_height + int(self.page_spacing * self.zoom_factor)
                else:
                    self.page_positions.append(QRect(x_offset, y_offset, self.current_width, 100)) # Placeholder height
                    y_offset += 100 + int(self.page_spacing * self.zoom_factor)
            else:
                self.page_positions.append(QRect(x_offset, y_offset, self.current_width, 100)) # Placeholder height
                y_offset += 100 + int(self.page_spacing * self.zoom_factor)

        self.total_height = y_offset
        # Imposta la larghezza minima alla larghezza della scroll area per permettere il centraggio
        min_width = max(self.current_width, scroll_area_width)
        self.setMinimumSize(min_width, self.total_height)
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

                    # Draw a placeholder while loading - usa nero invece di grigio
                    painter.fillRect(page_rect, Qt.black)
                else:
                    # Image is cached, draw it
                    # Se la dimensione cached non corrisponde, ridimensiona al volo
                    if cached_pixmap.width() != self.current_width:
                        # Ridimensiona temporaneamente mentre ricarica
                        scaled_pixmap = cached_pixmap.scaledToWidth(self.current_width, Qt.SmoothTransformation)
                        painter.drawPixmap(page_rect.topLeft(), scaled_pixmap)

                        # Ricarica in background con la dimensione corretta se non già in loading
                        if i not in self.loading_pages:
                            self.loading_pages.add(i)
                            runnable = ImageLoaderRunnable(i, image_data, self.current_width, self.image_loader_signals)
                            self.thread_pool.start(runnable)
                    else:
                        # Dimensione corretta, disegna normalmente
                        painter.drawPixmap(page_rect.topLeft(), cached_pixmap)

                # Aggiungi pagine successive da precaricare
                for j in range(1, self.preload_pages + 1):
                    next_page = i + j
                    if next_page < len(self.pages_data):
                        pages_to_preload.append(next_page)

        # Precarica le pagine successive se non sono già in cache o in loading
        if self.lazy_loading:
            for page_idx in pages_to_preload:
                cached = self.image_cache.get(page_idx)
                if (cached is None or cached.width() != self.current_width) and page_idx not in self.loading_pages:
                    self.loading_pages.add(page_idx)
                    runnable = ImageLoaderRunnable(page_idx, self.pages_data[page_idx],
                                                   self.current_width, self.image_loader_signals)
                    self.thread_pool.start(runnable)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Aggiorna il layout quando la finestra viene ridimensionata
        self.update_layout()

    def wheelEvent(self, event):
        """Gestisce lo scroll con la rotella del mouse"""
        scroll_area = self.parent().parent()
        if isinstance(scroll_area, QScrollArea):
            # Ottieni il delta dello scroll
            delta = event.angleDelta().y()
            # Applica lo scroll alla scrollbar verticale
            current_value = scroll_area.verticalScrollBar().value()
            scroll_area.verticalScrollBar().setValue(current_value - delta)
        event.accept()

    def keyPressEvent(self, event):
        """Gestisce lo zoom con le frecce su/giù della tastiera"""
        if event.key() == Qt.Key_Up:
            # Freccia su = Zoom in
            zoom_change = 1.1  # Zoom in del 10%
            old_zoom = self.zoom_factor
            self.zoom_factor *= zoom_change

            # Limita lo zoom tra min e max
            self.zoom_factor = max(self.min_zoom, min(self.max_zoom, self.zoom_factor))

            # Se lo zoom è effettivamente cambiato
            if self.zoom_factor != old_zoom:
                # NON svuotare la cache - le immagini vecchie vengono ridimensionate al volo
                # e ricaricate in background

                # Calcola il punto di zoom relativo alla viewport
                scroll_area = self.parent().parent()
                if isinstance(scroll_area, QScrollArea):
                    # Calcola la posizione centrale della viewport
                    viewport_center_y = scroll_area.verticalScrollBar().value() + scroll_area.viewport().height() // 2
                    old_ratio = viewport_center_y / max(1, self.total_height)

                    # Aggiorna il layout con il nuovo zoom
                    self.update_layout()

                    # Mantieni la stessa posizione relativa dopo lo zoom
                    new_pos_y = int(old_ratio * self.total_height - scroll_area.viewport().height() // 2)
                    scroll_area.verticalScrollBar().setValue(new_pos_y)

            event.accept()

        elif event.key() == Qt.Key_Down:
            # Freccia giù = Zoom out
            zoom_change = 0.9  # Zoom out del 10%
            old_zoom = self.zoom_factor
            self.zoom_factor *= zoom_change

            # Limita lo zoom tra min e max
            self.zoom_factor = max(self.min_zoom, min(self.max_zoom, self.zoom_factor))

            # Se lo zoom è effettivamente cambiato
            if self.zoom_factor != old_zoom:
                # NON svuotare la cache - le immagini vecchie vengono ridimensionate al volo
                # e ricaricate in background

                # Calcola il punto di zoom relativo alla viewport
                scroll_area = self.parent().parent()
                if isinstance(scroll_area, QScrollArea):
                    # Calcola la posizione centrale della viewport
                    viewport_center_y = scroll_area.verticalScrollBar().value() + scroll_area.viewport().height() // 2
                    old_ratio = viewport_center_y / max(1, self.total_height)

                    # Aggiorna il layout con il nuovo zoom
                    self.update_layout()

                    # Mantieni la stessa posizione relativa dopo lo zoom
                    new_pos_y = int(old_ratio * self.total_height - scroll_area.viewport().height() // 2)
                    scroll_area.verticalScrollBar().setValue(new_pos_y)

            event.accept()

        else:
            # Altri tasti vengono gestiti normalmente
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Inizia il panning con il mouse"""
        if event.button() == Qt.LeftButton:
            self.is_panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        """Gestisce il panning durante il drag del mouse"""
        if self.is_panning:
            scroll_area = self.parent().parent()
            if isinstance(scroll_area, QScrollArea):
                # Calcola lo spostamento
                delta = event.pos() - self.last_pan_point
                self.last_pan_point = event.pos()

                # Applica lo spostamento alle scrollbar
                scroll_area.horizontalScrollBar().setValue(
                    scroll_area.horizontalScrollBar().value() - delta.x()
                )
                scroll_area.verticalScrollBar().setValue(
                    scroll_area.verticalScrollBar().value() - delta.y()
                )
            event.accept()

    def mouseReleaseEvent(self, event):
        """Termina il panning"""
        if event.button() == Qt.LeftButton:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()

class ChapterReaderWindow(QMainWindow):
    def __init__(self, manga_file, chapter_id, parent=None):
        super().__init__(parent)
        self.manga_file = manga_file
        self.chapter_id = chapter_id
        self.db_conn = sqlite3.connect(manga_file)
        self.db_conn.row_factory = sqlite3.Row
        self.setWindowTitle("Lettore Capitolo")
        self.setGeometry(100, 100, 800, 1000) # Default size, will adjust to content

        self.scroll_area = QScrollArea(self)
        self.setCentralWidget(self.scroll_area)
        self.scroll_area.setWidgetResizable(True)
        # Disabilita la navigazione con le frecce nella scroll area
        self.scroll_area.verticalScrollBar().setFocusPolicy(Qt.NoFocus)
        self.scroll_area.horizontalScrollBar().setFocusPolicy(Qt.NoFocus)

        self.page_display_widget = PageDisplayWidget()
        self.scroll_area.setWidget(self.page_display_widget)
        self.scroll_area.verticalScrollBar().setSingleStep(100) # Aumenta la velocità di scorrimento
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.page_display_widget.update)

        # Installa event filter per intercettare le frecce
        self.scroll_area.installEventFilter(self)

        QTimer.singleShot(0, self.load_chapter_pages)

    def load_chapter_pages(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT image_data FROM pages WHERE chapter_id = ? ORDER BY page_number", (self.chapter_id,))
        pages = cursor.fetchall()

        image_data_list = [page_data['image_data'] for page_data in pages]
        self.page_display_widget.set_pages_data(image_data_list)

    def eventFilter(self, obj, event):
        """Filtra gli eventi per impedire che le frecce scrollino la pagina"""
        from PyQt5.QtCore import QEvent
        if obj == self.scroll_area and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Up, Qt.Key_Down):
                # Blocca l'evento e gestiscilo direttamente per lo zoom
                self.page_display_widget.keyPressEvent(event)
                return True  # Evento consumato, non propagare
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key_Up, Qt.Key_Down):
            # Gestisci lo zoom con le frecce
            self.page_display_widget.keyPressEvent(event)
            event.accept()  # Blocca la propagazione
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.db_conn:
            self.db_conn.close()
        super().closeEvent(event)


