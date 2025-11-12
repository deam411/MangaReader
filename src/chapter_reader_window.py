import sqlite3
from collections import OrderedDict
from PyQt5.QtWidgets import QMainWindow, QScrollArea, QVBoxLayout, QLabel, QWidget
from PyQt5.QtGui import QPainter, QPixmap, QImage, QCursor
from PyQt5.QtCore import Qt, QSize, QTimer, QRect, QRunnable, QThreadPool, pyqtSignal, QObject, QPoint
from .settings import Settings
from .constants import (
    PAGE_CACHE_CAPACITY,
    THREAD_POOL_MAX_THREADS,
    THREAD_POOL_MIN_THREADS,
    PAGE_SPACING,
    INITIAL_PAGE_COUNT,
    WINDOW_SIZE,
    CHAPTER_SEPARATOR_WIDTH,
    CHAPTER_SEPARATOR_HEIGHT,
    BLUE_LIGHT_FILTER_COLOR,
    BLUE_LIGHT_FILTER_OPACITY
)

class LRUCache:
    """
    Cache LRU (Least Recently Used) per le immagini con statistiche.

    Traccia hits/misses per monitorare performance.
    """
    def __init__(self, capacity=50):
        self.cache = OrderedDict()
        self.capacity = capacity
        # Statistiche performance
        self.hits = 0
        self.misses = 0

    def get(self, key):
        if key not in self.cache:
            self.misses += 1
            return None
        # Sposta l'elemento alla fine (più recente)
        self.cache.move_to_end(key)
        self.hits += 1
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
        # Reset statistiche quando cache viene svuotata
        self.hits = 0
        self.misses = 0

    def get_stats(self):
        """
        Restituisce statistiche cache.

        Returns:
            Dict con hits, misses, size, capacity, hit_rate
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'size': len(self.cache),
            'capacity': self.capacity,
            'usage': (len(self.cache) / self.capacity * 100) if self.capacity > 0 else 0.0
        }

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

        self.pages_data = [] # List of image_data (legacy)
        self.page_metadata = [] # List of metadata for on-demand loading
        self.db_conn = None  # Database connection for on-demand loading
        self.loaded_pages_cache = LRUCache(capacity=PAGE_CACHE_CAPACITY)  # Cache LRU per i dati raw delle pagine
        self.image_cache = LRUCache(capacity=cache_size)  # Cache LRU per i pixmap
        self.page_positions = [] # List of (x, y, width, height) for each page
        self.total_height = 0
        self.current_width = 0
        self.page_spacing = PAGE_SPACING  # Spaziatura tra pagine
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(THREAD_POOL_MAX_THREADS)  # Limita thread concorrenti
        self.image_loader_signals = ImageLoaderSignals()
        self.image_loader_signals.image_loaded.connect(self.handle_image_loaded)
        self.loading_pages = set()  # Traccia le pagine in caricamento
        self.window_size = WINDOW_SIZE  # Numero di pagine da tenere in memoria prima/dopo quella corrente
        self.initial_pages_loaded = 0  # Contatore per le prime pagine
        self.initial_page_count = INITIAL_PAGE_COUNT  # Numero di pagine iniziali da caricare velocemente
        self._is_loading = False  # Flag per prevenire race condition durante caricamento capitoli

        # Zoom and Pan support
        self.zoom_factor = settings.get("reader.zoom_level", 1.0) # Carica lo zoom globale
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.is_panning = False
        self.last_pan_point = QPoint()
        self.setMouseTracking(True)

        # Reading direction and view mode
        self.reading_direction = settings.get("reader.reading_direction", "ltr")
        self.view_mode = settings.get("reader.view_mode", "single")  # "single" o "double"

        # Blue light filter (night mode)
        self.blue_light_filter_enabled = settings.get("reader.blue_light_filter", False)

        # Abilita il focus per ricevere eventi tastiera
        self.setFocusPolicy(Qt.StrongFocus)

        # Nascondi il cursore durante la lettura
        self.setCursor(Qt.BlankCursor)

    def handle_image_loaded(self, page_index, pixmap):
        # Ignora eventi se siamo in fase di loading di un nuovo capitolo
        if self._is_loading:
            return

        num_pages = len(self.page_metadata) if self.page_metadata else len(self.pages_data)
        if 0 <= page_index < num_pages:
            self.image_cache.put(page_index, pixmap)  # Salva nella cache LRU
            self.loading_pages.discard(page_index)  # Rimuovi dal set di loading

            # Conta le prime pagine caricate
            if page_index < self.initial_page_count:
                self.initial_pages_loaded += 1

                # Dopo le prime pagine iniziali, riduci i thread per risparmiare risorse
                if self.initial_pages_loaded >= self.initial_page_count:
                    self.thread_pool.setMaxThreadCount(THREAD_POOL_MIN_THREADS)  # Riduci thread

            self.update() # Request repaint

    def set_view_mode(self, mode):
        """Cambia la modalità di visualizzazione (single/double)."""
        if mode in ["single", "double"]:
            self.view_mode = mode
            # Salva la preferenza
            settings = Settings()
            settings.set("reader.view_mode", mode)
            # Aggiorna il layout
            self.update_layout()
            return True
        return False

    def toggle_view_mode(self):
        """Alterna tra modalità singola e doppia pagina."""
        new_mode = "double" if self.view_mode == "single" else "single"
        self.set_view_mode(new_mode)
        return new_mode

    def toggle_blue_light_filter(self):
        """Alterna il filtro luce blu (modalità lettura notturna)."""
        self.blue_light_filter_enabled = not self.blue_light_filter_enabled
        settings = Settings()
        settings.set("reader.blue_light_filter", self.blue_light_filter_enabled)
        self.update()  # Ridisegna con/senza filtro
        return self.blue_light_filter_enabled

    def set_pages_metadata(self, metadata_list, db_conn):
        """Imposta i metadati delle pagine per caricamento on-demand."""
        # Fix: Imposta flag loading per prevenire race condition
        self._is_loading = True

        try:
            # Attendi che tutti i thread precedenti finiscano
            self.thread_pool.waitForDone()

            # Se RTL, inverti l'ordine delle pagine
            if self.reading_direction == "rtl":
                self.page_metadata = list(reversed(metadata_list))
            else:
                self.page_metadata = metadata_list

            self.db_conn = db_conn
            self.loaded_pages_cache.clear()
            self.image_cache.clear()
            self.loading_pages.clear()
            self.initial_pages_loaded = 0  # Reset contatore
            self.thread_pool.setMaxThreadCount(THREAD_POOL_MAX_THREADS)  # Reset thread per le prime pagine
            self.update_layout()
            self.setFocus()

            # Carica immediatamente le prime 5 pagine
            self.preload_initial_pages()
        finally:
            # Rilascia flag loading
            self._is_loading = False

    def set_pages_data(self, pages_data_list):
        """Legacy method - carica tutte le pagine in memoria."""
        # Fix: Imposta flag loading per prevenire race condition
        self._is_loading = True

        try:
            # Attendi che tutti i thread precedenti finiscano
            self.thread_pool.waitForDone()

            self.pages_data = pages_data_list
            self.page_metadata = []  # Disabilita caricamento on-demand
            self.image_cache.clear()
            self.loading_pages.clear()
            self.update_layout()
            self.setFocus()
        finally:
            # Rilascia flag loading
            self._is_loading = False

    def get_page_data(self, page_index):
        """Ottiene i dati di una pagina, caricandoli dal DB se necessario."""
        # Legacy mode: tutte le pagine già in memoria
        if not self.page_metadata and page_index < len(self.pages_data):
            return self.pages_data[page_index]

        # On-demand mode
        if page_index >= len(self.page_metadata):
            return None

        # Controlla se è già in cache
        cached_data = self.loaded_pages_cache.get(page_index)
        if cached_data is not None:
            return cached_data

        # Carica dal database
        metadata = self.page_metadata[page_index]

        if metadata['type'] == 'separator':
            # Genera il separatore (dimensioni da constants)
            from PyQt5.QtGui import QImage, QPainter, QFont, QColor
            from PyQt5.QtCore import QBuffer, QByteArray, QIODevice

            image = QImage(CHAPTER_SEPARATOR_WIDTH, CHAPTER_SEPARATOR_HEIGHT, QImage.Format_RGB32)
            image.fill(QColor(40, 40, 40))

            painter = QPainter(image)
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Arial", 32, QFont.Bold)
            painter.setFont(font)
            painter.drawText(image.rect(), Qt.AlignCenter, metadata['chapter_name'])
            painter.end()

            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.WriteOnly)
            image.save(buffer, "PNG")
            buffer.close()

            data = byte_array.data()
            self.loaded_pages_cache.put(page_index, data)
            return data

        elif metadata['type'] == 'page':
            # Carica dal database
            if self.db_conn:
                cursor = self.db_conn.cursor()
                cursor.execute(
                    "SELECT image_data FROM pages WHERE chapter_id = ? AND page_number = ?",
                    (metadata['chapter_id'], metadata['page_number'])
                )
                result = cursor.fetchone()
                if result:
                    data = result['image_data']
                    self.loaded_pages_cache.put(page_index, data)
                    return data

        return None

    def preload_initial_pages(self):
        """Carica immediatamente le prime pagine per visualizzazione rapida."""
        num_pages = len(self.page_metadata) if self.page_metadata else len(self.pages_data)
        pages_to_load = min(self.initial_page_count, num_pages)

        for i in range(pages_to_load):
            if i not in self.loading_pages:
                image_data = self.get_page_data(i)
                if image_data:
                    self.loading_pages.add(i)
                    runnable = ImageLoaderRunnable(i, image_data, self.current_width, self.image_loader_signals)
                    self.thread_pool.start(runnable)

    def cleanup_distant_pages(self, current_page):
        """Rimuove dalla cache le pagine lontane dalla posizione corrente.
        Nota: Con LRUCache questo metodo è meno critico, ma mantiene la logica di window."""
        # LRUCache gestisce automaticamente la rimozione, ma possiamo ancora
        # fare cleanup esplicito per rispettare la window size
        # Nota: LRUCache.cache è un OrderedDict, possiamo accedere alle chiavi
        if hasattr(self.loaded_pages_cache, 'cache'):
            pages_to_remove = []
            for page_idx in list(self.loaded_pages_cache.cache.keys()):
                if abs(page_idx - current_page) > self.window_size:
                    pages_to_remove.append(page_idx)

            for page_idx in pages_to_remove:
                if page_idx in self.loaded_pages_cache.cache:
                    del self.loaded_pages_cache.cache[page_idx]

    def update_layout(self):
        self.page_positions = []
        self.total_height = 0
        parent_width = self.parent().width() if self.parent() else 800
        scroll_area_width = self.parent().parent().viewport().width() if self.parent() and self.parent().parent() else parent_width

        if self.view_mode == "single":
            self._update_layout_single(parent_width, scroll_area_width)
        else:
            self._update_layout_double(parent_width, scroll_area_width)

    def _update_layout_single(self, parent_width, scroll_area_width):
        """Layout per vista singola pagina (verticale)."""
        self.current_width = int(parent_width * self.zoom_factor)

        if self.current_width <= 0:
            return

        # Calcola l'offset X per centrare le pagine
        x_offset = max(0, (scroll_area_width - self.current_width) // 2)

        # Determina il numero di pagine
        num_pages = len(self.page_metadata) if self.page_metadata else len(self.pages_data)

        y_offset = 0
        for i in range(num_pages):
            # Carica solo la prima pagina per determinare le dimensioni
            # Le altre pagine assumono dimensioni standard
            if i == 0 or self.loaded_pages_cache.get(i) is not None:
                image_data = self.get_page_data(i)
                if image_data:
                    temp_image = QImage()
                    temp_image.loadFromData(image_data)
                    if not temp_image.isNull():
                        original_size = temp_image.size()
                        scaled_height = int(original_size.height() * (self.current_width / original_size.width()))

                        self.page_positions.append(QRect(x_offset, y_offset, self.current_width, scaled_height))
                        y_offset += scaled_height + int(self.page_spacing * self.zoom_factor)
                        continue

            # Placeholder per pagine non caricate (usa dimensioni standard manga)
            standard_height = int(self.current_width * 1.4)  # Ratio tipico manga
            self.page_positions.append(QRect(x_offset, y_offset, self.current_width, standard_height))
            y_offset += standard_height + int(self.page_spacing * self.zoom_factor)

        self.total_height = y_offset
        # Imposta la larghezza minima alla larghezza della scroll area per permettere il centraggio
        min_width = max(self.current_width, scroll_area_width)
        self.setMinimumSize(min_width, self.total_height)
        self.update() # Request a repaint

    def _update_layout_double(self, parent_width, scroll_area_width):
        """Layout per vista doppia pagina (side-by-side)."""
        # In modalità doppia, ogni pagina occupa metà larghezza (meno spacing)
        page_width = int((parent_width * self.zoom_factor) / 2) - int(self.page_spacing * self.zoom_factor)
        self.current_width = page_width

        if self.current_width <= 0:
            return

        # Larghezza totale per due pagine
        total_double_width = page_width * 2 + int(self.page_spacing * self.zoom_factor)

        # Calcola l'offset X per centrare le due pagine
        x_offset_base = max(0, (scroll_area_width - total_double_width) // 2)

        # Determina il numero di pagine
        num_pages = len(self.page_metadata) if self.page_metadata else len(self.pages_data)

        y_offset = 0
        i = 0

        while i < num_pages:
            # Controlla se la pagina corrente è un separatore
            metadata = None
            if self.page_metadata and i < len(self.page_metadata):
                metadata = self.page_metadata[i]

            is_separator = metadata and metadata.get('type') == 'separator'

            if is_separator:
                # Separatore occupa l'intera larghezza
                separator_height = int(400 * self.zoom_factor)
                x_offset = x_offset_base
                self.page_positions.append(QRect(x_offset, y_offset, total_double_width, separator_height))
                y_offset += separator_height + int(self.page_spacing * self.zoom_factor)
                i += 1
                continue

            # Pagine normali - side by side
            # Determina posizioni per pagina sinistra e destra (o destra e sinistra se RTL)
            if self.reading_direction == "rtl":
                # RTL: prima pagina a destra, seconda a sinistra
                left_page_idx = i + 1 if i + 1 < num_pages else None
                right_page_idx = i
            else:
                # LTR: prima pagina a sinistra, seconda a destra
                left_page_idx = i
                right_page_idx = i + 1 if i + 1 < num_pages else None

            # Ottieni altezze delle pagine
            left_height = self._get_page_height(left_page_idx, page_width) if left_page_idx is not None else 0
            right_height = self._get_page_height(right_page_idx, page_width) if right_page_idx is not None else 0

            # Usa l'altezza massima tra le due pagine
            max_height = max(left_height, right_height)

            if max_height == 0:
                max_height = int(page_width * 1.4)  # Fallback

            # Crea posizioni per entrambe le pagine
            # Importante: aggiungiamo nell'ordine originale delle pagine
            if self.reading_direction == "rtl":
                # RTL: aggiungi prima right (indice i), poi left (indice i+1)
                x_right = x_offset_base + page_width + int(self.page_spacing * self.zoom_factor)
                self.page_positions.append(QRect(x_right, y_offset, page_width, max_height))
                if left_page_idx is not None:
                    x_left = x_offset_base
                    self.page_positions.append(QRect(x_left, y_offset, page_width, max_height))
            else:
                # LTR: aggiungi prima left (indice i), poi right (indice i+1)
                x_left = x_offset_base
                self.page_positions.append(QRect(x_left, y_offset, page_width, max_height))
                if right_page_idx is not None:
                    x_right = x_offset_base + page_width + int(self.page_spacing * self.zoom_factor)
                    self.page_positions.append(QRect(x_right, y_offset, page_width, max_height))

            y_offset += max_height + int(self.page_spacing * self.zoom_factor)

            # Avanza di 2 pagine (o 1 se è l'ultima)
            if right_page_idx is not None:
                i += 2
            else:
                i += 1

        self.total_height = y_offset
        min_width = max(total_double_width, scroll_area_width)
        self.setMinimumSize(min_width, self.total_height)
        self.update()

    def _get_page_height(self, page_idx, target_width):
        """Calcola l'altezza di una pagina dato un target width."""
        if page_idx is None or page_idx >= (len(self.page_metadata) if self.page_metadata else len(self.pages_data)):
            return 0

        # Controlla se è un separatore
        if self.page_metadata and page_idx < len(self.page_metadata):
            metadata = self.page_metadata[page_idx]
            if metadata.get('type') == 'separator':
                return int(400 * self.zoom_factor)

        # Prova a caricare i dati dell'immagine per ottenere dimensioni reali
        if page_idx == 0 or self.loaded_pages_cache.get(page_idx) is not None:
            image_data = self.get_page_data(page_idx)
            if image_data:
                temp_image = QImage()
                temp_image.loadFromData(image_data)
                if not temp_image.isNull():
                    original_size = temp_image.size()
                    return int(original_size.height() * (target_width / original_size.width()))

        # Usa dimensioni standard se non disponibili
        return int(target_width * 1.4)  # Ratio tipico manga

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)

        visible_rect = event.rect()
        num_pages = len(self.page_metadata) if self.page_metadata else len(self.pages_data)

        # Trova la pagina corrente visibile per il cleanup
        current_page = -1
        for i in range(num_pages):
            if i >= len(self.page_positions):
                continue
            page_rect = self.page_positions[i]
            if page_rect.intersects(visible_rect):
                current_page = i
                break

        # Cleanup delle pagine lontane (solo in modalità on-demand)
        if self.page_metadata and current_page >= 0:
            self.cleanup_distant_pages(current_page)

        # Lista delle pagine da precaricare
        pages_to_preload = []

        for i in range(num_pages):
            if i >= len(self.page_positions):
                continue

            page_rect = self.page_positions[i]

            if page_rect.intersects(visible_rect):
                cached_pixmap = self.image_cache.get(i)

                if cached_pixmap is None:
                    # Image not in cache
                    if i not in self.loading_pages:
                        # Carica i dati della pagina on-demand
                        image_data = self.get_page_data(i)
                        if image_data:
                            self.loading_pages.add(i)
                            runnable = ImageLoaderRunnable(i, image_data, self.current_width, self.image_loader_signals)
                            self.thread_pool.start(runnable)

                    # Mostra placeholder con messaggio "Caricamento..."
                    painter.fillRect(page_rect, Qt.black)
                    from PyQt5.QtGui import QFont, QColor
                    painter.setPen(QColor(150, 150, 150))
                    font = QFont("Arial", 16)
                    painter.setFont(font)
                    painter.drawText(page_rect, Qt.AlignCenter, "Caricamento...")
                else:
                    if cached_pixmap.width() != self.current_width:
                        scaled_pixmap = cached_pixmap.scaledToWidth(self.current_width, Qt.SmoothTransformation)
                        painter.drawPixmap(page_rect.topLeft(), scaled_pixmap)

                        if i not in self.loading_pages:
                            image_data = self.get_page_data(i)
                            if image_data:
                                self.loading_pages.add(i)
                                runnable = ImageLoaderRunnable(i, image_data, self.current_width, self.image_loader_signals)
                                self.thread_pool.start(runnable)
                    else:
                        painter.drawPixmap(page_rect.topLeft(), cached_pixmap)

                # Aggiungi pagine successive da precaricare
                for j in range(1, self.preload_pages + 1):
                    next_page = i + j
                    if next_page < num_pages:
                        pages_to_preload.append(next_page)

        # Precarica le pagine successive
        if self.lazy_loading:
            for page_idx in pages_to_preload:
                cached = self.image_cache.get(page_idx)
                if (cached is None or cached.width() != self.current_width) and page_idx not in self.loading_pages:
                    image_data = self.get_page_data(page_idx)
                    if image_data:
                        self.loading_pages.add(page_idx)
                        runnable = ImageLoaderRunnable(page_idx, image_data, self.current_width, self.image_loader_signals)
                        self.thread_pool.start(runnable)

        # Applica filtro luce blu se attivo (night mode)
        if self.blue_light_filter_enabled:
            from PyQt5.QtGui import QColor
            filter_color = QColor(*BLUE_LIGHT_FILTER_COLOR)
            filter_color.setAlpha(int(BLUE_LIGHT_FILTER_OPACITY * 255 / 100))
            painter.fillRect(self.rect(), filter_color)

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
        old_zoom = self.zoom_factor
        zoom_changed = False

        if event.key() == Qt.Key_Up:
            # Freccia su = Zoom in
            self.zoom_factor *= 1.1  # Zoom in del 10%
            zoom_changed = True

        elif event.key() == Qt.Key_Down:
            # Freccia giù = Zoom out
            self.zoom_factor *= 0.9  # Zoom out del 10%
            zoom_changed = True

        if zoom_changed:
            # Limita lo zoom tra min e max
            self.zoom_factor = max(self.min_zoom, min(self.max_zoom, self.zoom_factor))

            # Se lo zoom è effettivamente cambiato
            if self.zoom_factor != old_zoom:
                # Salva il nuovo zoom nelle impostazioni globali
                settings = Settings()
                settings.set("reader.zoom_level", self.zoom_factor)

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
            # Assicura che il widget abbia il focus per lo zoom con tastiera
            self.setFocus()
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
            self.setCursor(Qt.BlankCursor)  # Nascondi di nuovo il cursore
            event.accept()

    def cleanup(self):
        """Pulisce le risorse del widget."""
        # Attendi che tutti i thread finiscano
        if hasattr(self, 'thread_pool'):
            self.thread_pool.waitForDone(msecs=5000)  # Timeout di 5 secondi
            self.thread_pool.clear()
        # Pulisci le cache
        if hasattr(self, 'image_cache'):
            self.image_cache.clear()
        if hasattr(self, 'loaded_pages_cache'):
            self.loaded_pages_cache.clear()

    def closeEvent(self, event):
        """Cleanup quando il widget viene chiuso."""
        self.cleanup()
        super().closeEvent(event)

    def hideEvent(self, event):
        """Cleanup quando il widget viene nascosto."""
        # Ferma i thread in background quando il widget è nascosto
        if hasattr(self, 'thread_pool'):
            self.thread_pool.waitForDone(msecs=1000)  # Timeout breve
        super().hideEvent(event)

class ChapterReaderWindow(QMainWindow):
    def __init__(self, manga_file, chapter_id, parent=None):
        super().__init__(parent)
        self.manga_file = manga_file
        self.chapter_id = chapter_id
        self.db_conn = sqlite3.connect(manga_file)
        self.db_conn.row_factory = sqlite3.Row
        self.setWindowTitle("Lettore Capitolo")
        self.setGeometry(100, 100, 800, 1000)

        self.scroll_area = QScrollArea(self)
        self.setCentralWidget(self.scroll_area)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.verticalScrollBar().setFocusPolicy(Qt.NoFocus)
        self.scroll_area.horizontalScrollBar().setFocusPolicy(Qt.NoFocus)

        self.page_display_widget = PageDisplayWidget()
        self.scroll_area.setWidget(self.page_display_widget)
        self.scroll_area.verticalScrollBar().setSingleStep(100)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.page_display_widget.update)

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


