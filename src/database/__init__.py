"""
Database package per MangaReader.

Architettura modulare con manager specializzati:
- DatabaseConnection: Schema, indici, ottimizzazioni
- MetadataManager: Metadata manga CRUD
- ChapterManager: Volumes, chapters, pages CRUD
- BookmarkManager: Bookmarks CRUD
- HistoryManager: Reading history e progress
- BaseManager: Funzionalità comuni

Backward Compatibility:
- MangaDatabaseManager: Facade che mantiene API originale
"""

from .base_manager import BaseManager
from .connection import DatabaseConnection
from .metadata_manager import MetadataManager
from .chapter_manager import ChapterManager
from .bookmark_manager import BookmarkManager
from .history_manager import HistoryManager

__all__ = [
    'BaseManager',
    'DatabaseConnection',
    'MetadataManager',
    'ChapterManager',
    'BookmarkManager',
    'HistoryManager'
]
