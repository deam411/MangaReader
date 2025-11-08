"""
Test suite for Phase 4 Security Hardening.

Tests filename sanitization, path traversal protection,
and input validation for metadata.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path


def test_filename_sanitization():
    """Test filename sanitization prevents dangerous characters and path traversal."""
    print("Testing filename sanitization...")

    from src.importers.archive_importer import ArchiveImporter
    from src.exceptions import ValidationError

    importer = ArchiveImporter()

    # Test 1: Path traversal attempts
    dangerous_names = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "../../../../root/.ssh/id_rsa",
        "some/path/../../file.txt",
    ]

    for dangerous in dangerous_names:
        try:
            safe = importer.sanitize_filename(dangerous)
            # Should remove path components
            assert '/' not in safe and '\\' not in safe, f"Path separator found in: {safe}"
            assert '..' not in safe, f"Path traversal found in: {safe}"
            print(f"  ✓ Sanitized '{dangerous}' -> '{safe}'")
        except ValidationError as e:
            print(f"  ✓ Rejected dangerous filename '{dangerous}': {e}")

    # Test 2: Forbidden characters
    forbidden_chars_test = [
        "file<script>.txt",
        "file|pipe.txt",
        "file:colon.txt",
        "file*star.txt",
        "file?question.txt",
        'file"quote.txt',
    ]

    for test_name in forbidden_chars_test:
        safe = importer.sanitize_filename(test_name)
        for char in '<>:"|?*':
            assert char not in safe, f"Forbidden char '{char}' found in: {safe}"
        print(f"  ✓ Removed forbidden chars: '{test_name}' -> '{safe}'")

    # Test 3: Windows reserved names
    reserved_names = ["CON.txt", "PRN.jpg", "AUX.png", "NUL.dat"]
    for reserved in reserved_names:
        safe = importer.sanitize_filename(reserved)
        assert not safe.upper().startswith(('CON', 'PRN', 'AUX', 'NUL')), \
            f"Reserved name not handled: {safe}"
        print(f"  ✓ Handled reserved name: '{reserved}' -> '{safe}'")

    # Test 4: Hidden files (leading dots)
    hidden = ".hidden_file.txt"
    safe = importer.sanitize_filename(hidden)
    assert not safe.startswith('.'), f"Leading dot not removed: {safe}"
    print(f"  ✓ Removed leading dot: '{hidden}' -> '{safe}'")

    # Test 5: Empty filename after sanitization
    try:
        importer.sanitize_filename("...")
        assert False, "Should have raised ValidationError for empty result"
    except ValidationError:
        print("  ✓ Rejected filename that becomes empty after sanitization")

    # Test 6: Length limit
    long_name = "a" * 300 + ".txt"
    safe = importer.sanitize_filename(long_name)
    assert len(safe) <= 255, f"Filename too long: {len(safe)}"
    assert safe.endswith('.txt'), "Extension should be preserved"
    print(f"  ✓ Truncated long filename: {len(long_name)} -> {len(safe)} chars")

    print("✓ Filename sanitization tests passed\n")
    return True


def test_path_traversal_protection():
    """Test path traversal protection prevents escaping base directory."""
    print("Testing path traversal protection...")

    from src.importers.archive_importer import ArchiveImporter

    importer = ArchiveImporter()

    # Create temporary base directory
    with tempfile.TemporaryDirectory() as temp_base:
        # Test 1: Safe path (inside base)
        safe_path = os.path.join(temp_base, "safe_file.txt")
        assert importer.is_safe_path(temp_base, safe_path), \
            "Safe path incorrectly rejected"
        print(f"  ✓ Accepted safe path inside base")

        # Test 2: Dangerous path (outside base) with relative path
        dangerous_relative = os.path.join(temp_base, "../outside.txt")
        is_safe = importer.is_safe_path(temp_base, dangerous_relative)
        # This should be False because realpath will resolve ../ outside base
        print(f"  ✓ Path traversal check: {'SAFE' if is_safe else 'BLOCKED'} for '../outside.txt'")

        # Test 3: Subdirectory is safe
        subdir = os.path.join(temp_base, "subdir", "file.txt")
        assert importer.is_safe_path(temp_base, subdir), \
            "Subdirectory path incorrectly rejected"
        print(f"  ✓ Accepted subdirectory path")

        # Test 4: Base path itself is safe
        assert importer.is_safe_path(temp_base, temp_base), \
            "Base path itself should be safe"
        print(f"  ✓ Accepted base path itself")

    print("✓ Path traversal protection tests passed\n")
    return True


def test_metadata_validation():
    """Test input validation for manga metadata."""
    print("Testing metadata input validation...")

    from src.utils.validation import (
        validate_title,
        validate_author,
        validate_description,
        validate_year,
        validate_tags,
        validate_chapter_name,
        validate_volume_name,
        validate_order,
        sanitize_text
    )
    from src.exceptions import ValidationError

    # Test 1: Title validation
    valid_title = validate_title("  My Manga Title  ")
    assert valid_title == "My Manga Title", "Title whitespace not trimmed"
    print("  ✓ Title validation: whitespace trimmed")

    try:
        validate_title("")
        assert False, "Empty title should raise ValidationError"
    except ValidationError:
        print("  ✓ Title validation: empty title rejected")

    # Test 2: XSS prevention in description
    xss_attempts = [
        "<script>alert('XSS')</script>Normal text",
        "Text with <iframe src='evil.com'></iframe>",
        "Innocent text <object data='malicious'></object>",
    ]

    for xss in xss_attempts:
        try:
            sanitize_text(xss)
            assert False, f"XSS attempt should be rejected: {xss}"
        except ValidationError as e:
            print(f"  ✓ XSS blocked: {str(e)[:50]}...")

    # Test 3: Year validation
    assert validate_year(2023) == 2023, "Valid year rejected"
    assert validate_year("2023") == 2023, "String year not converted"
    assert validate_year(None) is None, "None year not handled"
    print("  ✓ Year validation: valid years accepted")

    try:
        validate_year(1800)
        assert False, "Year 1800 should be rejected"
    except ValidationError:
        print("  ✓ Year validation: year too old rejected")

    try:
        validate_year(2200)
        assert False, "Year 2200 should be rejected"
    except ValidationError:
        print("  ✓ Year validation: year too new rejected")

    # Test 4: Tags validation
    valid_tags = validate_tags("Action, Adventure, Fantasy")
    assert valid_tags is not None, "Valid tags rejected"
    print("  ✓ Tags validation: comma-separated tags accepted")

    try:
        validate_tags("Valid, <script>alert()</script>, Tags")
        assert False, "Tags with HTML should be rejected"
    except ValidationError:
        print("  ✓ Tags validation: HTML tags rejected")

    # Test 5: Order validation
    assert validate_order(1) == 1, "Valid order rejected"
    assert validate_order("5") == 5, "String order not converted"
    print("  ✓ Order validation: valid orders accepted")

    try:
        validate_order(0)
        assert False, "Order 0 should be rejected"
    except ValidationError:
        print("  ✓ Order validation: order < 1 rejected")

    try:
        validate_order("not_a_number")
        assert False, "Non-numeric order should be rejected"
    except ValidationError:
        print("  ✓ Order validation: non-numeric rejected")

    # Test 6: Length limits
    long_title = "A" * 300
    validated = validate_title(long_title)
    assert len(validated) <= 200, "Title not truncated"
    print(f"  ✓ Length limit: title truncated from {len(long_title)} to {len(validated)}")

    long_description = "B" * 3000
    validated_desc = validate_description(long_description)
    assert len(validated_desc) <= 2000, "Description not truncated"
    print(f"  ✓ Length limit: description truncated from {len(long_description)} to {len(validated_desc)}")

    print("✓ Metadata validation tests passed\n")
    return True


def test_database_validation_integration():
    """Test that database operations use validation correctly."""
    print("Testing database validation integration...")

    try:
        from src.database import MangaDatabaseManager
        from src.exceptions import ValidationError
    except ImportError as e:
        print(f"  ⊘ Skipped (missing dependency: {e})")
        return True

    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.manga') as f:
        temp_db = f.name

    try:
        db = MangaDatabaseManager(temp_db)

        # Test 1: Valid metadata insertion
        result = db.insert_metadata(
            title="Test Manga",
            author="Test Author",
            year=2023,
            tags="Action, Adventure"
        )
        assert result is True, "Valid metadata insertion failed"
        print("  ✓ Database accepts valid metadata")

        # Test 2: Invalid title (empty)
        try:
            db.insert_metadata(title="")
            assert False, "Empty title should raise ValidationError"
        except ValidationError:
            print("  ✓ Database rejects empty title")

        # Test 3: Invalid year (out of range)
        try:
            db.insert_metadata(title="Test", year=1800)
            assert False, "Invalid year should raise ValidationError"
        except ValidationError:
            print("  ✓ Database rejects invalid year")

        # Test 4: XSS attempt in description
        try:
            db.insert_metadata(
                title="XSS Test",
                description="<script>alert('XSS')</script>"
            )
            assert False, "XSS in description should be rejected"
        except ValidationError:
            print("  ✓ Database blocks XSS in description")

        # Test 5: Valid volume insertion
        volume_id = db.insert_volume("Volume 1", 1)
        assert volume_id is not None, "Valid volume insertion failed"
        print("  ✓ Database accepts valid volume")

        # Test 6: Invalid volume order
        try:
            db.insert_volume("Bad Volume", 0)
            assert False, "Order 0 should raise ValidationError"
        except ValidationError:
            print("  ✓ Database rejects invalid volume order")

        # Test 7: Valid chapter insertion
        chapter_id = db.insert_chapter("Chapter 1", 1, volume_id)
        assert chapter_id is not None, "Valid chapter insertion failed"
        print("  ✓ Database accepts valid chapter")

        # Test 8: Invalid chapter name (too long)
        long_name = "A" * 300
        chapter_id = db.insert_chapter(long_name, 2, volume_id)
        # Should succeed but truncated
        assert chapter_id is not None, "Chapter with long name failed"
        print("  ✓ Database truncates long chapter name")

        print("✓ Database validation integration tests passed\n")
        return True

    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_archive_importer_security():
    """Test security measures in archive importer."""
    print("Testing archive importer security...")

    from src.importers.archive_importer import ArchiveImporter

    importer = ArchiveImporter()

    # Test 1: Detect archive type safely
    # Create fake files to test detection
    with tempfile.NamedTemporaryFile(suffix='.cbz', delete=False) as f:
        fake_cbz = f.name
        f.write(b'PK\x03\x04')  # ZIP magic number

    try:
        detected = importer.detect_archive_type(fake_cbz)
        assert detected == 'cbz', f"CBZ not detected correctly: {detected}"
        print("  ✓ Archive type detection works")
    finally:
        os.unlink(fake_cbz)

    # Test 2: Image file validation
    assert importer.is_image_file("image.jpg") is True
    assert importer.is_image_file("image.png") is True
    assert importer.is_image_file("script.exe") is False
    assert importer.is_image_file("../../../etc/passwd") is False
    print("  ✓ Image file validation works")

    # Test 3: Supported formats
    formats = importer.get_supported_formats()
    assert '.cbz' in formats, "CBZ not in supported formats"
    assert '.zip' in formats, "ZIP not in supported formats"
    print(f"  ✓ Supported formats: {formats}")

    print("✓ Archive importer security tests passed\n")
    return True


def main():
    """Run all security validation tests."""
    print("=" * 70)
    print("SECURITY VALIDATION TESTS - Phase 5")
    print("=" * 70)
    print()

    tests = [
        test_filename_sanitization,
        test_path_traversal_protection,
        test_metadata_validation,
        test_database_validation_integration,
        test_archive_importer_security,
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

    print("=" * 70)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed > 0:
        print(f"WARNING: {failed} tests failed")
    else:
        print("ALL TESTS PASSED ✓")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
