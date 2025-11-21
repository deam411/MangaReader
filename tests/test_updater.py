"""
Test suite per auto-updater - v0.1.0.

Tests per version parsing, comparison e funzioni utility.
"""

import sys
import os


def test_version_parsing():
    """Test parsing delle versioni."""
    print("Testing version parsing...")

    from src.updater import parse_version

    # Test versioni valide
    test_cases = [
        ("0.1.0", (0, 1, 0)),
        ("v0.1.0", (0, 1, 0)),
        ("1.2.3", (1, 2, 3)),
        ("v10.20.30", (10, 20, 30)),
    ]

    for version_str, expected in test_cases:
        result = parse_version(version_str)
        assert result == expected, f"Parse failed for {version_str}: {result} != {expected}"
        print(f"  ✓ Parsed '{version_str}' -> {result}")

    # Test versioni invalide
    invalid_cases = ["0.1", "1.2.3.4", "abc", "v1.x.0", ""]

    for invalid in invalid_cases:
        try:
            parse_version(invalid)
            assert False, f"Should have raised ValueError for '{invalid}'"
        except ValueError:
            print(f"  ✓ Correctly rejected invalid version: '{invalid}'")

    print("✓ Version parsing tests passed\n")
    return True


def test_version_comparison():
    """Test confronto versioni."""
    print("Testing version comparison...")

    from src.updater import is_newer_version

    # Test casi dove latest > current
    newer_cases = [
        ("0.1.0", "0.2.0"),  # Minor bump
        ("0.1.0", "1.0.0"),  # Major bump
        ("0.1.0", "0.1.1"),  # Patch bump
        ("1.2.3", "2.0.0"),  # Major bump
        ("v0.1.0", "v0.2.0"),  # Con prefisso v
    ]

    for current, latest in newer_cases:
        result = is_newer_version(current, latest)
        assert result is True, f"{latest} should be newer than {current}"
        print(f"  ✓ {latest} > {current}")

    # Test casi dove latest <= current
    not_newer_cases = [
        ("0.2.0", "0.1.0"),  # Older
        ("1.0.0", "1.0.0"),  # Same
        ("0.1.1", "0.1.0"),  # Older patch
    ]

    for current, latest in not_newer_cases:
        result = is_newer_version(current, latest)
        assert result is False, f"{latest} should NOT be newer than {current}"
        print(f"  ✓ {latest} <= {current}")

    print("✓ Version comparison tests passed\n")
    return True


def test_get_current_version():
    """Test lettura versione corrente."""
    print("Testing get_current_version...")

    from src.updater import get_current_version
    from src.constants import APP_VERSION

    version = get_current_version()
    assert version == APP_VERSION, f"Version mismatch: {version} != {APP_VERSION}"
    print(f"  ✓ Current version: {version}")

    print("✓ Get current version test passed\n")
    return True


def test_platform_asset_detection():
    """Test rilevamento asset corretto per piattaforma."""
    print("Testing platform asset detection...")

    from src.updater import _get_platform_asset
    import platform

    # Mock assets come da GitHub API
    mock_assets = [
        {'name': 'MangaReader.exe', 'browser_download_url': 'https://example.com/MangaReader.exe'},
        {'name': 'MangaReader.dmg', 'browser_download_url': 'https://example.com/MangaReader.dmg'},
        {'name': 'MangaReader', 'browser_download_url': 'https://example.com/MangaReader'},
    ]

    asset_name, download_url = _get_platform_asset(mock_assets)

    system = platform.system()
    if system == 'Windows':
        assert asset_name == 'MangaReader.exe'
        print(f"  ✓ Windows: selected {asset_name}")
    elif system == 'Darwin':
        assert asset_name == 'MangaReader.dmg'
        print(f"  ✓ macOS: selected {asset_name}")
    elif system == 'Linux':
        assert asset_name == 'MangaReader'
        print(f"  ✓ Linux: selected {asset_name}")

    assert download_url is not None
    print(f"  ✓ Download URL found: {download_url}")

    print("✓ Platform asset detection test passed\n")
    return True


def test_update_info_formatting():
    """Test formattazione info aggiornamento."""
    print("Testing update info formatting...")

    from src.updater import get_update_info_text

    mock_update = {
        'version': '0.2.0',
        'release_notes': 'Test release notes\n- Feature 1\n- Feature 2',
        'published_at': '2025-11-08T12:00:00Z'
    }

    text = get_update_info_text(mock_update)

    assert '0.2.0' in text
    assert 'Feature 1' in text
    assert '2025-11-08' in text
    print(f"  ✓ Formatted text contains version, notes, and date")

    # Test con note molto lunghe
    long_notes = 'A' * 600
    mock_update_long = {
        'version': '0.3.0',
        'release_notes': long_notes,
        'published_at': '2025-11-08'
    }

    text_long = get_update_info_text(mock_update_long)
    assert len(text_long) < len(long_notes) + 200  # Dovrebbe essere troncato
    assert 'Vedi release completa su GitHub' in text_long
    print(f"  ✓ Long notes are truncated correctly")

    print("✓ Update info formatting test passed\n")
    return True


def main():
    """Run all updater tests."""
    print("=" * 70)
    print("AUTO-UPDATER TESTS - v0.1.0")
    print("=" * 70)
    print()

    tests = [
        test_version_parsing,
        test_version_comparison,
        test_get_current_version,
        test_platform_asset_detection,
        test_update_info_formatting,
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


if __name__ == "__main__":
    sys.exit(main())
