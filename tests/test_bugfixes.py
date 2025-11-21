#!/usr/bin/env python3
"""
Test specifici per i bugfix della Fase 1.
Questi test non richiedono PyQt5 e possono essere eseguiti in ambiente CLI.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_constants_max_image_size():
    """Test 1: Verifica che MAX_IMAGE_SIZE_MB sia definito correttamente."""
    from src.constants import MAX_IMAGE_SIZE_MB

    assert MAX_IMAGE_SIZE_MB == 50, f"Expected MAX_IMAGE_SIZE_MB=50, got {MAX_IMAGE_SIZE_MB}"
    assert isinstance(MAX_IMAGE_SIZE_MB, int), f"MAX_IMAGE_SIZE_MB deve essere int, è {type(MAX_IMAGE_SIZE_MB)}"

    print("✅ Test 1 PASSED: MAX_IMAGE_SIZE_MB correttamente definito")


def test_settings_logging_fix():
    """Test 2: Verifica che Settings.save() usi logger invece di print."""

    # Leggi il file sorgente
    settings_path = Path(__file__).parent / 'src' / 'settings.py'
    with open(settings_path, 'r') as f:
        content = f.read()

    # Verifica che non ci siano print() nella funzione save()
    # Cerca la definizione della funzione save
    save_func_start = content.find('def save(self):')
    if save_func_start == -1:
        raise AssertionError("Funzione save() non trovata")

    # Trova la fine della funzione (prossima funzione o fine file)
    next_def = content.find('\n    def ', save_func_start + 10)
    if next_def == -1:
        save_func_content = content[save_func_start:]
    else:
        save_func_content = content[save_func_start:next_def]

    # Verifica che usi logger.error() invece di print()
    assert 'print(' not in save_func_content, "save() contiene ancora print() invece di logger!"
    assert 'logger.error(' in save_func_content, "save() non usa logger.error()!"

    print("✅ Test 2 PASSED: Settings.save() usa logger correttamente")


def test_resource_leak_fix():
    """Test 3: Verifica che LibraryLoaderThread usi context manager."""

    views_path = Path(__file__).parent / 'views.py'
    with open(views_path, 'r') as f:
        content = f.read()

    # Trova la classe LibraryLoaderThread
    loader_start = content.find('class LibraryLoaderThread')
    if loader_start == -1:
        raise AssertionError("LibraryLoaderThread non trovata")

    # Trova il metodo run()
    run_start = content.find('def run(self):', loader_start)
    if run_start == -1:
        raise AssertionError("Metodo run() non trovato")

    # Trova la fine del metodo
    next_class = content.find('\nclass ', run_start + 10)
    if next_class == -1:
        run_content = content[run_start:]
    else:
        run_content = content[run_start:next_class]

    # Verifica che usi context manager (with sqlite3.connect)
    assert 'with sqlite3.connect(' in run_content, "Non usa context manager per sqlite3!"
    # Verifica che NON ci sia conn.close() esplicito (non più necessario con context manager)
    # Nota: potrebbe esserci in vecchi commenti, quindi cerchiamo pattern specifico
    lines = run_content.split('\n')
    for line in lines:
        if 'conn.close()' in line and not line.strip().startswith('#'):
            raise AssertionError("Trovato conn.close() esplicito - context manager non usato correttamente!")

    print("✅ Test 3 PASSED: LibraryLoaderThread usa context manager")


def test_cache_key_stability_fix():
    """Test 4: Verifica che la cache key usi file_path invece di id()."""

    views_path = Path(__file__).parent / 'views.py'
    with open(views_path, 'r') as f:
        content = f.read()

    # Trova MangaItemDelegate.paint()
    delegate_start = content.find('class MangaItemDelegate')
    paint_start = content.find('def paint(self, painter, option, index):', delegate_start)

    if paint_start == -1:
        raise AssertionError("Metodo paint() non trovato in MangaItemDelegate")

    # Cerca il blocco che definisce cache_key
    paint_end = content.find('\n    def ', paint_start + 10)
    if paint_end == -1:
        paint_content = content[paint_start:]
    else:
        paint_content = content[paint_start:paint_end]

    # Verifica che cache_key usi file_path
    assert 'cache_key = file_path' in paint_content or 'cache_key = (file_path' in paint_content, \
        "cache_key non usa file_path!"

    # Verifica che NON usi più id(cover_data) come chiave primaria
    # (potrebbe essere fallback, ma non primario)
    lines = paint_content.split('\n')
    for line in lines:
        if 'cache_key =' in line and 'id(cover_data)' in line and 'if' not in line and 'else' not in line:
            # Se è una assegnazione diretta (non ternario), è un problema
            if line.strip().startswith('cache_key = (id(cover_data)'):
                raise AssertionError("cache_key usa ancora id(cover_data) come chiave primaria!")

    print("✅ Test 4 PASSED: Cache key usa file_path stabile")


def test_file_size_validation_in_importer():
    """Test 5: Verifica validazione file size in archive_importer."""

    importer_path = Path(__file__).parent / 'src' / 'importers' / 'archive_importer.py'
    with open(importer_path, 'r') as f:
        content = f.read()

    # Verifica import di MAX_IMAGE_SIZE_MB
    assert 'from ..constants import' in content and 'MAX_IMAGE_SIZE_MB' in content, \
        "MAX_IMAGE_SIZE_MB non importato!"

    # Verifica validazione in extract_images_from_zip
    assert 'image_size_mb' in content, "Validazione dimensione immagine non implementata!"
    assert 'if image_size_mb > MAX_IMAGE_SIZE_MB' in content, "Check dimensione non presente!"

    print("✅ Test 5 PASSED: Validazione file size in importer")


def test_file_size_validation_in_creator():
    """Test 6: Verifica validazione file size in manga_creator_app."""

    creator_path = Path(__file__).parent / 'src' / 'creator' / 'manga_creator_app.py'
    with open(creator_path, 'r') as f:
        content = f.read()

    # Verifica import di MAX_IMAGE_SIZE_MB
    assert 'from ..constants import MAX_IMAGE_SIZE_MB' in content, \
        "MAX_IMAGE_SIZE_MB non importato in creator!"

    # Verifica validazione in convert_image_to_compatible_format
    convert_func_start = content.find('def convert_image_to_compatible_format')
    if convert_func_start == -1:
        raise AssertionError("convert_image_to_compatible_format non trovata")

    func_end = content.find('\n    def ', convert_func_start + 10)
    if func_end == -1:
        func_content = content[convert_func_start:]
    else:
        func_content = content[convert_func_start:func_end]

    assert 'file_size_mb' in func_content, "Validazione dimensione non implementata!"
    assert 'raise ValueError' in func_content, "ValueError non sollevato per file troppo grandi!"

    print("✅ Test 6 PASSED: Validazione file size in creator")


def test_race_condition_fix():
    """Test 7: Verifica fix race condition in PageDisplayWidget."""

    reader_path = Path(__file__).parent / 'src' / 'chapter_reader_window.py'
    with open(reader_path, 'r') as f:
        content = f.read()

    # Verifica che _is_loading esista in __init__
    init_start = content.find('def __init__(self, parent=None):')
    class_end = content.find('\n    def ', init_start + 100)
    init_content = content[init_start:class_end] if class_end != -1 else content[init_start:init_start+2000]

    assert 'self._is_loading = False' in init_content, "Flag _is_loading non inizializzato!"

    # Verifica che handle_image_loaded usi il flag
    handle_start = content.find('def handle_image_loaded')
    handle_end = content.find('\n    def ', handle_start + 10)
    handle_content = content[handle_start:handle_end] if handle_end != -1 else content[handle_start:handle_start+500]

    assert 'if self._is_loading:' in handle_content, "handle_image_loaded non controlla _is_loading!"
    assert 'return' in handle_content, "handle_image_loaded non fa return se _is_loading!"

    # Verifica che set_pages_metadata usi try-finally
    set_meta_start = content.find('def set_pages_metadata')
    set_meta_end = content.find('\n    def ', set_meta_start + 10)
    set_meta_content = content[set_meta_start:set_meta_end] if set_meta_end != -1 else content[set_meta_start:set_meta_start+1000]

    assert 'self._is_loading = True' in set_meta_content, "set_pages_metadata non imposta _is_loading!"
    assert 'try:' in set_meta_content, "set_pages_metadata non usa try-finally!"
    assert 'finally:' in set_meta_content, "set_pages_metadata non usa try-finally!"
    assert 'self._is_loading = False' in set_meta_content, "set_pages_metadata non rilascia _is_loading!"

    print("✅ Test 7 PASSED: Race condition fix implementato correttamente")


def run_all_tests():
    """Esegue tutti i test."""
    tests = [
        test_constants_max_image_size,
        test_settings_logging_fix,
        test_resource_leak_fix,
        test_cache_key_stability_fix,
        test_file_size_validation_in_importer,
        test_file_size_validation_in_creator,
        test_race_condition_fix,
    ]

    passed = 0
    failed = 0
    errors = []

    print("="*70)
    print("🧪 TESTING BUGFIX FASE 1")
    print("="*70)
    print()

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            errors.append(f"❌ {test_func.__name__}: {e}")
            print(f"❌ Test FAILED: {test_func.__name__}")
            print(f"   Error: {e}")
        except Exception as e:
            failed += 1
            errors.append(f"💥 {test_func.__name__}: {e}")
            print(f"💥 Test ERROR: {test_func.__name__}")
            print(f"   Error: {e}")

    print()
    print("="*70)
    print(f"📊 RISULTATI: {passed}/{len(tests)} test passati")
    print("="*70)

    if errors:
        print("\n❌ ERRORI:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("\n✅ TUTTI I TEST PASSATI!")
        return True


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
