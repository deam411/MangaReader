"""
Views package - Moduli UI per MangaReader.

Questo package contiene tutti i componenti UI dell'applicazione,
organizzati in moduli logici per migliorare la manutenibilità.

v0.1.0 - Phase 3.1: Split views.py in moduli separati
v0.1.5 - Refactoring completo: views.py → moduli MVC separati
"""

# Import main views
from .library_view import LibraryView
from .manga_view import MangaView
from .volume_view import VolumeView
from .reader_view import ReaderView

# Import widgets
from .widgets import LibraryLoaderThread, DeselectableListWidget, MangaItemDelegate

# Import dialogs
from .dialogs import ArchiveImportDialog, BookmarkDialog, ShortcutsDialog

# Import utilities
from .utils import sanitize_filename, calculate_reading_progress_fast

__all__ = [
    # Main Views
    'LibraryView',
    'MangaView',
    'VolumeView',
    'ReaderView',
    # Widgets
    'LibraryLoaderThread',
    'DeselectableListWidget',
    'MangaItemDelegate',
    # Dialogs
    'ArchiveImportDialog',
    'BookmarkDialog',
    'ShortcutsDialog',
    # Utils
    'sanitize_filename',
    'calculate_reading_progress_fast',
]
