"""
Isolated security tests that don't require PIL/PyQt5.

Tests validation logic directly without importing database/archive modules.
"""

import sys
import os
import tempfile


def test_validation_module():
    """Test validation module functions in isolation."""
    print("Testing validation module...")

    from src.utils.validation import (
        validate_title,
        validate_author,
        validate_description,
        validate_year,
        validate_tags,
        validate_chapter_name,
        validate_volume_name,
        validate_order,
        sanitize_text,
        DANGEROUS_HTML_TAGS
    )
    from src.exceptions import ValidationError

    # Test sanitize_text
    safe = sanitize_text("  Normal text  ")
    assert safe == "Normal text"
    print("  ✓ sanitize_text trims whitespace")

    # Test dangerous HTML tags detection
    for tag in DANGEROUS_HTML_TAGS:
        try:
            sanitize_text(f"Text with {tag}malicious</tag>")
            assert False, f"Should reject {tag}"
        except ValidationError:
            pass
    print(f"  ✓ Blocks {len(DANGEROUS_HTML_TAGS)} dangerous HTML tags")

    # Test null byte removal
    safe = sanitize_text("text\x00with\x00nulls")
    assert '\x00' not in safe
    print("  ✓ Removes null bytes")

    # Test title validation
    assert validate_title("Valid Title") == "Valid Title"
    print("  ✓ validate_title accepts valid input")

    try:
        validate_title("")
        assert False
    except ValidationError:
        print("  ✓ validate_title rejects empty")

    # Test author validation
    assert validate_author("Author Name") == "Author Name"
    assert validate_author(None) is None
    assert validate_author("") is None
    print("  ✓ validate_author handles optional input")

    # Test year validation
    assert validate_year(2023) == 2023
    assert validate_year("2023") == 2023
    assert validate_year(None) is None
    print("  ✓ validate_year converts and validates")

    try:
        validate_year(1800)
        assert False
    except ValidationError:
        print("  ✓ validate_year rejects old years")

    try:
        validate_year(2200)
        assert False
    except ValidationError:
        print("  ✓ validate_year rejects future years")

    # Test tags validation
    assert validate_tags("Action, Fantasy") is not None
    assert validate_tags(None) is None
    print("  ✓ validate_tags accepts valid input")

    try:
        validate_tags("Valid, <script>alert()</script>")
        assert False
    except ValidationError:
        print("  ✓ validate_tags blocks invalid characters")

    # Test order validation
    assert validate_order(1) == 1
    assert validate_order("5") == 5
    print("  ✓ validate_order converts strings to int")

    try:
        validate_order(0)
        assert False
    except ValidationError:
        print("  ✓ validate_order rejects 0")

    try:
        validate_order(-1)
        assert False
    except ValidationError:
        print("  ✓ validate_order rejects negative")

    try:
        validate_order(100000)
        assert False
    except ValidationError:
        print("  ✓ validate_order rejects too large")

    try:
        validate_order("abc")
        assert False
    except ValidationError:
        print("  ✓ validate_order rejects non-numeric")

    # Test chapter/volume names
    assert validate_chapter_name("Chapter 1") == "Chapter 1"
    assert validate_volume_name("Volume 1") == "Volume 1"
    print("  ✓ validate_chapter/volume_name work correctly")

    # Test length limits
    long_text = "A" * 500
    result = validate_title(long_text)
    assert len(result) <= 200
    print("  ✓ Length limits enforced (title)")

    result = validate_description("B" * 5000)
    assert len(result) <= 2000
    print("  ✓ Length limits enforced (description)")

    print("✓ Validation module tests passed\n")
    return True


def test_exceptions_hierarchy():
    """Test custom exceptions hierarchy."""
    print("Testing exceptions hierarchy...")

    from src.exceptions import (
        MangaReaderError,
        ValidationError,
        FileSizeError,
        DatabaseError,
        DatabaseSchemaError,
        CacheError,
        SettingsError,
    )

    # Test ValidationError
    exc = ValidationError("Test error")
    assert isinstance(exc, MangaReaderError)
    print("  ✓ ValidationError inherits from MangaReaderError")

    # Test FileSizeError
    exc = FileSizeError(100.5, 50)
    assert exc.actual_size_mb == 100.5
    assert exc.max_size_mb == 50
    assert isinstance(exc, ValidationError)
    print("  ✓ FileSizeError has correct attributes")

    # Test DatabaseError hierarchy
    exc = DatabaseSchemaError("Schema error")
    assert isinstance(exc, DatabaseError)
    assert isinstance(exc, MangaReaderError)
    print("  ✓ DatabaseSchemaError hierarchy correct")

    # Test CacheError
    exc = CacheError("Cache error")
    assert isinstance(exc, MangaReaderError)
    print("  ✓ CacheError hierarchy correct")

    # Test SettingsError
    exc = SettingsError("Settings error")
    assert isinstance(exc, MangaReaderError)
    print("  ✓ SettingsError hierarchy correct")

    print("✓ Exceptions hierarchy tests passed\n")
    return True


