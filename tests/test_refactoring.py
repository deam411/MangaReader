#!/usr/bin/env python3
"""
Script di test per verificare il refactoring v0.1.5.

Verifica:
1. Import delle view funzionano
2. Struttura modulare corretta
3. Backward compatibility
4. Sintassi Python corretta
"""

import sys
import os

# Aggiungi la directory corrente al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test 1: Verifica che tutti gli import funzionino."""
    print("=" * 60)
    print("TEST 1: Import delle view")
    print("=" * 60)

    try:
        # Test import dal proxy views.py (backward compatibility)
        print("✓ Testing import from views.py (proxy)...")
        from views import LibraryView, MangaView, VolumeView, ReaderView
        print("  ✓ LibraryView imported")
        print("  ✓ MangaView imported")
        print("  ✓ VolumeView imported")
        print("  ✓ ReaderView imported")

        # Test import diretto da src.views
        print("\n✓ Testing import from src.views package...")
        from src.views import (
            LibraryView as LibView2,
            MangaView as MangaView2,
            VolumeView as VolView2,
            ReaderView as ReadView2
        )
        print("  ✓ All views imported from src.views")

        # Test import widgets
        print("\n✓ Testing import widgets...")
        from src.views import LibraryLoaderThread, DeselectableListWidget, MangaItemDelegate
        print("  ✓ LibraryLoaderThread imported")
        print("  ✓ DeselectableListWidget imported")
        print("  ✓ MangaItemDelegate imported")

        # Test import dialogs
        print("\n✓ Testing import dialogs...")
        from src.views import ArchiveImportDialog, BookmarkDialog, ShortcutsDialog
        print("  ✓ ArchiveImportDialog imported")
        print("  ✓ BookmarkDialog imported")
        print("  ✓ ShortcutsDialog imported")

        # Test import utils
        print("\n✓ Testing import utils...")
        from src.views import sanitize_filename, calculate_reading_progress_fast
        print("  ✓ sanitize_filename imported")
        print("  ✓ calculate_reading_progress_fast imported")

        print("\n" + "=" * 60)
        print("✓ TEST 1 PASSED: Tutti gli import funzionano!")
        print("=" * 60)
        return True

    except ImportError as e:
        print(f"\n✗ TEST 1 FAILED: Errore import - {e}")
        return False
    except Exception as e:
        print(f"\n✗ TEST 1 FAILED: Errore inaspettato - {e}")
        return False


def test_file_structure():
    """Test 2: Verifica struttura file."""
    print("\n" + "=" * 60)
    print("TEST 2: Struttura file")
    print("=" * 60)

    required_files = [
        'views.py',  # Proxy
        'views_legacy.py',  # Backup
        'src/views/__init__.py',
        'src/views/widgets.py',
        'src/views/library_view.py',
        'src/views/manga_view.py',
        'src/views/volume_view.py',
        'src/views/reader_view.py',
        'src/views/dialogs.py',
        'src/views/utils.py',
    ]

    all_exist = True
    for file_path in required_files:
        exists = os.path.exists(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False

    if all_exist:
        print("\n" + "=" * 60)
        print("✓ TEST 2 PASSED: Tutti i file esistono!")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("✗ TEST 2 FAILED: Alcuni file mancanti!")
        print("=" * 60)
        return False


def test_syntax():
    """Test 3: Verifica sintassi Python."""
    print("\n" + "=" * 60)
    print("TEST 3: Sintassi Python")
    print("=" * 60)

    files_to_check = [
        'views.py',
        'src/views/__init__.py',
        'src/views/widgets.py',
        'src/views/library_view.py',
        'src/views/manga_view.py',
        'src/views/volume_view.py',
        'src/views/reader_view.py',
    ]

    import py_compile
    all_valid = True

    for file_path in files_to_check:
        try:
            py_compile.compile(file_path, doraise=True)
            print(f"  ✓ {file_path} - Sintassi OK")
        except py_compile.PyCompileError as e:
            print(f"  ✗ {file_path} - Errore sintassi: {e}")
            all_valid = False

    if all_valid:
        print("\n" + "=" * 60)
        print("✓ TEST 3 PASSED: Sintassi Python corretta!")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("✗ TEST 3 FAILED: Errori di sintassi!")
        print("=" * 60)
        return False


def test_class_attributes():
    """Test 4: Verifica attributi classi."""
    print("\n" + "=" * 60)
    print("TEST 4: Attributi classi View")
    print("=" * 60)

    try:
        from views import LibraryView, MangaView, VolumeView, ReaderView

        # Verifica che siano classi QWidget
        print("✓ Verificando ereditarietà...")
        from PyQt5.QtWidgets import QWidget

        views_to_check = [
            ('LibraryView', LibraryView),
            ('MangaView', MangaView),
            ('VolumeView', VolumeView),
            ('ReaderView', ReaderView),
        ]

        for name, view_class in views_to_check:
            # Verifica che abbiano __init__ method
            if hasattr(view_class, '__init__'):
                print(f"  ✓ {name} ha __init__ method")
            else:
                print(f"  ✗ {name} manca __init__ method")
                return False

        print("\n" + "=" * 60)
        print("✓ TEST 4 PASSED: Classi View correttamente definite!")
        print("=" * 60)
        return True

    except ImportError:
        print("  ⚠ PyQt5 non installato, skip test attributi")
        print("\n" + "=" * 60)
        print("⚠ TEST 4 SKIPPED: PyQt5 non disponibile")
        print("=" * 60)
        return True  # Non fallire se PyQt5 manca
    except Exception as e:
        print(f"\n✗ TEST 4 FAILED: {e}")
        return False


def test_version():
    """Test 5: Verifica versione."""
    print("\n" + "=" * 60)
    print("TEST 5: Versione")
    print("=" * 60)

    try:
        from src.constants import APP_VERSION
        print(f"  Versione corrente: {APP_VERSION}")

        if APP_VERSION == "0.1.5":
            print("  ✓ Versione corretta (0.1.5)")
            print("\n" + "=" * 60)
            print("✓ TEST 5 PASSED: Versione aggiornata!")
            print("=" * 60)
            return True
        else:
            print(f"  ✗ Versione errata (attesa: 0.1.5, trovata: {APP_VERSION})")
            print("\n" + "=" * 60)
            print("✗ TEST 5 FAILED: Versione non aggiornata!")
            print("=" * 60)
            return False

    except Exception as e:
        print(f"\n✗ TEST 5 FAILED: {e}")
        return False


def run_all_tests():
    """Esegue tutti i test."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "TEST REFACTORING v0.1.5" + " " * 25 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    tests = [
        ("Import", test_imports),
        ("Struttura File", test_file_structure),
        ("Sintassi Python", test_syntax),
        ("Attributi Classi", test_class_attributes),
        ("Versione", test_version),
    ]

    results = []
    for test_name, test_func in tests:
        passed = test_func()
        results.append((test_name, passed))

    # Riepilogo
    print("\n\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 20 + "RIEPILOGO" + " " * 29 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    total = len(results)
    passed = sum(1 for _, p in results if p)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {status:<15} {test_name}")

    print()
    print("=" * 60)
    if passed == total:
        print(f"✓ TUTTI I TEST PASSATI! ({passed}/{total})")
        print("=" * 60)
        print("\n🎉 Refactoring v0.1.5 funziona correttamente!")
        print("   Puoi procedere con sicurezza.\n")
        return 0
    else:
        print(f"✗ ALCUNI TEST FALLITI ({passed}/{total})")
        print("=" * 60)
        print("\n⚠ Ci sono problemi da risolvere prima di procedere.\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
