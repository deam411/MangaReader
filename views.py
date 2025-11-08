"""
Proxy module for backward compatibility.

v0.1.5: views.py è stato refactorizzato in src/views/ package.
Questo file mantiene la compatibilità con gli import esistenti.
"""

# Re-export everything from src.views
from src.views import (
    # Main Views
    LibraryView,
    MangaView,
    VolumeView,
    ReaderView,
    # Widgets
    LibraryLoaderThread,
    DeselectableListWidget,
    MangaItemDelegate,
    # Dialogs
    ArchiveImportDialog,
    BookmarkDialog,
    ShortcutsDialog,
    # Utils
    sanitize_filename,
    calculate_reading_progress_fast,
)

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
