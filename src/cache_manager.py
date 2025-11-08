"""
Gestore della cache persistent per le cover dei manga.
Salva le cover ridimensionate su disco per velocizzare il caricamento.
"""
import os
import hashlib
import time
from pathlib import Path
from .paths import get_data_dir
from .logger import get_logger
from .exceptions import CacheError

logger = get_logger(__name__)


class CacheManager:
    """Gestisce la cache persistent delle cover manga."""

    def __init__(self, cache_dir=None):
        """
        Inizializza il gestore cache.

        Args:
            cache_dir: Directory cache custom. Se None, usa default in AppData.
        """
        if cache_dir is None:
            data_dir = get_data_dir()
            self.cache_dir = os.path.join(data_dir, "cover_cache")
        else:
            self.cache_dir = cache_dir

        # Crea directory cache se non esiste
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"Cache directory: {self.cache_dir}")

        # Configurazione
        self.max_cache_age_days = 30  # Rimuovi file più vecchi di 30 giorni
        self.max_cache_size_mb = 100  # Limite dimensione cache (100 MB)

    def get_cache_key(self, manga_file_path, width):
        """
        Genera una chiave cache univoca per una cover.

        Args:
            manga_file_path: Percorso del file .manga
            width: Larghezza target della cover

        Returns:
            Stringa hash univoca

        Raises:
            CacheError: Se la generazione della chiave fallisce
        """
        # Usa hash del percorso + dimensione + mtime per invalidazione automatica
        try:
            mtime = os.path.getmtime(manga_file_path)
            cache_string = f"{manga_file_path}_{width}_{mtime}"
            hash_obj = hashlib.md5(cache_string.encode())
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"Errore generazione cache key: {e}")
            raise CacheError(f"Impossibile generare cache key per {manga_file_path}: {e}")

    def get_cache_path(self, cache_key):
        """
        Ottiene il percorso del file cache per una chiave.

        Args:
            cache_key: Chiave cache generata con get_cache_key()

        Returns:
            Percorso completo del file cache
        """
        return os.path.join(self.cache_dir, f"{cache_key}.png")

    def has_cached(self, manga_file_path, width):
        """
        Verifica se esiste una cover in cache.

        Args:
            manga_file_path: Percorso del file .manga
            width: Larghezza target della cover

        Returns:
            True se esiste in cache, False altrimenti
        """
        try:
            cache_key = self.get_cache_key(manga_file_path, width)
            cache_path = self.get_cache_path(cache_key)
            return os.path.exists(cache_path)
        except CacheError:
            # Se fallisce generazione cache key, consideriamo non in cache
            return False

    def get_cached(self, manga_file_path, width):
        """
        Recupera una cover dalla cache.

        Args:
            manga_file_path: Percorso del file .manga
            width: Larghezza target della cover

        Returns:
            Percorso del file cache se esiste, None altrimenti
        """
        try:
            cache_key = self.get_cache_key(manga_file_path, width)
            cache_path = self.get_cache_path(cache_key)

            if os.path.exists(cache_path):
                # Aggiorna access time
                os.utime(cache_path, None)
                logger.debug(f"Cache hit: {os.path.basename(manga_file_path)}")
                return cache_path

            logger.debug(f"Cache miss: {os.path.basename(manga_file_path)}")
            return None
        except CacheError:
            # Se fallisce generazione cache key, cache miss
            logger.debug(f"Cache miss (error): {os.path.basename(manga_file_path)}")
            return None

    def save_to_cache(self, manga_file_path, width, pixmap):
        """
        Salva una cover nella cache.

        Args:
            manga_file_path: Percorso del file .manga
            width: Larghezza della cover
            pixmap: QPixmap da salvare

        Returns:
            True se salvato con successo, False altrimenti
        """
        try:
            cache_key = self.get_cache_key(manga_file_path, width)
            cache_path = self.get_cache_path(cache_key)

            # Salva pixmap come PNG
            success = pixmap.save(cache_path, "PNG")

            if success:
                logger.debug(f"Saved to cache: {os.path.basename(manga_file_path)}")
                return True
            else:
                logger.warning(f"Failed to save cache: {cache_path}")
                raise CacheError(f"Impossibile salvare cache: {cache_path}")

        except CacheError:
            raise
        except Exception as e:
            logger.error(f"Errore salvataggio cache: {e}")
            raise CacheError(f"Errore salvataggio cache per {manga_file_path}: {e}")

    def cleanup_old_cache(self):
        """
        Rimuove file cache vecchi o in eccesso.

        Returns:
            Numero di file rimossi
        """
        try:
            now = time.time()
            removed_count = 0
            total_size = 0

            # Elenca tutti i file cache con info
            cache_files = []
            for filename in os.listdir(self.cache_dir):
                filepath = os.path.join(self.cache_dir, filename)
                if os.path.isfile(filepath) and filename.endswith('.png'):
                    stat = os.stat(filepath)
                    cache_files.append({
                        'path': filepath,
                        'size': stat.st_size,
                        'atime': stat.st_atime,
                        'age_days': (now - stat.st_atime) / (24 * 3600)
                    })
                    total_size += stat.st_size

            # Rimuovi file più vecchi di max_cache_age_days
            for file_info in cache_files:
                if file_info['age_days'] > self.max_cache_age_days:
                    os.remove(file_info['path'])
                    removed_count += 1
                    total_size -= file_info['size']
                    logger.debug(f"Removed old cache: {os.path.basename(file_info['path'])}")

            # Se cache troppo grande, rimuovi file meno usati (LRU)
            max_size_bytes = self.max_cache_size_mb * 1024 * 1024
            if total_size > max_size_bytes:
                # Ordina per access time (meno recente prima)
                cache_files.sort(key=lambda x: x['atime'])

                for file_info in cache_files:
                    if total_size <= max_size_bytes:
                        break

                    os.remove(file_info['path'])
                    removed_count += 1
                    total_size -= file_info['size']
                    logger.debug(f"Removed LRU cache: {os.path.basename(file_info['path'])}")

            if removed_count > 0:
                logger.info(f"Cache cleanup: removed {removed_count} files")

            return removed_count

        except Exception as e:
            logger.error(f"Errore durante cache cleanup: {e}")
            return 0

    def clear_all_cache(self):
        """
        Rimuove TUTTA la cache.

        Returns:
            Numero di file rimossi
        """
        try:
            removed_count = 0
            for filename in os.listdir(self.cache_dir):
                filepath = os.path.join(self.cache_dir, filename)
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    removed_count += 1

            logger.info(f"Cache cleared: {removed_count} files removed")
            return removed_count

        except Exception as e:
            logger.error(f"Errore durante clear cache: {e}")
            return 0

    def get_cache_info(self):
        """
        Ottiene informazioni sulla cache.

        Returns:
            Dict con info: file_count, total_size_mb
        """
        try:
            file_count = 0
            total_size = 0

            for filename in os.listdir(self.cache_dir):
                filepath = os.path.join(self.cache_dir, filename)
                if os.path.isfile(filepath):
                    file_count += 1
                    total_size += os.path.getsize(filepath)

            return {
                'file_count': file_count,
                'total_size_mb': total_size / (1024 * 1024),
                'cache_dir': self.cache_dir
            }

        except Exception as e:
            logger.error(f"Errore ottenimento cache info: {e}")
            return {'file_count': 0, 'total_size_mb': 0, 'cache_dir': self.cache_dir}
