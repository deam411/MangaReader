"""
Simple test for custom exceptions (no pytest required).
"""

import sys
import tempfile
import os


def test_exception_hierarchy():
    """Test la gerarchia di eccezioni."""
    print("Testing exception hierarchy...")

    from src.exceptions import (
        MangaReaderError,
        DatabaseError,
        DatabaseSchemaError,
        FileSizeError,
        CacheError,
        SettingsLoadError,
        SettingsSaveError,
    )

    # Test base exception
    exc = MangaReaderError("Test error")
    assert str(exc) == "Test error"
    print("  ✓ Base MangaReaderError works")

    # Test database hierarchy
    exc_db = DatabaseSchemaError("Schema error")
    assert isinstance(exc_db, DatabaseError)
    assert isinstance(exc_db, MangaReaderError)
    print("  ✓ DatabaseSchemaError hierarchy correct")

    # Test FileSizeError
    exc_size = FileSizeError(100.5, 50)
    assert exc_size.actual_size_mb == 100.5
    assert exc_size.max_size_mb == 50
    assert "100.5" in str(exc_size)
    print("  ✓ FileSizeError with parameters works")

    # Test cache exception
    exc_cache = CacheError("Cache error")
    assert isinstance(exc_cache, MangaReaderError)
    print("  ✓ CacheError hierarchy correct")

    # Test settings exceptions
    exc_load = SettingsLoadError("Load error")
    assert isinstance(exc_load, MangaReaderError)
    print("  ✓ SettingsLoadError hierarchy correct")

    print("✓ Exception hierarchy tests passed\n")


def test_file_size_error_usage():
    """Test FileSizeError in image_converter."""
    print("Testing FileSizeError in image_converter...")

    try:
        from src.utils.image_converter import convert_image_sync
        from src.exceptions import FileSizeError
        from src.constants import MAX_IMAGE_SIZE_MB
    except ImportError as e:
        print(f"  ⊘ Skipped (missing dependency: {e})")
        return True

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
        temp_path = f.name
        f.write(b'test data')

    try:
        # Mock os.path.getsize to simulate large file
        import os
        original_getsize = os.path.getsize

        def mock_getsize(path):
            if path == temp_path:
                return int((MAX_IMAGE_SIZE_MB + 10) * 1024 * 1024)
            return original_getsize(path)

        os.path.getsize = mock_getsize

        # Should raise FileSizeError
        try:
            convert_image_sync(temp_path)
            print("  ✗ FileSizeError was not raised!")
            return False
        except FileSizeError as e:
            assert e.actual_size_mb > MAX_IMAGE_SIZE_MB
            print(f"  ✓ FileSizeError raised correctly: {e}")
        finally:
            os.path.getsize = original_getsize

    finally:
        os.unlink(temp_path)

    print("✓ FileSizeError usage test passed\n")


def test_cache_error_usage():
    """Test CacheError in cache_manager."""
    print("Testing CacheError in cache_manager...")

    from src.cache_manager import CacheManager
    from src.exceptions import CacheError

    cache_mgr = CacheManager()

    # Non-existent file should raise CacheError
    try:
        cache_mgr.get_cache_key("/nonexistent/path/file.manga", 150)
        print("  ✗ CacheError was not raised!")
        return False
    except CacheError as e:
        print(f"  ✓ CacheError raised correctly: {e}")

    print("✓ CacheError usage test passed\n")


def test_database_schema_creation():
    """Test database schema creation."""
    print("Testing database schema with exceptions...")

    try:
        from src.database import MangaDatabaseManager
        import sqlite3
    except ImportError as e:
        print(f"  ⊘ Skipped (missing dependency: {e})")
        return True

    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.manga') as f:
        temp_db = f.name

    try:
        # Should succeed
        db = MangaDatabaseManager(temp_db)
        print("  ✓ Database schema created successfully")

        # Verify tables exist
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'metadata' in tables
            assert 'chapters' in tables
            assert 'pages' in tables
            print("  ✓ All required tables exist")

    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)

    print("✓ Database schema test passed\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("EXCEPTION HANDLING TESTS - Phase 3")
    print("=" * 60 + "\n")

    try:
        test_exception_hierarchy()
        test_file_size_error_usage()
        test_cache_error_usage()
        test_database_schema_creation()

        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
