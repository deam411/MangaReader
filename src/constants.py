"""
Modulo per le costanti centralizzate dell'applicazione.

Questo modulo contiene tutte le costanti utilizzate nell'applicazione,
fornendo un unico punto di riferimento per versioni, limiti, formati e configurazioni.
"""

# Informazioni applicazione
APP_NAME = "Manga Reader"
APP_VERSION = "0.1.0"
APP_AUTHOR = "Alessandro"
APP_DESCRIPTION = "Lettore e gestore di manga desktop multi-piattaforma"

# Formati immagine supportati
SUPPORTED_IMAGE_FORMATS = [
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".webp",
    ".jfif"
]

# Formati immagine che richiedono conversione
CONVERTIBLE_FORMATS = [".webp", ".jfif"]

# Estensione file manga
MANGA_FILE_EXTENSION = ".manga"

# Limiti prestazioni (default)
DEFAULT_CACHE_SIZE = 50  # Numero di immagini in cache
MIN_CACHE_SIZE = 10
MAX_CACHE_SIZE = 200

DEFAULT_PRELOAD_PAGES = 2  # Numero di pagine da precaricare
MIN_PRELOAD_PAGES = 0
MAX_PRELOAD_PAGES = 10

# Zoom reader
DEFAULT_ZOOM_LEVEL = 1.0
MIN_ZOOM_LEVEL = 0.1
MAX_ZOOM_LEVEL = 5.0
ZOOM_STEP = 0.1

# Qualità conversione immagini
IMAGE_CONVERSION_QUALITY = 95  # Per JPEG (0-100)

# Limiti dimensione file
MAX_IMAGE_SIZE_MB = 50  # Dimensione massima file immagine in MB

# Dimensioni thumbnail
THUMBNAIL_WIDTH = 150
THUMBNAIL_HEIGHT = 200

# Dimensioni copertine griglia
GRID_COVER_WIDTH = 150
GRID_COVER_HEIGHT = 200

# Dimensioni copertine delegate (rendering fisso)
DELEGATE_COVER_WIDTH = 250
DELEGATE_COVER_HEIGHT = 375

# Dimensioni separatore capitoli nel reader
CHAPTER_SEPARATOR_WIDTH = 800
CHAPTER_SEPARATOR_HEIGHT = 400

# Dimensioni icone pagine
PAGE_ICON_SIZE = 100

# Dimensioni finestre dialog
DIALOG_MIN_WIDTH = 400
DIALOG_MIN_HEIGHT = 300

# Tag predefiniti per manga
DEFAULT_TAGS = [
    "Azione",
    "Avventura",
    "Commedia",
    "Drama",
    "Fantasy",
    "Horror",
    "Mistero",
    "Romance",
    "Sci-Fi",
    "Slice of Life",
    "Soprannaturale",
    "Sport",
    "Storico",
    "Thriller"
]

# Tema predefinito
DEFAULT_THEME = "system"

# Lingue supportate
SUPPORTED_LANGUAGES = [
    "Italiano",
    "English",
    "Español",
    "Français",
    "Deutsch",
    "日本語",
    "中文",
    "한국어"
]

# Limiti UI
MAX_RECENT_FILES = 10  # Numero massimo di file recenti
COVER_CACHE_MAX = 100  # Numero massimo di cover in cache
GRID_SPACING = 10  # Spaziatura tra gli elementi della griglia (px)
GRID_ITEM_WIDTH = 280  # Larghezza item griglia (px)
GRID_ITEM_HEIGHT = 420  # Altezza item griglia (px)

# Cache e performance
PAGE_CACHE_CAPACITY = 100  # Capacità cache pagine caricate
THREAD_POOL_MAX_THREADS = 4  # Thread massimi per caricamento immagini
THREAD_POOL_MIN_THREADS = 2  # Thread minimi per caricamento immagini
PAGE_SPACING = 10  # Spaziatura tra pagine nel reader (px)
INITIAL_PAGE_COUNT = 5  # Numero di pagine iniziali da caricare velocemente
WINDOW_SIZE = 10  # Numero di pagine da tenere in memoria prima/dopo quella corrente

# Shortcut keyboard default
DEFAULT_SHORTCUTS = {
    "fullscreen": "F11",
    "exit": "Escape",
    "zoom_in": "Up",
    "zoom_out": "Down",
    "next_page": "Right",
    "prev_page": "Left"
}

# Database
DB_SCHEMA_VERSION = 2

# Network (per future feature)
DEFAULT_TIMEOUT = 30  # secondi
MAX_RETRIES = 3

# File logging
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Progress bar update interval (ms)
PROGRESS_UPDATE_INTERVAL = 100
