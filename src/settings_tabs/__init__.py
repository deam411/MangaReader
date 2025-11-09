"""
Settings tabs package per SettingsDialog modulare.

Ogni tab è un widget separato con la sua logica UI e business.

Architettura v0.2.0:
- GeneralTab: Libreria + aggiornamenti
- AppearanceTab: Tema
- PerformanceTab: Cache + preload
- ReaderTab: RTL + doppia pagina + sfondo LIBRARY
- ShortcutsTab: Scorciatoie personalizzabili
- BookmarksTab: Categorie segnalibri
"""

from .general_tab import GeneralTab, UpdateThread
from .appearance_tab import AppearanceTab
from .performance_tab import PerformanceTab
from .reader_tab import ReaderTab
from .shortcuts_tab import ShortcutsTab
from .bookmarks_tab import BookmarksTab
from .backup_tab import BackupTab

__all__ = [
    'GeneralTab',
    'AppearanceTab',
    'PerformanceTab',
    'ReaderTab',
    'ShortcutsTab',
    'BookmarksTab',
    'BackupTab',
    'UpdateThread'
]
