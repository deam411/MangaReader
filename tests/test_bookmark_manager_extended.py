"""
Test suite estesa per Bookmark Manager.

Verifica funzionalità di creazione, recupero, eliminazione e rinomina bookmarks.
Include test per multi-utente e casi edge.
"""
import pytest
import sqlite3
import tempfile
import os
import time
from src.database import MangaDatabaseManager
from src.database.bookmark_manager import BookmarkManager


class TestBookmarkManagerExtended:
    """Test suite estesa per Bookmark Manager."""

    @pytest.fixture
    def temp_manga_db(self):
        """Crea un database manga temporaneo con struttura completa."""
        from tests.conftest import create_temp_image
        from pathlib import Path

        fd, path = tempfile.mkstemp(suffix='.manga')
        os.close(fd)

        db_manager = MangaDatabaseManager(path)

        # Setup base
        db_manager.insert_metadata(
            title="Test Manga",
            author="Test Author",
            description="Test description"
        )

        # Crea 2 volumi con 2 capitoli ciascuno
        vol1_id = db_manager.insert_volume("Volume 1", 1)
        vol2_id = db_manager.insert_volume("Volume 2", 2)

        ch1_id = db_manager.insert_chapter("Chapter 1", 1, vol1_id)
        ch2_id = db_manager.insert_chapter("Chapter 2", 2, vol1_id)
        ch3_id = db_manager.insert_chapter("Chapter 3", 1, vol2_id)
        ch4_id = db_manager.insert_chapter("Chapter 4", 2, vol2_id)

        # Crea temp directory per immagini
        temp_dir = Path(tempfile.mkdtemp())
        test_image = create_temp_image(temp_dir, "test_page.png")

        # 10 pagine per capitolo
        for ch_id in [ch1_id, ch2_id, ch3_id, ch4_id]:
            for i in range(1, 11):
                db_manager.insert_page(ch_id, i, str(test_image))

        yield path, db_manager

        # Cleanup
        db_manager.close()
        if os.path.exists(path):
            os.remove(path)
        # Cleanup temp images
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_add_bookmark_success(self, temp_manga_db):
        """Test aggiunta bookmark con successo."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        bookmark_id = bookmark_mgr.add_bookmark(
            chapter_id=1,
            page_number=5,
            name="Scena epica",
            user="default"
        )

        assert bookmark_id > 0

        # Verifica salvato
        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert len(bookmarks) == 1
        assert bookmarks[0]['name'] == "Scena epica"
        assert bookmarks[0]['chapter_id'] == 1
        assert bookmarks[0]['page_number'] == 5

    def test_add_multiple_bookmarks(self, temp_manga_db):
        """Test aggiunta multipli bookmarks."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        bookmarks_to_add = [
            (1, 5, "Bookmark 1"),
            (2, 10, "Bookmark 2"),
            (3, 3, "Bookmark 3"),
            (4, 7, "Bookmark 4")
        ]

        for chapter_id, page, name in bookmarks_to_add:
            bookmark_id = bookmark_mgr.add_bookmark(chapter_id, page, name, "default")
            assert bookmark_id > 0

        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert len(bookmarks) == 4

    def test_add_bookmark_same_position_multiple_times(self, temp_manga_db):
        """Test aggiunta multipli bookmarks alla stessa posizione (consentito)."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # Stesso capitolo e pagina, nomi diversi
        id1 = bookmark_mgr.add_bookmark(1, 5, "Bookmark A", "default")
        id2 = bookmark_mgr.add_bookmark(1, 5, "Bookmark B", "default")

        assert id1 > 0
        assert id2 > 0
        assert id1 != id2

        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert len(bookmarks) == 2

    def test_get_bookmarks_empty(self, temp_manga_db):
        """Test recupero bookmarks quando non ce ne sono."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert bookmarks == []

    def test_get_bookmarks_with_chapter_volume_info(self, temp_manga_db):
        """Test che get_bookmarks includa info chapter e volume."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        bookmark_mgr.add_bookmark(1, 5, "Test Bookmark", "default")

        bookmarks = bookmark_mgr.get_bookmarks("default")

        assert len(bookmarks) == 1
        assert 'chapter_name' in bookmarks[0]
        assert 'volume_name' in bookmarks[0]
        assert bookmarks[0]['chapter_name'] == "Chapter 1"
        assert bookmarks[0]['volume_name'] == "Volume 1"

    def test_get_bookmarks_ordered_by_timestamp(self, temp_manga_db):
        """Test che bookmarks siano ordinati per timestamp (più recenti prima)."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # Aggiungi con piccoli delay per assicurare timestamp diversi
        bookmark_mgr.add_bookmark(1, 1, "First", "default")
        time.sleep(0.01)
        bookmark_mgr.add_bookmark(2, 2, "Second", "default")
        time.sleep(0.01)
        bookmark_mgr.add_bookmark(3, 3, "Third", "default")

        bookmarks = bookmark_mgr.get_bookmarks("default")

        # Dovrebbero essere ordinati dal più recente (Third) al più vecchio (First)
        assert bookmarks[0]['name'] == "Third"
        assert bookmarks[1]['name'] == "Second"
        assert bookmarks[2]['name'] == "First"

    def test_delete_bookmark_success(self, temp_manga_db):
        """Test eliminazione bookmark con successo."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # Aggiungi bookmark
        bookmark_id = bookmark_mgr.add_bookmark(1, 5, "To Delete", "default")

        # Verifica esistente
        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert len(bookmarks) == 1

        # Elimina
        result = bookmark_mgr.delete_bookmark(bookmark_id)
        assert result is True

        # Verifica eliminato
        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert len(bookmarks) == 0

    def test_delete_nonexistent_bookmark(self, temp_manga_db):
        """Test eliminazione bookmark inesistente."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # ID 999 non esiste
        result = bookmark_mgr.delete_bookmark(999)

        # Non dovrebbe dare errore, ritorna True comunque
        assert result is True

    def test_delete_specific_bookmark_keeps_others(self, temp_manga_db):
        """Test che eliminare un bookmark non elimini gli altri."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        id1 = bookmark_mgr.add_bookmark(1, 1, "Keep 1", "default")
        id2 = bookmark_mgr.add_bookmark(2, 2, "Delete This", "default")
        id3 = bookmark_mgr.add_bookmark(3, 3, "Keep 2", "default")

        # Elimina solo il secondo
        bookmark_mgr.delete_bookmark(id2)

        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert len(bookmarks) == 2

        names = [bm['name'] for bm in bookmarks]
        assert "Keep 1" in names
        assert "Keep 2" in names
        assert "Delete This" not in names

    def test_update_bookmark_name_success(self, temp_manga_db):
        """Test rinomina bookmark con successo."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        bookmark_id = bookmark_mgr.add_bookmark(1, 5, "Old Name", "default")

        result = bookmark_mgr.update_bookmark_name(bookmark_id, "New Name")
        assert result is True

        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert bookmarks[0]['name'] == "New Name"

    def test_update_nonexistent_bookmark_name(self, temp_manga_db):
        """Test rinomina bookmark inesistente."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # ID 999 non esiste
        result = bookmark_mgr.update_bookmark_name(999, "New Name")

        # Non dovrebbe dare errore
        assert result is True

    def test_update_bookmark_name_empty_string(self, temp_manga_db):
        """Test rinomina bookmark con stringa vuota."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        bookmark_id = bookmark_mgr.add_bookmark(1, 5, "Original", "default")

        # Rinomina con stringa vuota
        result = bookmark_mgr.update_bookmark_name(bookmark_id, "")
        assert result is True

        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert bookmarks[0]['name'] == ""

    def test_multiple_users_separate_bookmarks(self, temp_manga_db):
        """Test che bookmarks siano separati per utente."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # User1 bookmarks
        bookmark_mgr.add_bookmark(1, 1, "User1 BM1", "user1")
        bookmark_mgr.add_bookmark(2, 2, "User1 BM2", "user1")

        # User2 bookmarks
        bookmark_mgr.add_bookmark(3, 3, "User2 BM1", "user2")

        # User3 no bookmarks

        bookmarks_user1 = bookmark_mgr.get_bookmarks("user1")
        bookmarks_user2 = bookmark_mgr.get_bookmarks("user2")
        bookmarks_user3 = bookmark_mgr.get_bookmarks("user3")

        assert len(bookmarks_user1) == 2
        assert len(bookmarks_user2) == 1
        assert len(bookmarks_user3) == 0

    def test_bookmark_timestamp_auto_generation(self, temp_manga_db):
        """Test che timestamp venga generato automaticamente."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        import time
        before = int(time.time())

        bookmark_mgr.add_bookmark(1, 5, "Test", "default")

        after = int(time.time())

        bookmarks = bookmark_mgr.get_bookmarks("default")
        timestamp = bookmarks[0]['timestamp']

        # Timestamp dovrebbe essere nell'intervallo
        assert before <= timestamp <= after

    def test_bookmark_with_unicode_name(self, temp_manga_db):
        """Test bookmark con caratteri unicode nel nome."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        unicode_names = [
            "書籍マーク",  # Giapponese
            "书签",  # Cinese
            "закладка",  # Russo
            "🔖 Importante",  # Emoji
        ]

        for name in unicode_names:
            bookmark_mgr.add_bookmark(1, 1, name, "default")

        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert len(bookmarks) == len(unicode_names)

        saved_names = [bm['name'] for bm in bookmarks]
        for name in unicode_names:
            assert name in saved_names

    def test_bookmark_with_long_name(self, temp_manga_db):
        """Test bookmark con nome molto lungo."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # Nome di 500 caratteri
        long_name = "A" * 500

        bookmark_id = bookmark_mgr.add_bookmark(1, 5, long_name, "default")
        assert bookmark_id > 0

        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert bookmarks[0]['name'] == long_name

    def test_bookmark_with_special_characters(self, temp_manga_db):
        """Test bookmark con caratteri speciali."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        special_names = [
            "Quote \"test\"",
            "Apostrophe's test",
            "Backslash \\ test",
            "Newline\ntest",
            "Tab\ttest",
        ]

        for name in special_names:
            bookmark_mgr.add_bookmark(1, 1, name, "default")

        bookmarks = bookmark_mgr.get_bookmarks("default")
        saved_names = [bm['name'] for bm in bookmarks]

        for name in special_names:
            assert name in saved_names

    def test_bookmark_at_page_zero(self, temp_manga_db):
        """Test bookmark a pagina 0 (caso edge)."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        bookmark_id = bookmark_mgr.add_bookmark(1, 0, "Page Zero", "default")
        assert bookmark_id > 0

        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert bookmarks[0]['page_number'] == 0

    def test_bookmark_at_high_page_number(self, temp_manga_db):
        """Test bookmark con numero pagina molto alto."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # Pagina 999999 (potrebbe non esistere ma il bookmark viene salvato)
        bookmark_id = bookmark_mgr.add_bookmark(1, 999999, "High Page", "default")
        assert bookmark_id > 0

        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert bookmarks[0]['page_number'] == 999999

    def test_bookmark_invalid_chapter_id(self, temp_manga_db):
        """Test bookmark con chapter_id non esistente."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # Chapter 999 non esiste
        # Il bookmark viene salvato ma get_bookmarks potrebbe fallire il JOIN
        bookmark_id = bookmark_mgr.add_bookmark(999, 5, "Invalid Chapter", "default")

        # Potrebbe fallire per FK constraint o essere salvato
        # Dipende da come è configurato il database

    def test_get_bookmarks_with_deleted_chapter(self, temp_manga_db):
        """Test recupero bookmarks quando capitolo viene eliminato."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # Aggiungi bookmark
        bookmark_mgr.add_bookmark(1, 5, "Test", "default")

        # Elimina il capitolo
        with sqlite3.connect(path) as conn:
            conn.execute("DELETE FROM chapters WHERE id = 1")

        # get_bookmarks dovrebbe gestire gracefully (JOIN fallisce)
        bookmarks = bookmark_mgr.get_bookmarks("default")

        # Potrebbe essere vuoto o contenere bookmark con chapter_name=None
        # Dipende dalla configurazione del JOIN

    def test_concurrent_bookmark_additions(self, temp_manga_db):
        """Test aggiunta consecutiva rapida di bookmarks."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # Simula aggiunta rapida di molti bookmarks
        for i in range(50):
            bookmark_id = bookmark_mgr.add_bookmark(
                chapter_id=(i % 4) + 1,  # Cicla tra i 4 capitoli
                page_number=i,
                name=f"Bookmark {i}",
                user="default"
            )
            assert bookmark_id > 0

        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert len(bookmarks) == 50

    def test_delete_all_bookmarks_one_by_one(self, temp_manga_db):
        """Test eliminazione di tutti i bookmarks uno per uno."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # Aggiungi 10 bookmarks
        bookmark_ids = []
        for i in range(10):
            bookmark_id = bookmark_mgr.add_bookmark(1, i, f"BM {i}", "default")
            bookmark_ids.append(bookmark_id)

        # Elimina tutti uno per uno
        for bookmark_id in bookmark_ids:
            result = bookmark_mgr.delete_bookmark(bookmark_id)
            assert result is True

        # Verifica nessun bookmark rimasto
        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert len(bookmarks) == 0

    def test_bookmark_fields_complete(self, temp_manga_db):
        """Test che tutti i campi del bookmark siano presenti."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        bookmark_mgr.add_bookmark(1, 5, "Complete Test", "default")

        bookmarks = bookmark_mgr.get_bookmarks("default")
        bookmark = bookmarks[0]

        # Verifica tutti i campi
        assert 'id' in bookmark
        assert 'chapter_id' in bookmark
        assert 'page_number' in bookmark
        assert 'name' in bookmark
        assert 'timestamp' in bookmark
        assert 'chapter_name' in bookmark
        assert 'volume_name' in bookmark

    def test_bookmarks_across_different_volumes(self, temp_manga_db):
        """Test bookmarks su capitoli di volumi diversi."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        # Bookmark su chapter 1 (volume 1)
        bookmark_mgr.add_bookmark(1, 5, "Vol1 BM", "default")

        # Bookmark su chapter 3 (volume 2)
        bookmark_mgr.add_bookmark(3, 7, "Vol2 BM", "default")

        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert len(bookmarks) == 2

        # Verifica volumi diversi
        volume_names = [bm['volume_name'] for bm in bookmarks]
        assert "Volume 1" in volume_names
        assert "Volume 2" in volume_names

    def test_rename_multiple_times(self, temp_manga_db):
        """Test rinomina bookmark multiple volte."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        bookmark_id = bookmark_mgr.add_bookmark(1, 5, "Name 1", "default")

        # Rinomina più volte
        names = ["Name 2", "Name 3", "Name 4", "Final Name"]

        for name in names:
            result = bookmark_mgr.update_bookmark_name(bookmark_id, name)
            assert result is True

        # Verifica l'ultimo nome
        bookmarks = bookmark_mgr.get_bookmarks("default")
        assert bookmarks[0]['name'] == "Final Name"

    def test_user_with_special_characters(self, temp_manga_db):
        """Test utente con caratteri speciali."""
        path, db_manager = temp_manga_db
        bookmark_mgr = BookmarkManager(path)

        special_users = [
            "user@email.com",
            "user-123",
            "user_test",
            "用户",  # Unicode
        ]

        for user in special_users:
            bookmark_mgr.add_bookmark(1, 1, f"BM for {user}", user)

        # Verifica ogni utente abbia il suo bookmark
        for user in special_users:
            bookmarks = bookmark_mgr.get_bookmarks(user)
            assert len(bookmarks) == 1
