"""
CollectionController - Business logic per gestione collezioni.

Responsabilità:
- Creazione nuove collections
- Aggiunta manga a collections
- Gestione collections esistenti
"""

from PyQt5.QtWidgets import QInputDialog, QMessageBox

from src.collections import CollectionManager
from src.logger import get_logger

logger = get_logger(__name__)


class CollectionController:
    """Controller per la gestione delle collections di manga."""

    def __init__(self, view):
        """
        Inizializza il controller per le collections.

        Args:
            view: L'istanza di LibraryView da controllare
        """
        self.view = view
        self.collection_manager = CollectionManager()

    def create_new_collection(self, manga_file):
        """
        Crea una nuova collection e aggiunge il manga (v0.3.0).

        Args:
            manga_file: Percorso del file .manga da aggiungere alla nuova collection
        """
        collection_name, ok = QInputDialog.getText(
            self.view,
            "Nuova Collection",
            "Nome della collection:"
        )

        if not ok or not collection_name.strip():
            return

        collection_name = collection_name.strip()

        # Crea la collection
        if self.collection_manager.create_collection(collection_name):
            # Aggiungi il manga alla collection
            self.collection_manager.add_to_collection(collection_name, manga_file)

            QMessageBox.information(
                self.view,
                "Collection Creata",
                f"Collection '{collection_name}' creata e manga aggiunto!"
            )
            logger.info(f"Collection '{collection_name}' creata con manga: {manga_file}")
        else:
            QMessageBox.warning(
                self.view,
                "Errore",
                f"Collection '{collection_name}' già esistente!"
            )

    def add_to_collection(self, manga_file, collection_name):
        """
        Aggiunge il manga a una collection esistente (v0.3.0).

        Args:
            manga_file: Percorso del file .manga da aggiungere
            collection_name: Nome della collection a cui aggiungere il manga
        """
        self.collection_manager.add_to_collection(collection_name, manga_file)

        QMessageBox.information(
            self.view,
            "Manga Aggiunto",
            f"Manga aggiunto alla collection '{collection_name}'!"
        )
        logger.info(f"Manga {manga_file} aggiunto a collection: {collection_name}")

    def get_all_collections(self):
        """
        Ottiene tutte le collections esistenti.

        Returns:
            list: Lista dei nomi delle collections
        """
        return self.collection_manager.get_all_collections()

    def remove_from_collection(self, manga_file, collection_name):
        """
        Rimuove il manga da una collection.

        Args:
            manga_file: Percorso del file .manga da rimuovere
            collection_name: Nome della collection da cui rimuovere il manga

        Returns:
            bool: True se rimosso con successo, False altrimenti
        """
        try:
            self.collection_manager.remove_from_collection(collection_name, manga_file)
            logger.info(f"Manga {manga_file} rimosso da collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Errore rimozione manga da collection: {e}")
            return False

    def delete_collection(self, collection_name):
        """
        Elimina una collection.

        Args:
            collection_name: Nome della collection da eliminare

        Returns:
            bool: True se eliminata con successo, False altrimenti
        """
        try:
            self.collection_manager.delete_collection(collection_name)
            logger.info(f"Collection '{collection_name}' eliminata")
            return True
        except Exception as e:
            logger.error(f"Errore eliminazione collection: {e}")
            return False

    def get_collection_manga(self, collection_name):
        """
        Ottiene tutti i manga di una collection.

        Args:
            collection_name: Nome della collection

        Returns:
            list: Lista dei percorsi dei file .manga nella collection
        """
        try:
            return self.collection_manager.get_collection_manga(collection_name)
        except Exception as e:
            logger.error(f"Errore recupero manga collection: {e}")
            return []
