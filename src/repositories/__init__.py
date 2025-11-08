"""
Repositories package per MangaReader v0.2.0.

Pattern repository per separare business logic da data access:
- MangaRepository: Metadata e cover operations
- ChapterRepository: Volumes, chapters, pages operations + navigation
- BookmarkRepository: Bookmarks e reading history

Usage Example:
    from src.repositories import MangaRepository, ChapterRepository, BookmarkRepository

    # Metadata operations
    with MangaRepository(manga_file) as repo:
        metadata = repo.get_metadata()
        repo.update_metadata(title="New Title")

    # Chapter navigation
    with ChapterRepository(manga_file) as repo:
        volumes = repo.get_all_volumes()
        next_chapter = repo.get_next_chapter(current_id)

    # Reading progress
    with BookmarkRepository(manga_file) as repo:
        repo.save_reading_position(chapter_id=1, page_number=15)
        progress = repo.get_reading_progress()
"""

from .base_repository import BaseRepository
from .manga_repository import MangaRepository
from .chapter_repository import ChapterRepository
from .bookmark_repository import BookmarkRepository

__all__ = [
    'BaseRepository',
    'MangaRepository',
    'ChapterRepository',
    'BookmarkRepository'
]
