"""Sistema collections per organizzazione manga con persistenza database."""
import sqlite3
import os
from typing import List, Dict, Optional
from ..logger import get_logger
from ..paths import get_app_data_dir

logger = get_logger(__name__)

class CollectionManager:
    """
    Gestore collections manga con persistenza database.

    Le collections sono salvate in un database SQLite separato
    per permettere organizzazione cross-manga.
    """

    def __init__(self):
        self.db_path = os.path.join(get_app_data_dir(), "collections.db")
        self._closed = False

        # Assicurati che la directory padre esista
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self._init_database()
        self.collections: Dict[str, List[str]] = {}
        self._load_collections()
        logger.info(f"CollectionManager inizializzato con database: {self.db_path}")

    def _init_database(self):
        """Crea lo schema database per le collections."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Tabella collections
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        created_at INTEGER DEFAULT (strftime('%s', 'now'))
                    )
                ''')

                # Tabella collection_items (relazione many-to-many)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collection_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        collection_id INTEGER NOT NULL,
                        manga_path TEXT NOT NULL,
                        added_at INTEGER DEFAULT (strftime('%s', 'now')),
                        FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
                        UNIQUE(collection_id, manga_path)
                    )
                ''')

                # Indici per performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_collection_items_collection_id
                    ON collection_items(collection_id)
                ''')

                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_collection_items_manga_path
                    ON collection_items(manga_path)
                ''')

                conn.commit()
                logger.debug("Schema collections database creato")
        except sqlite3.Error as e:
            logger.error(f"Errore creazione database collections: {e}")

    def _load_collections(self):
        """Carica tutte le collections dal database in memoria."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Carica collections
                cursor.execute('SELECT id, name FROM collections')
                collections_data = cursor.fetchall()

                self.collections = {}
                for collection in collections_data:
                    coll_id = collection['id']
                    coll_name = collection['name']

                    # Carica manga items per questa collection
                    cursor.execute('''
                        SELECT manga_path FROM collection_items
                        WHERE collection_id = ?
                        ORDER BY added_at
                    ''', (coll_id,))

                    items = cursor.fetchall()
                    self.collections[coll_name] = [item['manga_path'] for item in items]

                logger.debug(f"Caricate {len(self.collections)} collections dal database")
        except sqlite3.Error as e:
            logger.error(f"Errore caricamento collections: {e}")
            self.collections = {}

    def create_collection(self, name: str, description: str = "") -> bool:
        """
        Crea una nuova collection.

        Args:
            name: Nome della collection
            description: Descrizione opzionale

        Returns:
            True se creata, False se esiste già
        """
        if self._closed:
            logger.warning("CollectionManager is closed")
            return False

        if name in self.collections:
            return False

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO collections (name, description)
                    VALUES (?, ?)
                ''', (name, description))
                conn.commit()

                self.collections[name] = []
                logger.info(f"Collection creata: {name}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Collection già esistente: {name}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Errore creazione collection: {e}")
            return False

    def delete_collection(self, collection_id_or_name) -> bool:
        """
        Elimina una collection.

        Args:
            collection_id_or_name: ID (int) o nome (str) della collection

        Returns:
            True se eliminata, False se non esiste
        """
        try:
            # Determina se è un ID o un nome
            if isinstance(collection_id_or_name, int):
                # È un ID, cerca il nome corrispondente
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT name FROM collections WHERE id = ?', (collection_id_or_name,))
                    row = cursor.fetchone()
                    if not row:
                        logger.warning(f"Collection ID non esistente: {collection_id_or_name}")
                        return False
                    name = row['name']
            else:
                # È un nome
                name = collection_id_or_name
                if name not in self.collections:
                    return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Prima cancella tutti gli items della collection (cascade)
                cursor.execute('SELECT id FROM collections WHERE name = ?', (name,))
                result = cursor.fetchone()
                if result:
                    collection_id = result[0]
                    cursor.execute('DELETE FROM collection_items WHERE collection_id = ?', (collection_id,))

                # Poi cancella la collection stessa
                cursor.execute('DELETE FROM collections WHERE name = ?', (name,))
                conn.commit()

                del self.collections[name]
                logger.info(f"Collection eliminata: {name}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore eliminazione collection: {e}")
            return False

    def add_to_collection(self, collection_id_or_name, manga_path: str) -> bool:
        """
        Aggiunge manga a collection.

        Args:
            collection_id_or_name: ID (int) o nome (str) della collection
            manga_path: Path al file .manga

        Returns:
            True se aggiunto, False altrimenti
        """
        try:
            # Determina se è un ID o un nome
            if isinstance(collection_id_or_name, int):
                # È un ID, cerca il nome corrispondente
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT name FROM collections WHERE id = ?', (collection_id_or_name,))
                    row = cursor.fetchone()
                    if not row:
                        logger.warning(f"Collection ID non esistente: {collection_id_or_name}")
                        return False
                    collection_name = row['name']
            else:
                # È un nome
                collection_name = collection_id_or_name
                if collection_name not in self.collections:
                    logger.warning(f"Collection non esistente: {collection_name}")
                    return False

            if manga_path in self.collections[collection_name]:
                logger.debug(f"Manga già in collection {collection_name}")
                return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get collection_id
                cursor.execute('SELECT id FROM collections WHERE name = ?', (collection_name,))
                result = cursor.fetchone()
                if not result:
                    return False

                collection_id = result[0]

                # Add manga to collection
                cursor.execute('''
                    INSERT INTO collection_items (collection_id, manga_path)
                    VALUES (?, ?)
                ''', (collection_id, manga_path))
                conn.commit()

                self.collections[collection_name].append(manga_path)
                logger.debug(f"Manga aggiunto a {collection_name}: {manga_path}")
                return True
        except sqlite3.IntegrityError:
            logger.debug(f"Manga già in collection")
            return False
        except sqlite3.Error as e:
            logger.error(f"Errore aggiunta manga a collection: {e}")
            return False

    def remove_from_collection(self, collection_id_or_name, manga_path: str) -> bool:
        """
        Rimuove manga da collection.

        Args:
            collection_id_or_name: ID (int) o nome (str) della collection
            manga_path: Path al file .manga

        Returns:
            True se rimosso, False altrimenti
        """
        try:
            # Determina se è un ID o un nome
            if isinstance(collection_id_or_name, int):
                # È un ID, cerca il nome corrispondente
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT name FROM collections WHERE id = ?', (collection_id_or_name,))
                    row = cursor.fetchone()
                    if not row:
                        logger.warning(f"Collection ID non esistente: {collection_id_or_name}")
                        return False
                    collection_name = row['name']
            else:
                # È un nome
                collection_name = collection_id_or_name
                if collection_name not in self.collections:
                    return False

            if manga_path not in self.collections[collection_name]:
                return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get collection_id
                cursor.execute('SELECT id FROM collections WHERE name = ?', (collection_name,))
                result = cursor.fetchone()
                if not result:
                    return False

                collection_id = result[0]

                # Remove manga from collection
                cursor.execute('''
                    DELETE FROM collection_items
                    WHERE collection_id = ? AND manga_path = ?
                ''', (collection_id, manga_path))
                conn.commit()

                self.collections[collection_name].remove(manga_path)
                logger.debug(f"Manga rimosso da {collection_name}: {manga_path}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore rimozione manga da collection: {e}")
            return False

    def get_collection(self, name: str) -> List[str]:
        """
        Ritorna i manga in una collection.

        Args:
            name: Nome della collection

        Returns:
            Lista di path ai file .manga
        """
        return self.collections.get(name, [])

    def get_collection_items(self, collection_id_or_name):
        """
        Ritorna gli items di una collection con metadata.

        Args:
            collection_id_or_name: ID (int) o nome (str) della collection

        Returns:
            Lista di dict con manga_path e added_at
        """
        try:
            # Determina se è un ID o un nome e ottieni l'ID
            if isinstance(collection_id_or_name, int):
                collection_id = collection_id_or_name
            else:
                # È un nome, cerca l'ID
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT id FROM collections WHERE name = ?', (collection_id_or_name,))
                    row = cursor.fetchone()
                    if not row:
                        return []
                    collection_id = row['id']

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT manga_path, added_at
                    FROM collection_items
                    WHERE collection_id = ?
                    ORDER BY added_at
                ''', (collection_id,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Errore recupero items collection: {e}")
            return []

    def get_all_collections(self) -> List[Dict]:
        """
        Ritorna tutte le collections con metadata completo.

        Returns:
            Lista di dict con info collection (id, name, description, created_at)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, description, created_at
                    FROM collections
                    ORDER BY created_at ASC
                ''')
                collections = [dict(row) for row in cursor.fetchall()]
                logger.debug(f"Recuperate {len(collections)} collections")
                return collections
        except sqlite3.Error as e:
            logger.error(f"Errore recupero collections: {e}")
            return []

    def get_collections_for_manga(self, manga_path: str) -> List[Dict]:
        """
        Ritorna tutte le collections che contengono un manga.

        Args:
            manga_path: Path al file .manga

        Returns:
            Lista di dict con info collection (id, name, description)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT c.id, c.name, c.description, c.created_at
                    FROM collections c
                    INNER JOIN collection_items ci ON c.id = ci.collection_id
                    WHERE ci.manga_path = ?
                    ORDER BY c.name
                ''', (manga_path,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Errore recupero collections per manga: {e}")
            return []

    def rename_collection(self, collection_id_or_name, new_name: str) -> bool:
        """
        Rinomina una collection.

        Args:
            collection_id_or_name: ID (int) o nome (str) della collection
            new_name: Nuovo nome

        Returns:
            True se rinominata, False altrimenti
        """
        try:
            # Determina se è un ID o un nome
            if isinstance(collection_id_or_name, int):
                # È un ID, cerca il nome corrispondente
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT name FROM collections WHERE id = ?', (collection_id_or_name,))
                    row = cursor.fetchone()
                    if not row:
                        logger.warning(f"Collection ID non esistente: {collection_id_or_name}")
                        return False
                    old_name = row['name']
            else:
                # È un nome
                old_name = collection_id_or_name
                if old_name not in self.collections:
                    logger.warning(f"Collection non esistente: {old_name}")
                    return False

            if new_name in self.collections:
                logger.warning(f"Collection già esistente con nome: {new_name}")
                return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE collections SET name = ? WHERE name = ?', (new_name, old_name))
                conn.commit()

                # Aggiorna cache in memoria
                self.collections[new_name] = self.collections.pop(old_name)
                logger.info(f"Collection rinominata: {old_name} → {new_name}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore rinomina collection: {e}")
            return False

    def update_collection_description(self, collection_id_or_name, description: str) -> bool:
        """
        Aggiorna la descrizione di una collection.

        Args:
            collection_id_or_name: ID (int) o nome (str) della collection
            description: Nuova descrizione

        Returns:
            True se aggiornata, False altrimenti
        """
        try:
            # Determina se è un ID o un nome
            if isinstance(collection_id_or_name, int):
                # È un ID, cerca il nome corrispondente
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT name FROM collections WHERE id = ?', (collection_id_or_name,))
                    row = cursor.fetchone()
                    if not row:
                        logger.warning(f"Collection ID non esistente: {collection_id_or_name}")
                        return False
                    name = row['name']
            else:
                # È un nome
                name = collection_id_or_name
                if name not in self.collections:
                    logger.warning(f"Collection non esistente: {name}")
                    return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE collections SET description = ? WHERE name = ?', (description, name))
                conn.commit()

                logger.info(f"Descrizione aggiornata per collection: {name}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore aggiornamento descrizione: {e}")
            return False

    def get_collection_count(self, collection_id_or_name=None) -> int:
        """
        Ritorna il numero di items in una collection, oppure il numero totale di collections.

        Args:
            collection_id_or_name: ID (int) o nome (str) della collection. Se None, ritorna il totale delle collections.

        Returns:
            Numero di items nella collection, oppure numero totale di collections
        """
        if collection_id_or_name is None:
            # Nessun parametro: ritorna numero totale collections
            return len(self.collections)

        # Parametro fornito: conta items nella collection
        try:
            # Determina se è un ID o un nome e ottieni l'ID
            if isinstance(collection_id_or_name, int):
                collection_id = collection_id_or_name
            else:
                # È un nome, cerca l'ID
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT id FROM collections WHERE name = ?', (collection_id_or_name,))
                    row = cursor.fetchone()
                    if not row:
                        return 0
                    collection_id = row['id']

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM collection_items WHERE collection_id = ?', (collection_id,))
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Errore conteggio items collection: {e}")
            return 0

    def close(self) -> None:
        """
        Chiude le connessioni al database.

        Questo metodo è fornito per compatibilità con i test.
        CollectionManager usa context manager per le connessioni,
        quindi non mantiene connessioni persistenti da chiudere.
        """
        self._closed = True
        logger.debug("CollectionManager closed")
