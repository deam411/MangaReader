"""
Utility per conversione immagini con supporto threading.

Converte immagini WebP/JFIF in formati compatibili (PNG/JPEG) in background.
"""

import os
import threading
from typing import Callable, Optional
from io import BytesIO
from PIL import Image

from ..constants import MAX_IMAGE_SIZE_MB, IMAGE_CONVERSION_QUALITY
from ..logger import get_logger
from ..exceptions import FileSizeError, ImportError as MangaImportError

logger = get_logger(__name__)


class ImageConversionError(MangaImportError):
    """Eccezione per errori di conversione immagini."""
    pass


def convert_image_sync(file_path: str) -> bytes:
    """
    Conversione sincrona di immagini (versione ottimizzata).

    Args:
        file_path: Percorso al file immagine

    Returns:
        Dati immagine come bytes

    Raises:
        ValueError: Se file troppo grande
        ImageConversionError: Se conversione fallisce
    """
    try:
        # Valida dimensione file
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_IMAGE_SIZE_MB:
            raise FileSizeError(file_size_mb, MAX_IMAGE_SIZE_MB)

        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext in ['.webp', '.jfif']:
            # Converti usando Pillow
            img = Image.open(file_path)

            # Mantieni trasparenza se presente
            if img.mode in ('RGBA', 'LA', 'P'):
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                return buffer.getvalue()
            else:
                # Converti in JPEG per immagini senza trasparenza
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=IMAGE_CONVERSION_QUALITY)
                return buffer.getvalue()
        else:
            # Formati standard, leggi direttamente
            with open(file_path, 'rb') as f:
                return f.read()

    except FileSizeError:
        # Re-raise validation errors
        raise
    except Exception as e:
        raise ImageConversionError(f"Errore conversione {file_path}: {e}")


class ImageConverterThread(threading.Thread):
    """
    Thread worker per conversione immagini in background.

    Esegue la conversione senza bloccare l'UI.
    """

    def __init__(
        self,
        file_path: str,
        callback: Callable[[bytes], None],
        error_callback: Optional[Callable[[Exception], None]] = None
    ):
        """
        Inizializza thread conversione.

        Args:
            file_path: Percorso file da convertire
            callback: Funzione chiamata con risultato (bytes)
            error_callback: Funzione chiamata in caso di errore (opzionale)
        """
        super().__init__(daemon=True)
        self.file_path = file_path
        self.callback = callback
        self.error_callback = error_callback
        self._result = None
        self._error = None

    def run(self):
        """Esegue la conversione in background."""
        try:
            logger.debug(f"Conversione in background: {os.path.basename(self.file_path)}")
            self._result = convert_image_sync(self.file_path)

            # Chiama callback con risultato
            if self.callback:
                self.callback(self._result)

        except Exception as e:
            logger.error(f"Errore conversione thread: {e}")
            self._error = e

            # Chiama error callback se fornito
            if self.error_callback:
                self.error_callback(e)

    def get_result(self, timeout: Optional[float] = None) -> bytes:
        """
        Attende completamento e restituisce risultato.

        Args:
            timeout: Timeout in secondi (None = infinito)

        Returns:
            Dati immagine convertita

        Raises:
            TimeoutError: Se timeout scade
            ImageConversionError: Se conversione fallita
        """
        self.join(timeout)

        if self.is_alive():
            raise TimeoutError("Conversione immagine timeout")

        if self._error:
            raise self._error

        return self._result


class ImageConverterPool:
    """
    Pool di thread per conversioni multiple in parallelo.

    Gestisce code di conversioni con limite thread attivi.
    """

    def __init__(self, max_workers: int = 4):
        """
        Inizializza pool.

        Args:
            max_workers: Numero massimo thread concorrenti
        """
        self.max_workers = max_workers
        self.active_threads = []
        self._lock = threading.Lock()

    def submit(
        self,
        file_path: str,
        callback: Callable[[bytes], None],
        error_callback: Optional[Callable[[Exception], None]] = None
    ) -> ImageConverterThread:
        """
        Sottomette conversione al pool.

        Args:
            file_path: File da convertire
            callback: Callback per risultato
            error_callback: Callback per errori

        Returns:
            Thread creato
        """
        # Cleanup thread terminati
        self._cleanup_finished_threads()

        # Attendi se troppi thread attivi
        while len(self.active_threads) >= self.max_workers:
            self._cleanup_finished_threads()
            threading.Event().wait(0.1)  # Sleep 100ms

        # Crea e avvia thread
        thread = ImageConverterThread(file_path, callback, error_callback)
        thread.start()

        with self._lock:
            self.active_threads.append(thread)

        return thread

    def _cleanup_finished_threads(self):
        """Rimuove thread completati dalla lista."""
        with self._lock:
            self.active_threads = [t for t in self.active_threads if t.is_alive()]

    def wait_all(self, timeout: Optional[float] = None):
        """
        Attende completamento di tutti i thread.

        Args:
            timeout: Timeout totale in secondi
        """
        for thread in self.active_threads:
            thread.join(timeout)

    def active_count(self) -> int:
        """Restituisce numero thread attivi."""
        self._cleanup_finished_threads()
        return len(self.active_threads)
