"""
UpdateController - Business logic per gestione aggiornamenti app.

Responsabilità:
- Controllo disponibilità aggiornamenti
- Download e installazione updates
- Gestione versioning
"""

from src.logger import get_logger

logger = get_logger(__name__)


class UpdateController:
    """Controller per la gestione degli aggiornamenti dell'applicazione."""

    def __init__(self, view):
        """
        Inizializza il controller per gli aggiornamenti.

        Args:
            view: L'istanza di LibraryView da controllare
        """
        self.view = view

    def check_for_updates(self):
        """
        Controlla se sono disponibili aggiornamenti.

        Returns:
            dict: Informazioni sull'aggiornamento disponibile, None se non ci sono aggiornamenti
        """
        from src.updater import check_for_updates

        try:
            update_info = check_for_updates()
            return update_info
        except Exception as e:
            logger.error(f"Errore durante il controllo aggiornamenti: {e}")
            return None

    def download_update(self, update_url, output_path):
        """
        Scarica un aggiornamento.

        Args:
            update_url: URL dell'aggiornamento da scaricare
            output_path: Percorso dove salvare l'aggiornamento

        Returns:
            bool: True se il download è riuscito, False altrimenti
        """
        from src.updater import download_update

        try:
            success = download_update(update_url, output_path)
            return success
        except Exception as e:
            logger.error(f"Errore durante il download dell'aggiornamento: {e}")
            return False

    def install_update(self, update_path):
        """
        Installa un aggiornamento.

        Args:
            update_path: Percorso del file di aggiornamento da installare

        Returns:
            bool: True se l'installazione è stata avviata con successo, False altrimenti
        """
        from src.updater import install_update

        try:
            success = install_update(update_path)
            return success
        except Exception as e:
            logger.error(f"Errore durante l'installazione dell'aggiornamento: {e}")
            return False

    def get_update_info_text(self, update_info):
        """
        Genera il testo informativo sull'aggiornamento.

        Args:
            update_info: Dizionario con le informazioni sull'aggiornamento

        Returns:
            str: Testo formattato con le informazioni sull'aggiornamento
        """
        from src.updater import get_update_info_text

        try:
            info_text = get_update_info_text(update_info)
            return info_text
        except Exception as e:
            logger.error(f"Errore durante la generazione del testo info: {e}")
            return ""
