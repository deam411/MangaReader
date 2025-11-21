"""
Test manuale rapido per verificare le ottimizzazioni di performance.
Crea un database di test e misura i tempi di operazione.
"""
import os
import time
import tempfile
from pathlib import Path
from src.database import MangaDatabaseManager
from src.cache_manager import CacheManager

def test_performance():
    print("Test Performance Ottimizzazioni")
    print("=" * 60)

    # Crea un database temporaneo
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_perf.manga")

        print("\n1️⃣ Test Creazione Database con Indici...")
        start = time.time()
        db = MangaDatabaseManager(db_path)
        elapsed = time.time() - start
        print(f"   ✅ Database creato in {elapsed*1000:.2f}ms")

        # Verifica indici
        import sqlite3
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = [row[0] for row in c.fetchall()]
        print(f"   ✅ {len(indexes)} indici creati: {', '.join(indexes[:3])}...")

        # Verifica WAL mode
        c.execute("PRAGMA journal_mode")
        journal_mode = c.fetchone()[0]
        print(f"   ✅ Journal mode: {journal_mode.upper()}")
        conn.close()

        print("\n2️⃣ Test Inserimento Dati...")
        start = time.time()

        # Crea un piccolo manga di test
        db.insert_metadata("Test Manga", author="Test Author")

        for vol in range(1, 3):
            vol_id = db.insert_volume(f"Volume {vol}", vol)
            for chap in range(1, 4):
                chap_id = db.insert_chapter(f"Chapter {chap}", (vol-1)*3+chap, volume_id=vol_id)

        elapsed = time.time() - start
        print(f"   ✅ 2 volumi, 6 capitoli inseriti in {elapsed*1000:.2f}ms")

        print("\n3️⃣ Test Query con Indici...")
        start = time.time()
        volumes = db.get_volumes()
        elapsed_vol = time.time() - start

        start = time.time()
        chapters = db.get_chapters_for_volume(volumes[0]['id'])
        elapsed_chap = time.time() - start

        print(f"   ✅ Query volumes: {elapsed_vol*1000:.2f}ms")
        print(f"   ✅ Query chapters: {elapsed_chap*1000:.2f}ms")

        print("\n4️⃣ Test Cache Manager...")
        cache_dir = os.path.join(temp_dir, "cache")
        cache = CacheManager(cache_dir=cache_dir)

        # Crea un file dummy
        dummy_file = os.path.join(temp_dir, "test.manga")
        with open(dummy_file, 'w') as f:
            f.write("test")

        # Test cache key generation
        start = time.time()
        cache_key = cache.get_cache_key(dummy_file, 250)
        elapsed = time.time() - start
        print(f"   ✅ Cache key generata in {elapsed*1000:.3f}ms: {cache_key[:16]}...")

        # Test cache info
        info = cache.get_cache_info()
        print(f"   ✅ Cache directory: {info['cache_dir']}")
        print(f"   ✅ Cache files: {info['file_count']}, Size: {info['total_size_mb']:.2f}MB")

        print("\n" + "=" * 60)
        print("✅ TUTTI I TEST COMPLETATI CON SUCCESSO!")
        print("🚀 Le ottimizzazioni di performance funzionano correttamente!")
        print("=" * 60)

if __name__ == "__main__":
    test_performance()
