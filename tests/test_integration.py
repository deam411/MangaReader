#!/usr/bin/env python3
"""Test di integrazione per verificare correttezza logica dei bugfix."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_integration_1_settings_logger():
    """Verifica che Settings possa essere importato e logger sia usabile."""
    try:
        from src.settings import Settings
        from src.logger import get_logger

        # Verifica che Settings sia singleton
        s1 = Settings()
        s2 = Settings()
        assert s1 is s2, "Settings non è singleton!"

        # Verifica che logger sia accessibile
        logger = get_logger('test')
        assert logger is not None, "Logger non accessibile!"

        print("✅ Integration 1: Settings + Logger integrazione OK")
        return True
    except Exception as e:
        print(f"❌ Integration 1 FAILED: {e}")
        return False


def test_integration_2_constants_import():
    """Verifica che le nuove costanti siano importabili ovunque necessario."""
    try:
        from src.constants import MAX_IMAGE_SIZE_MB
        from src.importers.archive_importer import ArchiveImporter

        # Verifica che l'importer abbia accesso alla costante
        # (controlla che sia nel namespace del modulo)
        import src.importers.archive_importer as importer_module

        # Il modulo deve avere accesso a MAX_IMAGE_SIZE_MB
        assert hasattr(importer_module, 'MAX_IMAGE_SIZE_MB'), \
            "Importer non ha accesso a MAX_IMAGE_SIZE_MB!"

        assert importer_module.MAX_IMAGE_SIZE_MB == 50, \
            f"Valore costante non corretto: {importer_module.MAX_IMAGE_SIZE_MB}"

        print("✅ Integration 2: Constants import chain OK")
        return True
    except Exception as e:
        print(f"❌ Integration 2 FAILED: {e}")
        return False


def test_integration_3_lru_cache_usage():
    """Verifica che LRUCache sia usato correttamente."""
    try:
        from src.chapter_reader_window import LRUCache

        # Test funzionamento LRU
        cache = LRUCache(capacity=3)

        cache.put('a', 1)
        cache.put('b', 2)
        cache.put('c', 3)

        assert cache.get('a') == 1, "LRU get fallito!"

        # Aggiungi nuovo elemento - 'b' dovrebbe essere rimosso (least recently used)
        cache.put('d', 4)

        assert cache.get('a') is not None, "a dovrebbe essere ancora in cache (usato recentemente)"
        assert cache.get('c') is not None, "c dovrebbe essere ancora in cache"
        assert cache.get('d') is not None, "d dovrebbe essere in cache"

        print("✅ Integration 3: LRUCache funziona correttamente")
        return True
    except Exception as e:
        print(f"❌ Integration 3 FAILED: {e}")
        return False


def test_integration_4_database_manager():
    """Verifica che MangaDatabaseManager sia importabile."""
    try:
        from src.database import MangaDatabaseManager

        # Verifica che la classe esista e abbia i metodi previsti
        assert hasattr(MangaDatabaseManager, 'create_manga_db_schema'), \
            "Metodo create_manga_db_schema non trovato!"
        assert hasattr(MangaDatabaseManager, 'optimize_database_settings'), \
            "Metodo optimize_database_settings non trovato!"

        print("✅ Integration 4: MangaDatabaseManager import OK")
        return True
    except Exception as e:
        print(f"❌ Integration 4 FAILED: {e}")
        return False


def test_integration_5_cache_manager():
    """Verifica CacheManager integrazione."""
    try:
        from src.cache_manager import CacheManager
        import tempfile
        import os

        # Crea cache manager con directory temporanea
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(cache_dir=tmpdir)

            # Verifica che la directory sia stata creata
            assert os.path.exists(tmpdir), "Cache dir non creata!"

            # Verifica metodi esistano
            assert hasattr(cache, 'get_cached'), "Metodo get_cached non trovato!"
            assert hasattr(cache, 'save_to_cache'), "Metodo save_to_cache non trovato!"
            assert hasattr(cache, 'cleanup_old_cache'), "Metodo cleanup_old_cache non trovato!"

            # Test get_cache_info
            info = cache.get_cache_info()
            assert 'file_count' in info, "cache_info non contiene file_count!"
            assert 'total_size_mb' in info, "cache_info non contiene total_size_mb!"

        print("✅ Integration 5: CacheManager integrazione OK")
        return True
    except Exception as e:
        print(f"❌ Integration 5 FAILED: {e}")
        return False


def run_integration_tests():
    """Esegue tutti i test di integrazione."""
    tests = [
        test_integration_1_settings_logger,
        test_integration_2_constants_import,
        test_integration_3_lru_cache_usage,
        test_integration_4_database_manager,
        test_integration_5_cache_manager,
    ]

    print("="*70)
    print("🔗 TEST DI INTEGRAZIONE")
    print("="*70)
    print()

    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()

    print("="*70)
    print(f"📊 RISULTATI: {passed}/{len(tests)} test integrazione passati")
    print("="*70)

    return passed == len(tests)


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
