"""Sistema collections per organizzazione manga."""
from typing import List, Dict
from ..logger import get_logger

logger = get_logger(__name__)

class CollectionManager:
    """Gestore collections manga."""

    def __init__(self):
        self.collections: Dict[str, List[str]] = {}
        logger.info("CollectionManager inizializzato")

    def create_collection(self, name: str) -> bool:
        """Crea una nuova collection."""
        if name not in self.collections:
            self.collections[name] = []
            logger.info(f"Collection creata: {name}")
            return True
        return False

    def add_to_collection(self, collection_name: str, manga_path: str):
        """Aggiunge manga a collection."""
        if collection_name in self.collections:
            self.collections[collection_name].append(manga_path)
            logger.debug(f"Manga aggiunto a {collection_name}")

    def get_collection(self, name: str) -> List[str]:
        """Ritorna i manga in una collection."""
        return self.collections.get(name, [])

    def get_all_collections(self) -> List[str]:
        """Ritorna tutte le collections."""
        return list(self.collections.keys())
