"""Sistema backup e restore libreria."""
import os
import zipfile
from typing import Optional
from ..logger import get_logger

logger = get_logger(__name__)

class BackupManager:
    """Gestore backup libreria manga."""

    def __init__(self, library_path: str):
        self.library_path = library_path
        logger.info(f"BackupManager inizializzato per {library_path}")

    def create_backup(self, backup_path: str, incremental: bool = False) -> bool:
        """
        Crea backup della libreria.

        Args:
            backup_path: Percorso file backup (.zip)
            incremental: Se True, crea backup incrementale

        Returns:
            True se successo
        """
        try:
            logger.info(f"Creazione backup: {backup_path}")
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup di tutti i file .manga
                for root, dirs, files in os.walk(self.library_path):
                    for file in files:
                        if file.endswith('.manga'):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.library_path)
                            zipf.write(file_path, arcname)
                            logger.debug(f"Backup: {arcname}")

            logger.info("Backup completato")
            return True
        except Exception as e:
            logger.error(f"Errore backup: {e}")
            return False

    def restore_backup(self, backup_path: str, target_path: Optional[str] = None) -> bool:
        """
        Ripristina backup.

        Args:
            backup_path: Percorso file backup
            target_path: Directory di destinazione (None = libreria corrente)

        Returns:
            True se successo
        """
        try:
            restore_path = target_path or self.library_path
            logger.info(f"Ripristino backup da {backup_path} a {restore_path}")

            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(restore_path)

            logger.info("Ripristino completato")
            return True
        except Exception as e:
            logger.error(f"Errore ripristino: {e}")
            return False

    def list_backups(self, backup_dir: str) -> list:
        """Lista tutti i backup disponibili."""
        backups = []
        if os.path.exists(backup_dir):
            for file in os.listdir(backup_dir):
                if file.endswith('.zip'):
                    backups.append(os.path.join(backup_dir, file))
        return backups
