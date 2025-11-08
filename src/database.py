import sqlite3
import os
from PIL import Image # Importa la libreria Pillow
from .logger import get_logger
from .exceptions import (
    DatabaseError,
    DatabaseSchemaError,
    DatabaseConnectionError,
    DatabaseQueryError,
    ValidationError
)
from .utils.validation import (
    validate_title,
    validate_author,
    validate_description,
    validate_language,
    validate_year,
    validate_tags,
    validate_chapter_name,
    validate_volume_name,
    validate_order
)

logger = get_logger(__name__)

class MangaDatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        logger.debug(f"MangaDatabaseManager: __init__ called for db_path: {db_path}")
        logger.debug(f"Loading database.py from: {__file__}")
        # create_manga_db_schema is called here to ensure the database is ready
        self.create_manga_db_schema()
        self.migrate_schema_to_v2() # Chiama la funzione di migrazione dello schema
        self.create_performance_indexes() # Crea indici per performance ottimali
        self.optimize_database_settings() # Ottimizza le impostazioni del database

    def create_manga_db_schema(self):
        """
        Crea lo schema del database per un file .manga.

        Returns:
            True in caso di successo

        Raises:
            DatabaseSchemaError: Se la creazione dello schema fallisce
            DatabaseConnectionError: Se la connessione al database fallisce
        """
        logger.debug(f"MangaDatabaseManager: create_manga_db_schema called for db_path: {self.db_path}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()

                # Tabella metadata
                c.execute('''
                    CREATE TABLE IF NOT EXISTS metadata (
                        title TEXT,
                        author TEXT,
                        description TEXT,
                        language TEXT,
                        cover BLOB,
                        year INTEGER,
                        tags TEXT
                    )
                ''')

                # Tabella volumes
                c.execute('''
                    CREATE TABLE IF NOT EXISTS volumes (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        "order" INTEGER,
                        cover BLOB
                    )
                ''')

                # Tabella chapters
                c.execute('''
                    CREATE TABLE IF NOT EXISTS chapters (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        "order" INTEGER,
                        description TEXT,
                        volume_id INTEGER,
                        FOREIGN KEY (volume_id) REFERENCES volumes (id)
                    )
                ''')

                # Tabella pages
                c.execute('''
                    CREATE TABLE IF NOT EXISTS pages (
                        chapter_id INTEGER,
                        page_number INTEGER,
                        image_data BLOB,
                        FOREIGN KEY (chapter_id) REFERENCES chapters (id)
                    )
                ''')

                # Tabella history
                c.execute('''
                    CREATE TABLE IF NOT EXISTS history (
                        user TEXT,
                        chapter_id INTEGER,
                        page_number INTEGER,
                        timestamp INTEGER,
                        notes TEXT
                    )
                ''')

                # Tabella bookmarks
                c.execute('''
                    CREATE TABLE IF NOT EXISTS bookmarks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user TEXT DEFAULT 'default',
                        chapter_id INTEGER,
                        page_number INTEGER,
                        name TEXT,
                        timestamp INTEGER,
                        FOREIGN KEY (chapter_id) REFERENCES chapters (id)
                    )
                ''')

                conn.commit()
                logger.debug(f"MangaDatabaseManager: create_manga_db_schema successful for db_path: {self.db_path}")
                return True
        except sqlite3.OperationalError as e:
            logger.error(f"MangaDatabaseManager: Errore connessione database per {self.db_path}: {e}")
            raise DatabaseConnectionError(f"Impossibile connettersi al database {self.db_path}") from e
        except sqlite3.Error as e:
            logger.error(f"MangaDatabaseManager: Errore durante la creazione dello schema del database per {self.db_path}: {e}")
            raise DatabaseSchemaError(f"Errore creazione schema per {self.db_path}") from e

    def create_performance_indexes(self):
        """
        Crea indici per ottimizzare le performance delle query.
        Gli indici vengono creati solo se non esistono già.
        """
        logger.debug(f"MangaDatabaseManager: create_performance_indexes called for db_path: {self.db_path}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()

                # Indice su chapters.volume_id (FK usata nei JOIN)
                c.execute('''
                    CREATE INDEX IF NOT EXISTS idx_chapters_volume_id
                    ON chapters(volume_id)
                ''')

                # Indice su pages.chapter_id (FK usata per caricare pagine)
                c.execute('''
                    CREATE INDEX IF NOT EXISTS idx_pages_chapter_id
                    ON pages(chapter_id)
                ''')

                # Indice composito su pages per query ordinate
                c.execute('''
                    CREATE INDEX IF NOT EXISTS idx_pages_chapter_page
                    ON pages(chapter_id, page_number)
                ''')

                # Indice su bookmarks.chapter_id (FK usata per caricare segnalibri)
                c.execute('''
                    CREATE INDEX IF NOT EXISTS idx_bookmarks_chapter_id
                    ON bookmarks(chapter_id)
                ''')

                # Indice composito su bookmarks per query per utente
                c.execute('''
                    CREATE INDEX IF NOT EXISTS idx_bookmarks_user_chapter
                    ON bookmarks(user, chapter_id)
                ''')

                # Fix: Indice su bookmarks.timestamp per ordinamento veloce
                c.execute('''
                    CREATE INDEX IF NOT EXISTS idx_bookmarks_timestamp
                    ON bookmarks(timestamp DESC)
                ''')

                # Indice su history.chapter_id (per calcolare progresso)
                c.execute('''
                    CREATE INDEX IF NOT EXISTS idx_history_chapter_id
                    ON history(chapter_id)
                ''')

                # Indice composito su history per query per utente
                c.execute('''
                    CREATE INDEX IF NOT EXISTS idx_history_user_chapter
                    ON history(user, chapter_id, timestamp DESC)
                ''')

                # Indice su chapters.order per ordinamento veloce
                c.execute('''
                    CREATE INDEX IF NOT EXISTS idx_chapters_order
                    ON chapters("order")
                ''')

                # Indice su volumes.order per ordinamento veloce
                c.execute('''
                    CREATE INDEX IF NOT EXISTS idx_volumes_order
                    ON volumes("order")
                ''')

                conn.commit()
                logger.info(f"Indici di performance creati con successo per {self.db_path}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante la creazione degli indici per {self.db_path}: {e}")
            return False

    def optimize_database_settings(self):
        """
        Ottimizza le impostazioni SQLite per performance migliori.
        Abilita WAL mode, aumenta cache size, e ottimizza altri parametri.
        """
        logger.debug(f"MangaDatabaseManager: optimize_database_settings called for db_path: {self.db_path}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()

                # Abilita WAL mode per migliori performance di lettura concorrente
                # WAL permette letture mentre si scrive, e migliora le performance generali
                c.execute('PRAGMA journal_mode=WAL')

                # Aumenta dimensione cache (default 2MB -> 10MB)
                # Più cache = meno accessi disco = più veloce
                c.execute('PRAGMA cache_size=-10000')  # Negativo = kilobytes (10MB)

                # Abilita memory-mapped I/O per file fino a 256MB
                # Accesso diretto alla memoria invece di chiamate di sistema
                c.execute('PRAGMA mmap_size=268435456')  # 256MB

                # Ottimizza il numero di pagine nel pool di cache temporaneo
                c.execute('PRAGMA temp_store=MEMORY')

                # Sincronizzazione NORMAL è più veloce e ancora sicura
                # (FULL è troppo lento, OFF è pericoloso)
                c.execute('PRAGMA synchronous=NORMAL')

                # Analizza il database per ottimizzare il query planner
                # Questo aiuta SQLite a scegliere i migliori indici
                c.execute('ANALYZE')

                conn.commit()
                logger.info(f"Impostazioni database ottimizzate per {self.db_path}")
                return True
        except sqlite3.Error as e:
            logger.warning(f"Errore durante l'ottimizzazione delle impostazioni database: {e}")
            # Non è un errore critico, continua comunque
            return False

    def migrate_schema_to_v2(self):
        """
        Migra lo schema del database alla versione 2: aggiunge la colonna volume_id alla tabella chapters.

        Returns:
            True in caso di successo

        Raises:
            DatabaseSchemaError: Se la migrazione fallisce
        """
        logger.debug(f"MangaDatabaseManager: migrate_schema_to_v2 called for db_path: {self.db_path}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()

                # Controlla se la colonna volume_id esiste già nella tabella chapters
                c.execute("PRAGMA table_info(chapters)")
                columns = [col[1] for col in c.fetchall()]
                if 'volume_id' not in columns:
                    logger.info(f"Aggiunta colonna 'volume_id' alla tabella 'chapters' in {self.db_path}")
                    c.execute("ALTER TABLE chapters ADD COLUMN volume_id INTEGER")

                    # Crea un volume di default se non esiste
                    c.execute("SELECT id FROM volumes WHERE name = 'Default Volume' LIMIT 1")
                    default_volume_id = c.fetchone()
                    if not default_volume_id:
                        c.execute("INSERT INTO volumes (name, 'order') VALUES ('Default Volume', 1)")
                        default_volume_id = c.lastrowid
                        logger.info(f"Creato 'Default Volume' con ID: {default_volume_id}")
                    else:
                        default_volume_id = default_volume_id[0]
                        logger.debug(f"'Default Volume' esistente con ID: {default_volume_id}")

                    # Assegna tutti i capitoli esistenti al volume di default
                    c.execute("UPDATE chapters SET volume_id = ? WHERE volume_id IS NULL", (default_volume_id,))
                    logger.info("Capitoli esistenti assegnati a 'Default Volume'")
                else:
                    logger.debug("Colonna 'volume_id' già presente nella tabella 'chapters'. Nessuna migrazione necessaria")

                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante la migrazione dello schema del database per {self.db_path}: {e}")
            raise DatabaseSchemaError(f"Errore migrazione schema per {self.db_path}") from e

    def insert_metadata(self, title, author=None, description=None, language=None, cover=None, year=None, tags=None):
        """
        Inserisce i metadati per il manga con validazione input.

        Args:
            title: Titolo manga (required)
            author: Autore (optional)
            description: Descrizione (optional)
            language: Lingua (optional)
            cover: Cover image blob (optional)
            year: Anno pubblicazione (optional)
            tags: Tags comma-separated (optional)

        Returns:
            True in caso di successo, False altrimenti

        Raises:
            ValidationError: Se metadata non validi
        """
        try:
            # Valida e sanitizza input
            title = validate_title(title)
            author = validate_author(author)
            description = validate_description(description)
            language = validate_language(language)
            year = validate_year(year)
            tags = validate_tags(tags)

            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO metadata (title, author, description, language, cover, year, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (title, author, description, language, cover, year, tags))
                conn.commit()
                return True
        except ValidationError:
            # Re-raise validation errors
            raise
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'inserimento dei metadati: {e}")
            return False

    def update_metadata(self, title, author=None, description=None, language=None, cover=None, year=None, tags=None):
        """
        Aggiorna i metadati per il manga.
        Restituisce True in caso di successo, False altrimenti.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    UPDATE metadata SET
                        author = ?,
                        description = ?,
                        language = ?,
                        cover = ?,
                        year = ?,
                        tags = ?
                    WHERE title = ?
                ''', (author, description, language, cover, year, tags, title))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'aggiornamento dei metadati: {e}")
            return False

    def get_metadata(self):
        """
        Recupera i metadati per il manga.
        Restituisce un dizionario con i metadati o None se non trovati.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute('SELECT title, author, description, language, cover, year, tags FROM metadata')
                metadata = c.fetchone()
                if metadata:
                    return dict(metadata)
                return None
        except sqlite3.Error as e:
            logger.error(f"Errore durante il recupero dei metadati: {e}")
            return None

    def insert_volume(self, name, order, cover=None):
        """
        Inserisce un nuovo volume con validazione input.

        Args:
            name: Nome volume
            order: Ordine volume
            cover: Cover image blob (optional)

        Returns:
            ID del volume in caso di successo, None in caso di errore

        Raises:
            ValidationError: Se input non validi
        """
        try:
            # Valida input
            name = validate_volume_name(name)
            order = validate_order(order)

            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO volumes (name, "order", cover)
                    VALUES (?, ?, ?)
                ''', (name, order, cover))
                conn.commit()
                return c.lastrowid
        except ValidationError:
            # Re-raise validation errors
            raise
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'inserimento del volume: {e}")
            return None

    def update_volume(self, volume_id, name, order, cover=None):
        """
        Aggiorna un volume esistente.
        Restituisce True in caso di successo, False altrimenti.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    UPDATE volumes SET
                        name = ?,
                        "order" = ?,
                        cover = ?
                    WHERE id = ?
                ''', (name, order, cover, volume_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'aggiornamento del volume: {e}")
            return False

    def delete_volume(self, volume_id):
        """
        Elimina un volume e tutti i suoi capitoli e pagine.
        Restituisce True in caso di successo, False altrimenti.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                # Trova tutti i capitoli nel volume
                c.execute('SELECT id FROM chapters WHERE volume_id = ?', (volume_id,))
                chapter_ids = [row[0] for row in c.fetchall()]
                # Elimina le pagine di ogni capitolo
                for chapter_id in chapter_ids:
                    c.execute('DELETE FROM pages WHERE chapter_id = ?', (chapter_id,))
                # Elimina i capitoli
                c.execute('DELETE FROM chapters WHERE volume_id = ?', (volume_id,))
                # Elimina il volume
                c.execute('DELETE FROM volumes WHERE id = ?', (volume_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'eliminazione del volume {volume_id}: {e}")
            return False

    def get_volumes(self):
        """
        Recupera tutti i volumi, ordinati per 'order'.
        Restituisce una lista di oggetti Row o una lista vuota in caso di errore/nessun dato.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute('SELECT id, name, "order", cover FROM volumes ORDER BY "order"')
                return c.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Errore durante il recupero dei volumi: {e}")
            return []

    def insert_chapter(self, name, order, volume_id, description=None):
        """
        Inserisce un nuovo capitolo con validazione input.

        Args:
            name: Nome capitolo
            order: Ordine capitolo
            volume_id: ID volume parent
            description: Descrizione (optional)

        Returns:
            ID del capitolo in caso di successo, None in caso di errore

        Raises:
            ValidationError: Se input non validi
        """
        try:
            # Valida input
            name = validate_chapter_name(name)
            order = validate_order(order)
            description = validate_description(description)

            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO chapters (name, "order", description, volume_id)
                    VALUES (?, ?, ?, ?)
                ''', (name, order, description, volume_id))
                conn.commit()
                return c.lastrowid
        except ValidationError:
            # Re-raise validation errors
            raise
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'inserimento del capitolo: {e}")
            return None

    def get_chapters_for_volume(self, volume_id):
        """
        Recupera tutti i capitoli per un dato volume, ordinati per 'order'.
        Restituisce una lista di oggetti Row o una lista vuota in caso di errore/nessun dato.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute('SELECT id, name, "order", description FROM chapters WHERE volume_id = ? ORDER BY "order"', (volume_id,))
                return c.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Errore durante il recupero dei capitoli per il volume {volume_id}: {e}")
            return []

    def get_all_chapters(self):
        """
        Recupera tutti i capitoli per il manga, ordinati per 'order'.
        Restituisce una lista di oggetti Row o una lista vuota in caso di errore/nessun dato.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute('SELECT id, name, "order", description FROM chapters ORDER BY "order"')
                return c.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Errore durante il recupero dei capitoli: {e}")
            return []

    def get_pages_for_chapter(self, chapter_id):
        """
        Recupera tutte le pagine per un dato capitolo, ordinate per page_number.
        Restituisce una lista di oggetti Row o una lista vuota in caso di errore/nessun dato.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute('SELECT page_number, image_data FROM pages WHERE chapter_id = ? ORDER BY page_number', (chapter_id,))
                return c.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Errore durante il recupero delle pagine per il capitolo {chapter_id}: {e}")
            return []

    def insert_page(self, chapter_id, page_number, image_path):
        """
        Inserisce una nuova pagina in un capitolo.
        image_path è il percorso del file immagine.
        Converte automaticamente .webp e .jfif in formato compatibile.
        Restituisce True in caso di successo, False altrimenti.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()

                # Controlla se il file è webp o jfif e convertilo
                file_ext = os.path.splitext(image_path)[1].lower()
                if file_ext in ['.webp', '.jfif']:
                    # Converti usando Pillow
                    from io import BytesIO
                    img = Image.open(image_path)
                    # Converti in RGB se necessario (per PNG con trasparenza)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # Mantieni trasparenza se presente
                        buffer = BytesIO()
                        img.save(buffer, format='PNG')
                        image_data = buffer.getvalue()
                    else:
                        # Converti in JPEG per immagini senza trasparenza (più efficiente)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        buffer = BytesIO()
                        img.save(buffer, format='JPEG', quality=95)
                        image_data = buffer.getvalue()
                else:
                    # Formati standard, leggi direttamente
                    with open(image_path, 'rb') as f:
                        image_data = f.read()

                c.execute('INSERT INTO pages (chapter_id, page_number, image_data) VALUES (?, ?, ?)',
                          (chapter_id, page_number, image_data))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'inserimento della pagina: {e}")
            return False
        except Exception as e:
            logger.error(f"Errore durante la conversione dell'immagine: {e}")
            return False

    def delete_chapter_and_pages(self, chapter_id):
        """
        Elimina un capitolo e tutte le sue pagine.
        Restituisce True in caso di successo, False altrimenti.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                # Prima elimina le pagine associate al capitolo
                c.execute('DELETE FROM pages WHERE chapter_id = ?', (chapter_id,))
                # Poi elimina il capitolo stesso
                c.execute('DELETE FROM chapters WHERE id = ?', (chapter_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'eliminazione del capitolo {chapter_id}: {e}")
            return False

    def update_chapter_name(self, chapter_id, new_name):
        """
        Rinomina un capitolo.
        Restituisce True in caso di successo, False altrimenti.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('UPDATE chapters SET name = ? WHERE id = ?', (new_name, chapter_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'aggiornamento del nome del capitolo {chapter_id}: {e}")
            return False

    def update_chapters_order(self, chapter_ids):
        """
        Aggiorna l'ordine dei capitoli.
        chapter_ids è una lista di ID di capitoli nell'ordine desiderato.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                for index, chapter_id in enumerate(chapter_ids):
                    c.execute('UPDATE chapters SET "order" = ? WHERE id = ?', (index + 1, chapter_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'aggiornamento dell'ordine dei capitoli: {e}")
            return False

    def delete_page(self, chapter_id, page_number):
        """
        Elimina una pagina da un capitolo.
        Restituisce True in caso di successo, False altrimenti.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('DELETE FROM pages WHERE chapter_id = ? AND page_number = ?', (chapter_id, page_number))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'eliminazione della pagina {page_number} dal capitolo {chapter_id}: {e}")
            return False

    def update_page_order(self, chapter_id, ordered_pages_data):
        """
        Aggiorna l'ordine delle pagine per un capitolo.
        Questo metodo cancella tutte le pagine esistenti per il capitolo e le reinserisce
        con il nuovo ordine.
        ordered_pages_data è una lista di dati di immagine (BLOB).
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                # Cancella tutte le pagine esistenti per questo capitolo
                c.execute('DELETE FROM pages WHERE chapter_id = ?', (chapter_id,))
                # Inserisce le pagine nel nuovo ordine
                for index, image_data in enumerate(ordered_pages_data):
                    c.execute('INSERT INTO pages (chapter_id, page_number, image_data) VALUES (?, ?, ?)',
                              (chapter_id, index + 1, image_data))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'aggiornamento dell'ordine delle pagine per il capitolo {chapter_id}: {e}")
            return False

    def swap_page_order(self, chapter_id, page_number1, page_number2):
        """
        Scambia l'ordine di due pagine.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                # Ottieni i dati delle due pagine
                c.execute("SELECT image_data FROM pages WHERE chapter_id = ? AND page_number = ?", (chapter_id, page_number1))
                page1_data = c.fetchone()[0]
                c.execute("SELECT image_data FROM pages WHERE chapter_id = ? AND page_number = ?", (chapter_id, page_number2))
                page2_data = c.fetchone()[0]

                # Scambia i dati
                c.execute("UPDATE pages SET image_data = ? WHERE chapter_id = ? AND page_number = ?", (page2_data, chapter_id, page_number1))
                c.execute("UPDATE pages SET image_data = ? WHERE chapter_id = ? AND page_number = ?", (page1_data, chapter_id, page_number2))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante lo scambio di pagine per il capitolo {chapter_id}: {e}")
            return False

    def save_reading_position(self, chapter_id: int, page_number: int, user: str = "default") -> bool:
        """
        Salva la posizione di lettura corrente.

        Args:
            chapter_id: ID del capitolo
            page_number: Numero della pagina corrente
            user: Nome utente (default: "default")

        Returns:
            True se il salvataggio è riuscito, False altrimenti
        """
        try:
            import time
            timestamp = int(time.time())

            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()

                # Controlla se esiste già una entry per questo utente
                c.execute('SELECT rowid FROM history WHERE user = ? LIMIT 1', (user,))
                existing = c.fetchone()

                if existing:
                    # Aggiorna posizione esistente
                    c.execute('''
                        UPDATE history
                        SET chapter_id = ?, page_number = ?, timestamp = ?
                        WHERE user = ?
                    ''', (chapter_id, page_number, timestamp, user))
                    logger.debug(f"Aggiornata posizione di lettura: capitolo {chapter_id}, pagina {page_number}")
                else:
                    # Inserisci nuova posizione
                    c.execute('''
                        INSERT INTO history (user, chapter_id, page_number, timestamp)
                        VALUES (?, ?, ?, ?)
                    ''', (user, chapter_id, page_number, timestamp))
                    logger.debug(f"Salvata nuova posizione di lettura: capitolo {chapter_id}, pagina {page_number}")

                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante il salvataggio della posizione di lettura: {e}")
            return False

    def get_last_reading_position(self, user: str = "default"):
        """
        Recupera l'ultima posizione di lettura salvata.

        Args:
            user: Nome utente (default: "default")

        Returns:
            Dizionario con chapter_id, page_number, timestamp, e informazioni del capitolo
            None se non ci sono posizioni salvate
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()

                # Recupera ultima posizione con info capitolo
                c.execute('''
                    SELECT h.chapter_id, h.page_number, h.timestamp,
                           ch.name as chapter_name, ch.volume_id,
                           v.name as volume_name
                    FROM history h
                    LEFT JOIN chapters ch ON h.chapter_id = ch.id
                    LEFT JOIN volumes v ON ch.volume_id = v.id
                    WHERE h.user = ?
                    ORDER BY h.timestamp DESC
                    LIMIT 1
                ''', (user,))

                result = c.fetchone()

                if result:
                    logger.debug(f"Recuperata posizione: capitolo {result['chapter_id']}, pagina {result['page_number']}")
                    return dict(result)
                else:
                    logger.debug("Nessuna posizione di lettura salvata")
                    return None
        except sqlite3.Error as e:
            logger.error(f"Errore durante il recupero della posizione di lettura: {e}")
            return None

    def get_reading_progress(self, user: str = "default"):
        """
        Calcola il progresso di lettura (percentuale completamento).
        Ottimizzato per evitare subquery annidate.

        Args:
            user: Nome utente (default: "default")

        Returns:
            Dizionario con total_pages, read_pages, percentage
            None se non ci sono dati
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()

                # Conta totale pagine
                c.execute('SELECT COUNT(*) FROM pages')
                total_pages = c.fetchone()[0]

                if total_pages == 0:
                    return None

                # Recupera ultima posizione
                position = self.get_last_reading_position(user)

                if not position:
                    return {
                        'total_pages': total_pages,
                        'read_pages': 0,
                        'percentage': 0.0
                    }

                # OTTIMIZZATO: Pre-calcola l'order del capitolo corrente
                # invece di usare una subquery annidata
                c.execute('SELECT "order" FROM chapters WHERE id = ?', (position['chapter_id'],))
                current_chapter_order_row = c.fetchone()

                if not current_chapter_order_row:
                    return {
                        'total_pages': total_pages,
                        'read_pages': 0,
                        'percentage': 0.0
                    }

                current_chapter_order = current_chapter_order_row[0]

                # Conta pagine lette fino alla posizione corrente
                # Query ottimizzata senza subquery annidata
                c.execute('''
                    SELECT COUNT(*) FROM pages p
                    JOIN chapters ch ON p.chapter_id = ch.id
                    WHERE ch."order" < ?
                       OR (ch.id = ? AND p.page_number <= ?)
                ''', (current_chapter_order, position['chapter_id'], position['page_number']))

                read_pages = c.fetchone()[0]
                percentage = (read_pages / total_pages) * 100

                logger.debug(f"Progresso lettura: {read_pages}/{total_pages} ({percentage:.1f}%)")

                return {
                    'total_pages': total_pages,
                    'read_pages': read_pages,
                    'percentage': percentage
                }
        except sqlite3.Error as e:
            logger.error(f"Errore durante il calcolo del progresso: {e}")
            return None

    def clear_reading_history(self, user: str = "default") -> bool:
        """
        Cancella la cronologia di lettura per un utente.

        Args:
            user: Nome utente (default: "default")

        Returns:
            True se la cancellazione è riuscita, False altrimenti
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('DELETE FROM history WHERE user = ?', (user,))
                conn.commit()
                logger.info(f"Cronologia di lettura cancellata per utente: {user}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante la cancellazione della cronologia: {e}")
            return False

    # ===== BOOKMARKS METHODS =====

    def add_bookmark(self, chapter_id: int, page_number: int, name: str, user: str = "default") -> int:
        """
        Aggiunge un bookmark alla posizione specificata.

        Args:
            chapter_id: ID del capitolo
            page_number: Numero della pagina
            name: Nome del bookmark
            user: Nome utente (default: "default")

        Returns:
            ID del bookmark creato, o -1 in caso di errore
        """
        try:
            import time
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                timestamp = int(time.time())
                c.execute('''
                    INSERT INTO bookmarks (user, chapter_id, page_number, name, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user, chapter_id, page_number, name, timestamp))
                conn.commit()
                bookmark_id = c.lastrowid
                logger.info(f"Bookmark creato: {name} (ID: {bookmark_id})")
                return bookmark_id
        except sqlite3.Error as e:
            logger.error(f"Errore durante la creazione del bookmark: {e}")
            return -1

    def get_bookmarks(self, user: str = "default"):
        """
        Ottiene tutti i bookmarks dell'utente con informazioni capitolo/volume.

        Args:
            user: Nome utente (default: "default")

        Returns:
            Lista di dizionari con info bookmark, o lista vuota
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute('''
                    SELECT
                        b.id,
                        b.chapter_id,
                        b.page_number,
                        b.name,
                        b.timestamp,
                        c.name as chapter_name,
                        v.name as volume_name
                    FROM bookmarks b
                    JOIN chapters c ON b.chapter_id = c.id
                    JOIN volumes v ON c.volume_id = v.id
                    WHERE b.user = ?
                    ORDER BY b.timestamp DESC
                ''', (user,))

                bookmarks = []
                for row in c.fetchall():
                    bookmarks.append({
                        'id': row['id'],
                        'chapter_id': row['chapter_id'],
                        'page_number': row['page_number'],
                        'name': row['name'],
                        'timestamp': row['timestamp'],
                        'chapter_name': row['chapter_name'],
                        'volume_name': row['volume_name']
                    })

                return bookmarks
        except sqlite3.Error as e:
            logger.error(f"Errore durante il recupero dei bookmarks: {e}")
            return []

    def delete_bookmark(self, bookmark_id: int) -> bool:
        """
        Elimina un bookmark.

        Args:
            bookmark_id: ID del bookmark da eliminare

        Returns:
            True se eliminazione riuscita, False altrimenti
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('DELETE FROM bookmarks WHERE id = ?', (bookmark_id,))
                conn.commit()
                logger.info(f"Bookmark eliminato (ID: {bookmark_id})")
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'eliminazione del bookmark: {e}")
            return False

    def update_bookmark_name(self, bookmark_id: int, new_name: str) -> bool:
        """
        Rinomina un bookmark.

        Args:
            bookmark_id: ID del bookmark
            new_name: Nuovo nome

        Returns:
            True se rinominazione riuscita, False altrimenti
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('UPDATE bookmarks SET name = ? WHERE id = ?', (new_name, bookmark_id))
                conn.commit()
                logger.info(f"Bookmark rinominato (ID: {bookmark_id}) -> {new_name}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Errore durante la rinominazione del bookmark: {e}")
            return False

if __name__ == '__main__':
    DB_FILE = 'test.manga'
    DUMMY_IMAGE_PATH = 'dummy_page.png'

    # Rimuovi il file di test esistente se presente per un test pulito
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    if os.path.exists(DUMMY_IMAGE_PATH):
        os.remove(DUMMY_IMAGE_PATH)

    # Crea un'immagine dummy per il test
    try:
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(DUMMY_IMAGE_PATH)
        print(f"Immagine dummy '{DUMMY_IMAGE_PATH}' creata per il test.")
    except Exception as e:
        print(f"Errore durante la creazione dell'immagine dummy: {e}")
        exit()

    # Crea un'istanza del gestore del database
    db_manager = MangaDatabaseManager(DB_FILE)

    # create_manga_db_schema è chiamato nell'__init__
    # Non è necessario chiamarlo esplicitamente qui, ma il controllo del risultato è utile
    if db_manager.create_manga_db_schema():
        print(f"Database '{DB_FILE}' creato con successo e schema inizializzato.")

        # Esempio di utilizzo delle nuove funzioni di inserimento
        print("\n--- Inserimento dati di esempio ---")

        # Inserisci metadati
        if db_manager.insert_metadata(
                        title="Manga di Prova",
                        author="Autore Esempio",
                        description="Questo è un manga di prova per dimostrare le funzionalità.",
                        language="Italiano",
                        year=2023,
                        tags="fantasy,azione"):
            print("Metadati inseriti.")
        else:
            print("Errore nell'inserimento dei metadati.")

        # Inserisci capitoli
        chapter1_id = db_manager.insert_chapter("Capitolo 1: L'inizio", 1)
        if chapter1_id:
            print(f"Capitolo 1 inserito. ID: {chapter1_id}")
        else:
            print("Errore nell'inserimento del Capitolo 1.")

        chapter2_id = db_manager.insert_chapter("Capitolo 2: La scoperta", 2)
        if chapter2_id:
            print(f"Capitolo 2 inserito. ID: {chapter2_id}")
        else:
            print("Errore nell'inserimento del Capitolo 2.")

        # Inserisci pagine (ora usando il percorso dell'immagine dummy)
        if chapter1_id and db_manager.insert_page(chapter1_id, 1, DUMMY_IMAGE_PATH):
            print("Pagina 1 per Capitolo 1 inserita (da file immagine).")
        else:
            print("Errore nell'inserimento della Pagina 1 per Capitolo 1.")

        if chapter1_id and db_manager.insert_page(chapter1_id, 2, DUMMY_IMAGE_PATH):
            print("Pagina 2 per Capitolo 1 inserita (da file immagine).")
        else:
            print("Errore nell'inserimento della Pagina 2 per Capitolo 1.")

        if chapter2_id and db_manager.insert_page(chapter2_id, 1, DUMMY_IMAGE_PATH):
            print("Pagina 1 per Capitolo 2 inserita (da file immagine).")
        else:
            print("Errore nell'inserimento della Pagina 1 per Capitolo 2.")

        print(f"\nFile '{DB_FILE}' popolato con dati di esempio.")

        # Esempio di utilizzo delle nuove funzioni di recupero
        print("\n--- Recupero dati di esempio ---")

        # Recupera e stampa metadati
        metadata = db_manager.get_metadata()
        if metadata:
            print("\nMetadati:")
            for key in metadata.keys():
                print(f"  {key}: {metadata[key]}")
        else:
            print("Nessun metadato trovato o errore nel recupero.")

        # Recupera e stampa capitoli
        chapters = db_manager.get_chapters()
        if chapters:
            print("\nCapitoli:")
            for chapter in chapters:
                print(f"  ID: {chapter['id']}, Nome: {chapter['name']}, Ordine: {chapter['order']}")
                # Recupera e stampa pagine per ogni capitolo
                pages = db_manager.get_pages_for_chapter(chapter['id'])
                if pages:
                    print(f"    Pagine per {chapter['name']}:\n")
                    for page in pages:
                        # Ora image_data conterrà i byte reali dell'immagine
                        print(f"      Pagina: {page['page_number']}, Dimensione dati immagine: {len(page['image_data'])} byte")
                else:
                    print(f"    Nessuna pagina trovata o errore nel recupero per {chapter['name']}.")
        else:
            print("Nessun capitolo trovato o errore nel recupero.")
        print("\nRecupero dati completato.")
    else:
        print(f"Errore critico: impossibile creare lo schema del database per '{DB_FILE}'.")

    # Pulisci l'immagine dummy
    if os.path.exists(DUMMY_IMAGE_PATH):
        os.remove(DUMMY_IMAGE_PATH)
        print(f"Immagine dummy '{DUMMY_IMAGE_PATH}' rimossa.")