"""
Views package - Moduli UI per MangaReader.

Questo package contiene tutti i componenti UI dell'applicazione,
organizzati in moduli logici per migliorare la manutenibilità.

v0.1.0 - Phase 3.1: Split views.py in moduli separati
"""

# Import dialogs
from .dialogs import ArchiveImportDialog, BookmarkDialog, ShortcutsDialog

# Import utilities
from .utils import sanitize_filename, calculate_reading_progress_fast

__all__ = [
    # Dialogs
    'ArchiveImportDialog',
    'BookmarkDialog',
    'ShortcutsDialog',
    # Utils
    'sanitize_filename',
    'calculate_reading_progress_fast',
]
