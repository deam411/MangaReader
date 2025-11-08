"""
Modulo per importare manga da archivi compressi (CBZ, CBR).

CBZ = Comic Book ZIP (archivio ZIP di immagini)
CBR = Comic Book RAR (archivio RAR di immagini)

v0.2.0: Usa security.py centralizzato per validazione e sanitizzazione.
"""

import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Tuple

from ..database import MangaDatabaseManager
from ..constants import SUPPORTED_IMAGE_FORMATS, MANGA_FILE_EXTENSION, MAX_IMAGE_SIZE_MB
from ..logger import get_logger
from ..exceptions import ArchiveFormatError, ValidationError
# v0.2.0: Import centralizzato security utilities
from ..utils.security import sanitize_filename, is_safe_path, validate_image_size

logger = get_logger(__name__)

# Prova a importare rarfile (opzionale)
try:
    import rarfile
    RAR_AVAILABLE = True
except ImportError:
    RAR_AVAILABLE = False
    logger.warning("rarfile non disponibile. Import CBR disabilitato.")


class ArchiveImporter:
    """
    Gestisce l'importazione di manga da archivi compressi.

    Formati supportati:
    - CBZ (ZIP): Sempre disponibile
    - CBR (RAR): Richiede il modulo rarfile

    v0.2.0: Usa funzioni security centralizzate da src.utils.security
    """

    def __init__(self):
        self.temp_dir = None

    @staticmethod
    def detect_archive_type(file_path: str) -> Optional[str]:
        """
        Rileva il tipo di archivio dal file.

        Args:
            file_path: Percorso al file da analizzare

        Returns:
            'cbz' per ZIP, 'cbr' per RAR, None se non riconosciuto
        """
        ext = Path(file_path).suffix.lower()

        if ext in ['.cbz', '.zip']:
            return 'cbz'
        elif ext in ['.cbr', '.rar']:
            return 'cbr'

        # Fallback: prova a rilevare dal magic number
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(8)

                # ZIP magic: PK\x03\x04
                if magic.startswith(b'PK\x03\x04'):
                    return 'cbz'

                # RAR magic: Rar!\x1a\x07 (RAR 5.0) or Rar!\x1a\x07\x01 (RAR 4.x)
                if magic.startswith(b'Rar!'):
                    return 'cbr'

        except Exception as e:
            logger.error(f"Errore rilevamento tipo archivio: {e}")

        return None

    @staticmethod
    def is_image_file(filename: str) -> bool:
        """
        Verifica se un file è un'immagine supportata.

        Args:
            filename: Nome del file

        Returns:
            True se è un'immagine supportata
        """
        ext = Path(filename).suffix.lower()
        return ext in SUPPORTED_IMAGE_FORMATS

    def extract_images_from_zip(self, zip_path: str) -> List[Tuple[str, bytes]]:
        """
        Estrae immagini da un archivio ZIP.

        Args:
            zip_path: Percorso all'archivio ZIP

        Returns:
            Lista di tuple (filename, image_data)
        """
        images = []

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Ottieni lista file ordinata
                file_list = sorted(zip_file.namelist())

                for filename in file_list:
                    # Salta directory e file nascosti
                    if filename.endswith('/') or Path(filename).name.startswith('.'):
                        continue

                    if self.is_image_file(filename):
                        try:
                            # v0.2.0: Usa sanitize_filename centralizzato
                            safe_filename = sanitize_filename(Path(filename).name)

                            image_data = zip_file.read(filename)

                            # v0.2.0: Usa validate_image_size centralizzato
                            if not validate_image_size(image_data, MAX_IMAGE_SIZE_MB):
                                logger.warning(f"Immagine troppo grande saltata: {safe_filename}")
                                continue

                            images.append((safe_filename, image_data))
                            logger.debug(f"Estratta immagine: {safe_filename}")
                        except ValidationError as e:
                            logger.warning(f"Filename invalido saltato: {filename} - {e}")
                        except Exception as e:
                            logger.error(f"Errore estrazione {filename}: {e}")

            logger.info(f"Estratte {len(images)} immagini da {zip_path}")
            return images

        except zipfile.BadZipFile:
            logger.error(f"File ZIP corrotto: {zip_path}")
            return []
        except Exception as e:
            logger.error(f"Errore estrazione ZIP: {e}")
            return []

    def extract_images_from_rar(self, rar_path: str) -> List[Tuple[str, bytes]]:
        """
        Estrae immagini da un archivio RAR.

        Args:
            rar_path: Percorso all'archivio RAR

        Returns:
            Lista di tuple (filename, image_data)
        """
        if not RAR_AVAILABLE:
            logger.error("rarfile non installato. Impossibile estrarre CBR.")
            return []

        images = []

        try:
            with rarfile.RarFile(rar_path, 'r') as rar_file:
                # Ottieni lista file ordinata
                file_list = sorted(rar_file.namelist())

                for filename in file_list:
                    # Salta directory e file nascosti
                    if filename.endswith('/') or Path(filename).name.startswith('.'):
                        continue

                    if self.is_image_file(filename):
                        try:
                            # v0.2.0: Usa sanitize_filename centralizzato
                            safe_filename = sanitize_filename(Path(filename).name)

                            image_data = rar_file.read(filename)

                            # v0.2.0: Usa validate_image_size centralizzato
                            if not validate_image_size(image_data, MAX_IMAGE_SIZE_MB):
                                logger.warning(f"Immagine troppo grande saltata: {safe_filename}")
                                continue

                            images.append((safe_filename, image_data))
                            logger.debug(f"Estratta immagine: {safe_filename}")
                        except ValidationError as e:
                            logger.warning(f"Filename invalido saltato: {filename} - {e}")
                        except Exception as e:
                            logger.error(f"Errore estrazione {filename}: {e}")

            logger.info(f"Estratte {len(images)} immagini da {rar_path}")
            return images

        except rarfile.BadRarFile:
            logger.error(f"File RAR corrotto: {rar_path}")
            return []
        except Exception as e:
            logger.error(f"Errore estrazione RAR: {e}")
            return []

    def import_archive(
        self,
        archive_path: str,
        output_path: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        volume_name: Optional[str] = None,
        chapter_name: Optional[str] = None
    ) -> bool:
        """
        Importa un archivio manga e lo converte in formato .manga.

        Args:
            archive_path: Percorso all'archivio CBZ/CBR
            output_path: Percorso di output per il file .manga
            title: Titolo del manga (default: nome file)
            author: Autore (opzionale)
            volume_name: Nome volume (default: "Volume 1")
            chapter_name: Nome capitolo (default: "Chapter 1")

        Returns:
            True se l'import è riuscito, False altrimenti
        """
        # Rileva tipo archivio
        archive_type = self.detect_archive_type(archive_path)

        if not archive_type:
            logger.error(f"Tipo archivio non riconosciuto: {archive_path}")
            return False

        logger.info(f"Importazione {archive_type.upper()} da: {archive_path}")

        # Estrai immagini
        if archive_type == 'cbz':
            images = self.extract_images_from_zip(archive_path)
        elif archive_type == 'cbr':
            images = self.extract_images_from_rar(archive_path)
        else:
            logger.error(f"Tipo archivio non supportato: {archive_type}")
            return False

        if not images:
            logger.error("Nessuna immagine trovata nell'archivio")
            return False

        # Determina metadata di default
        if not title:
            title = Path(archive_path).stem

        if not volume_name:
            volume_name = "Volume 1"

        if not chapter_name:
            chapter_name = "Chapter 1"

        # Assicurati che output_path abbia estensione .manga
        if not output_path.endswith(MANGA_FILE_EXTENSION):
            output_path = output_path + MANGA_FILE_EXTENSION

        # Valida output_path per prevenire path traversal
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if not os.path.exists(output_dir):
            logger.error(f"Directory output non esiste: {output_dir}")
            return False

        # Crea database manga
        try:
            # Rimuovi file esistente se presente
            if os.path.exists(output_path):
                os.remove(output_path)

            db_manager = MangaDatabaseManager(output_path)

            # Inserisci metadata
            db_manager.insert_metadata(
                title=title,
                author=author,
                description=f"Importato da {Path(archive_path).name}",
                language="",
                year=None,
                tags=""
            )
            logger.info(f"Metadata inseriti: {title}")

            # Crea volume
            volume_id = db_manager.insert_volume(volume_name, 1)
            logger.info(f"Volume creato: {volume_name}")

            # Crea capitolo
            chapter_id = db_manager.insert_chapter(chapter_name, 1, volume_id)
            logger.info(f"Capitolo creato: {chapter_name}")

            # Usa directory temporanea per salvare immagini
            self.temp_dir = tempfile.mkdtemp()

            try:
                # Inserisci pagine
                for page_num, (filename, image_data) in enumerate(images, start=1):
                    # v0.2.0: Sanitizza filename per prevenire path traversal vulnerability
                    safe_filename = sanitize_filename(filename)
                    temp_image_path = os.path.join(self.temp_dir, safe_filename)

                    # v0.2.0: Verifica path traversal protection con security.py
                    if not is_safe_path(self.temp_dir, temp_image_path):
                        logger.error(f"Path traversal rilevato per: {filename}")
                        continue

                    with open(temp_image_path, 'wb') as f:
                        f.write(image_data)

                    # Inserisci nel database
                    if db_manager.insert_page(chapter_id, page_num, temp_image_path):
                        logger.debug(f"Pagina {page_num}/{len(images)} inserita")
                    else:
                        logger.error(f"Errore inserimento pagina {page_num}")

                logger.info(f"Import completato: {len(images)} pagine importate")
                return True

            finally:
                # Pulisci directory temporanea
                if self.temp_dir and os.path.exists(self.temp_dir):
                    shutil.rmtree(self.temp_dir, ignore_errors=True)
                    self.temp_dir = None

        except Exception as e:
            logger.error(f"Errore durante import: {e}")
            # Rimuovi file .manga parziale
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            return False

    @staticmethod
    def get_supported_formats() -> List[str]:
        """
        Restituisce lista formati supportati.

        Returns:
            Lista di estensioni supportate
        """
        formats = ['.cbz', '.zip']

        if RAR_AVAILABLE:
            formats.extend(['.cbr', '.rar'])

        return formats

    @staticmethod
    def is_rar_supported() -> bool:
        """Verifica se import RAR è disponibile."""
        return RAR_AVAILABLE
