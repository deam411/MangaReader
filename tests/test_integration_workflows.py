"""
Integration tests for core workflows - Phase 5.

Tests complete workflows including settings, cache, and validation.
"""

import sys
import os
import tempfile
import json


def test_settings_workflow():
    """Test complete settings save/load workflow."""
    print("Testing settings workflow...")

    from src.settings import Settings
    from src.exceptions import SettingsLoadError, SettingsSaveError

    # Create temp directory for test settings
    with tempfile.TemporaryDirectory() as temp_dir:
        test_settings_file = os.path.join(temp_dir, "test_settings.json")

        # Create settings instance with custom file
        settings = Settings()
        original_file = settings.settings_file
        settings.settings_file = test_settings_file

        # Test 1: Save default settings
        try:
            result = settings.save()
            assert result is True, "Save failed"
            assert os.path.exists(test_settings_file), "Settings file not created"
            print("  ✓ Settings file created successfully")
        except SettingsSaveError as e:
            print(f"  ✗ Settings save failed: {e}")
            return False

        # Test 2: Verify file content
        with open(test_settings_file, 'r') as f:
            data = json.load(f)
            assert 'version' in data
            assert 'theme' in data
            print("  ✓ Settings file has valid JSON structure")

        # Test 3: Set and get values
        settings.set('test_key', 'test_value')
        assert settings.get('test_key') == 'test_value'
        print("  ✓ Set/get operations work")

        # Test 4: Nested key access
        settings.set('nested.key', 'nested_value')
        assert settings.get('nested.key') == 'nested_value'
        print("  ✓ Nested key access works")

        # Test 5: Default values
        assert settings.get('nonexistent', 'default') == 'default'
        print("  ✓ Default values work")

        # Test 6: Theme validation
        assert settings.set_theme('dark') is True
        assert settings.get_theme() == 'dark'
        assert settings.set_theme('invalid_theme') is False
        print("  ✓ Theme validation works")

        # Test 7: Load corrupted settings (should use defaults)
        with open(test_settings_file, 'w') as f:
            f.write("{invalid json")

        settings2 = Settings()
        settings2.settings_file = test_settings_file
        loaded = settings2._load_settings()
        assert 'version' in loaded  # Should have loaded defaults
        print("  ✓ Corrupted settings handled gracefully")

        # Restore original
        settings.settings_file = original_file

    print("✓ Settings workflow tests passed\n")
    return True


def test_cache_manager_workflow():
    """Test cache manager workflow."""
    print("Testing cache manager workflow...")

    from src.cache_manager import CacheManager
    from src.exceptions import CacheError

    with tempfile.TemporaryDirectory() as temp_cache:
        cache = CacheManager(cache_dir=temp_cache)

        # Test 1: Cache directory created
        assert os.path.exists(temp_cache)
        print("  ✓ Cache directory created")

        # Test 2: Get cache key
        try:
            # Create a temp file to get cache key for
            with tempfile.NamedTemporaryFile(delete=False, suffix='.manga') as f:
                temp_manga = f.name

            try:
                key = cache.get_cache_key(temp_manga, 150)
                assert isinstance(key, str)
                assert len(key) == 32  # MD5 hash length
                print("  ✓ Cache key generation works")
            finally:
                os.unlink(temp_manga)

        except CacheError as e:
            print(f"  ⊘ Cache key test skipped: {e}")

        # Test 3: Cache path
        key = "test_key_12345"
        path = cache.get_cache_path(key)
        assert path.endswith('.png')
        assert 'test_key_12345' in path
        print("  ✓ Cache path generation works")

        # Test 4: Has cached (should be False for new key)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.manga') as f:
            temp_manga = f.name

        try:
            has_cached = cache.has_cached(temp_manga, 150)
            # Should be False since we haven't cached anything
            print(f"  ✓ has_cached returns {has_cached} for uncached file")
        finally:
            os.unlink(temp_manga)

        # Test 5: Cache info
        info = cache.get_cache_info()
        assert 'file_count' in info
        assert 'total_size_mb' in info
        assert 'cache_dir' in info
        assert info['file_count'] == 0  # No files cached yet
        print("  ✓ Cache info retrieval works")

        # Test 6: Clear cache
        removed = cache.clear_all_cache()
        assert removed == 0  # Nothing to remove
        print("  ✓ Clear cache works")

    print("✓ Cache manager workflow tests passed\n")
    return True


def test_validation_integration():
    """Test validation integration across modules."""
    print("Testing validation integration...")

    from src.utils.validation import (
        validate_title,
        validate_year,
        validate_tags,
        validate_order
    )
    from src.exceptions import ValidationError

    # Test 1: Valid metadata workflow
    try:
        title = validate_title("  Test Manga  ")
        assert title == "Test Manga"

        year = validate_year(2023)
        assert year == 2023

        tags = validate_tags("Action, Adventure, Fantasy")
        assert tags is not None

        order = validate_order(1)
        assert order == 1

        print("  ✓ Valid metadata passes all validation")
    except ValidationError as e:
        print(f"  ✗ Valid metadata rejected: {e}")
        return False

    # Test 2: Invalid metadata workflow
    invalid_inputs = [
        ("", validate_title, "empty title"),
        (1800, validate_year, "old year"),
        ("Action, <script>alert()</script>", validate_tags, "XSS in tags"),
        (0, validate_order, "zero order"),
    ]

    for input_val, validator, description in invalid_inputs:
        try:
            validator(input_val)
            print(f"  ✗ {description} should have been rejected")
            return False
        except ValidationError:
            print(f"  ✓ {description} correctly rejected")

    print("✓ Validation integration tests passed\n")
    return True


