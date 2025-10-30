import sqlite3
import os
from PIL import Image # Importa la libreria Pillow

class MangaDatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        print(f"MangaDatabaseManager: __init__ called for db_path: {db_path}") # DEBUG
        print(f"DEBUG: Loading database.py from: {__file__}") # DEBUG PRINT
        # create_manga_db_schema is called here to ensure the database is ready
        self.create_manga_db_schema()
        self.migrate_schema_to_v2() # Chiama la funzione di migrazione dello schema

    def create_manga_db_schema(self):
        """
        Crea lo schema del database per un file .manga.
        Restituisce True in caso di successo, False altrimenti.
        """
        print(f"MangaDatabaseManager: create_manga_db_schema called for db_path: {self.db_path}") # DEBUG
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

                conn.commit()
                print(f"MangaDatabaseManager: create_manga_db_schema successful for db_path: {self.db_path}") # DEBUG
                return True
        except sqlite3.Error as e:
            print(f"MangaDatabaseManager: Errore durante la creazione dello schema del database per {self.db_path}: {e}") # DEBUG
            return False

    def migrate_schema_to_v2(self):
        """
        Migra lo schema del database alla versione 2: aggiunge la colonna volume_id alla tabella chapters.
        """
        print(f"MangaDatabaseManager: migrate_schema_to_v2 called for db_path: {self.db_path}") # DEBUG
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()

                # Controlla se la colonna volume_id esiste già nella tabella chapters
                c.execute("PRAGMA table_info(chapters)")
                columns = [col[1] for col in c.fetchall()]
                if 'volume_id' not in columns:
                    print(f"MangaDatabaseManager: Aggiunta colonna 'volume_id' alla tabella 'chapters' in {self.db_path}") # DEBUG
                    c.execute("ALTER TABLE chapters ADD COLUMN volume_id INTEGER")

                    # Crea un volume di default se non esiste
                    c.execute("SELECT id FROM volumes WHERE name = 'Default Volume' LIMIT 1")
                    default_volume_id = c.fetchone()
                    if not default_volume_id:
                        c.execute("INSERT INTO volumes (name, 'order') VALUES ('Default Volume', 1)")
                        default_volume_id = c.lastrowid
                        print(f"MangaDatabaseManager: Creato 'Default Volume' con ID: {default_volume_id}") # DEBUG
                    else:
                        default_volume_id = default_volume_id[0]
                        print(f"MangaDatabaseManager: 'Default Volume' esistente con ID: {default_volume_id}") # DEBUG

                    # Assegna tutti i capitoli esistenti al volume di default
                    c.execute("UPDATE chapters SET volume_id = ? WHERE volume_id IS NULL", (default_volume_id,))
                    print(f"MangaDatabaseManager: Capitoli esistenti assegnati a 'Default Volume'.") # DEBUG
                else:
                    print(f"MangaDatabaseManager: Colonna 'volume_id' già presente nella tabella 'chapters'. Nessuna migrazione necessaria.") # DEBUG

                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"MangaDatabaseManager: Errore durante la migrazione dello schema del database per {self.db_path}: {e}") # DEBUG
            return False

    def insert_metadata(self, title, author=None, description=None, language=None, cover=None, year=None, tags=None):
        """
        Inserisce i metadati per il manga.
        Restituisce True in caso di successo, False altrimenti.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO metadata (title, author, description, language, cover, year, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (title, author, description, language, cover, year, tags))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Errore durante l'inserimento dei metadati: {e}")
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
            print(f"Errore durante l'aggiornamento dei metadati: {e}")
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
            print(f"Errore durante il recupero dei metadati: {e}")
            return None

    def insert_volume(self, name, order, cover=None):
        """
        Inserisce un nuovo volume.
        Restituisce l'ID del volume in caso di successo, o None in caso di errore.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO volumes (name, "order", cover)
                    VALUES (?, ?, ?)
                ''', (name, order, cover))
                conn.commit()
                return c.lastrowid
        except sqlite3.Error as e:
            print(f"Errore durante l'inserimento del volume: {e}")
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
            print(f"Errore durante l'aggiornamento del volume: {e}")
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
            print(f"Errore durante l'eliminazione del volume {volume_id}: {e}")
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
            print(f"Errore durante il recupero dei volumi: {e}")
            return []

    def insert_chapter(self, name, order, volume_id, description=None):
        """
        Inserisce un nuovo capitolo e restituisce l'ID del capitolo in caso di successo,
        o None in caso di errore.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO chapters (name, "order", description, volume_id)
                    VALUES (?, ?, ?, ?)
                ''', (name, order, description, volume_id))
                conn.commit()
                return c.lastrowid
        except sqlite3.Error as e:
            print(f"Errore durante l'inserimento del capitolo: {e}")
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
            print(f"Errore durante il recupero dei capitoli per il volume {volume_id}: {e}")
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
            print(f"Errore durante il recupero dei capitoli: {e}")
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
            print(f"Errore durante il recupero delle pagine per il capitolo {chapter_id}: {e}")
            return []

    def insert_page(self, chapter_id, page_number, image_path):
        """
        Inserisce una nuova pagina in un capitolo.
        image_path è il percorso del file immagine.
        Restituisce True in caso di successo, False altrimenti.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                c.execute('INSERT INTO pages (chapter_id, page_number, image_data) VALUES (?, ?, ?)',
                          (chapter_id, page_number, image_data))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Errore durante l'inserimento della pagina: {e}")
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
            print(f"Errore durante l'eliminazione del capitolo {chapter_id}: {e}")
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
            print(f"Errore durante l'aggiornamento del nome del capitolo {chapter_id}: {e}")
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
            print(f"Errore durante l'aggiornamento dell'ordine dei capitoli: {e}")
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
            print(f"Errore durante l'eliminazione della pagina {page_number} dal capitolo {chapter_id}: {e}")
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
            print(f"Errore durante l'aggiornamento dell'ordine delle pagine per il capitolo {chapter_id}: {e}")
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
            print(f"Errore durante lo scambio di pagine per il capitolo {chapter_id}: {e}")
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