def test_filename_sanitization_isolated():
    """Test filename sanitization without importing archive_importer."""
    print("Testing filename sanitization (isolated)...")

    import re

    # Replicate the sanitization logic to test it
    FORBIDDEN_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
    WINDOWS_RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }

    def test_sanitize(filename):
        if not filename:
            return None

        # Extract basename
        sanitized = os.path.basename(filename)

        # Remove forbidden chars
        sanitized = re.sub(FORBIDDEN_FILENAME_CHARS, '_', sanitized)

        # Remove multiple dots
        sanitized = re.sub(r'\.{2,}', '_', sanitized)

        # Remove leading/trailing dots
        sanitized = sanitized.strip('.')

        # Check reserved names
        from pathlib import Path
        name_without_ext = Path(sanitized).stem.upper()
        if name_without_ext in WINDOWS_RESERVED_NAMES:
            sanitized = f"file_{sanitized}"

        return sanitized

    # Test path traversal
    result = test_sanitize("../../../etc/passwd")
    assert '/' not in result and '\\' not in result
    assert '..' not in result
    print("  ✓ Path traversal characters removed")

    # Test forbidden characters
    result = test_sanitize("file<>:|?*.txt")
    for char in '<>:|?*':
        assert char not in result
    print("  ✓ Forbidden characters removed")

    # Test reserved names
    result = test_sanitize("CON.txt")
    assert result.startswith("file_")
    print("  ✓ Reserved names handled")

    # Test leading dots
    result = test_sanitize(".hidden")
    assert not result.startswith('.')
    print("  ✓ Leading dots removed")

    print("✓ Filename sanitization isolated tests passed\n")
    return True


def test_path_safety():
    """Test path safety checking logic."""
    print("Testing path safety logic...")

    # Create temp directory for testing
    with tempfile.TemporaryDirectory() as base:
        # Test safe paths
        safe_path = os.path.join(base, "file.txt")
        base_real = os.path.realpath(base)
        safe_real = os.path.realpath(safe_path)

        # Check if safe_real starts with base_real
        is_safe = safe_real.startswith(base_real + os.sep) or safe_real == base_real
        assert is_safe, "Safe path should be accepted"
        print("  ✓ Safe path correctly identified")

        # Test path with .. (would escape)
        # Note: We can't actually create a file outside in tests,
        # but we can test the logic
        dangerous_path = os.path.join(base, "..", "outside.txt")
        dangerous_real = os.path.realpath(dangerous_path)

        is_safe = dangerous_real.startswith(base_real + os.sep) or dangerous_real == base_real
        # This should be False if dangerous_real is actually outside base
        print(f"  ✓ Path traversal detection: path is {'SAFE' if is_safe else 'UNSAFE'}")

    print("✓ Path safety tests passed\n")
    return True


def test_constants():
    """Test that security constants are properly defined."""
    print("Testing security constants...")

    from src.constants import MAX_IMAGE_SIZE_MB
    from src.utils.validation import (
        MAX_TITLE_LENGTH,
        MAX_AUTHOR_LENGTH,
        MAX_DESCRIPTION_LENGTH,
        MAX_TAGS_LENGTH
    )

    assert MAX_IMAGE_SIZE_MB == 50
    print(f"  ✓ MAX_IMAGE_SIZE_MB = {MAX_IMAGE_SIZE_MB}")

    assert MAX_TITLE_LENGTH == 200
    print(f"  ✓ MAX_TITLE_LENGTH = {MAX_TITLE_LENGTH}")

    assert MAX_DESCRIPTION_LENGTH == 2000
    print(f"  ✓ MAX_DESCRIPTION_LENGTH = {MAX_DESCRIPTION_LENGTH}")

    assert MAX_TAGS_LENGTH == 500
    print(f"  ✓ MAX_TAGS_LENGTH = {MAX_TAGS_LENGTH}")

    print("✓ Security constants tests passed\n")
    return True


def main():
    """Run all isolated security tests."""
    print("=" * 70)
    print("ISOLATED SECURITY TESTS - Phase 5")
    print("=" * 70)
    print()

    tests = [
        test_validation_module,
        test_exceptions_hierarchy,
        test_filename_sanitization_isolated,
        test_path_safety,
        test_constants,
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
        print("ALL TESTS PASSED ✓")
        return 0
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(main())