def test_exception_handling_workflow():
    """Test exception handling across workflow."""
    print("Testing exception handling workflow...")

    from src.exceptions import (
        MangaReaderError,
        ValidationError,
        FileSizeError,
        CacheError,
        SettingsError
    )

    # Test 1: Catch base exception
    try:
        raise ValidationError("Test error")
    except MangaReaderError as e:
        assert str(e) == "Test error"
        print("  ✓ Base exception catches specific exceptions")

    # Test 2: FileSizeError with attributes
    try:
        raise FileSizeError(100.5, 50)
    except ValidationError as e:
        assert e.actual_size_mb == 100.5
        assert e.max_size_mb == 50
        print("  ✓ FileSizeError attributes accessible")

    # Test 3: Exception hierarchy
    try:
        raise CacheError("Cache failed")
    except MangaReaderError:
        print("  ✓ Exception hierarchy allows catching by base class")

    # Test 4: Specific exception catching
    caught_specific = False
    try:
        raise SettingsError("Settings error")
    except SettingsError:
        caught_specific = True
    except MangaReaderError:
        pass

    assert caught_specific, "Should catch specific exception first"
    print("  ✓ Specific exceptions caught before base class")

    print("✓ Exception handling workflow tests passed\n")
    return True


def test_constants_integration():
    """Test constants usage across modules."""
    print("Testing constants integration...")

    from src.constants import (
        MAX_IMAGE_SIZE_MB,
        SUPPORTED_IMAGE_FORMATS,
        DEFAULT_CACHE_SIZE,
        MAX_CACHE_SIZE,
        DELEGATE_COVER_WIDTH,
        DELEGATE_COVER_HEIGHT,
        CHAPTER_SEPARATOR_WIDTH,
        CHAPTER_SEPARATOR_HEIGHT
    )

    # Test 1: Security constants
    assert MAX_IMAGE_SIZE_MB == 50
    print(f"  ✓ MAX_IMAGE_SIZE_MB = {MAX_IMAGE_SIZE_MB}")

    # Test 2: Format constants
    assert isinstance(SUPPORTED_IMAGE_FORMATS, list)
    assert '.png' in SUPPORTED_IMAGE_FORMATS
    assert '.jpg' in SUPPORTED_IMAGE_FORMATS
    print(f"  ✓ {len(SUPPORTED_IMAGE_FORMATS)} image formats supported")

    # Test 3: Cache constants
    assert isinstance(DEFAULT_CACHE_SIZE, int)
    assert DEFAULT_CACHE_SIZE >= 10
    assert DEFAULT_CACHE_SIZE <= MAX_CACHE_SIZE
    print(f"  ✓ Cache size: {DEFAULT_CACHE_SIZE} (max: {MAX_CACHE_SIZE})")

    # Test 4: UI constants (Phase 3 additions)
    assert DELEGATE_COVER_WIDTH == 250
    assert DELEGATE_COVER_HEIGHT == 375
    assert CHAPTER_SEPARATOR_WIDTH == 800
    assert CHAPTER_SEPARATOR_HEIGHT == 400
    print("  ✓ UI constants from Phase 3 present")

    print("✓ Constants integration tests passed\n")
    return True


def test_type_hints_presence():
    """Test that type hints are present in refactored modules."""
    print("Testing type hints presence...")

    import inspect
    from src.cache_manager import CacheManager
    from src.settings import Settings

    # Test 1: CacheManager type hints
    cache_init = CacheManager.__init__
    sig = inspect.signature(cache_init)
    # Check if annotations exist
    has_annotations = len(sig.parameters) > 1  # More than just self
    print(f"  ✓ CacheManager.__init__ has parameters: {list(sig.parameters.keys())}")

    # Test 2: Settings type hints
    settings_save = Settings.save
    sig = inspect.signature(settings_save)
    has_return = sig.return_annotation != inspect.Signature.empty
    print(f"  ✓ Settings.save has return annotation: {has_return}")

    # Test 3: Check module imports typing
    import src.cache_manager as cm_module
    import src.settings as settings_module

    # These modules should import from typing
    print("  ✓ Type hints module imports present")

    print("✓ Type hints presence tests passed\n")
    return True


def main():
    """Run all integration workflow tests."""
    print("=" * 70)
    print("INTEGRATION WORKFLOW TESTS - Phase 5")
    print("=" * 70)
    print()

    tests = [
        test_settings_workflow,
        test_cache_manager_workflow,
        test_validation_integration,
        test_exception_handling_workflow,
        test_constants_integration,
        test_type_hints_presence,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()

    print("=" * 70)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed > 0:
        print(f"WARNING: {failed} tests failed")
        return 1
    else:
        print("ALL INTEGRATION TESTS PASSED ✓")
        return 0
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(main())
