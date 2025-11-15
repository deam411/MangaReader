import customtkinter as ctk
from PIL import Image
import requests
from bs4 import BeautifulSoup
import os
import re
import html
import urllib.parse
import io
import threading
import queue
import asyncio
from customtkinter import filedialog

# Imports from manga_downloader_lib
from manga_downloader_lib.manga_downloader import process_manga_download
from manga_downloader_lib.src.config import set_download_folder, get_download_folder
from manga_downloader_lib.src.file_utils import create_manga_directory
from manga_downloader_lib.src.general_utils import fetch_page
from manga_downloader_lib.src.crawler_utils import extract_volume_info
from manga_downloader_lib.src.pdf_generator import extract_number
from manga_reader_db_integration.database.manager import MangaDatabaseManager
from manga_reader_db_integration.database.manager import MangaDatabaseManager
from manga_reader_db_integration.exceptions import ValidationError, DatabaseError

# --- Existing Functions (slightly modified for GUI) ---

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_manga_covers(manga_url):
    try:
        response = requests.get(manga_url, headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')
    icon_elements = soup.select('i[data-volume-image]')
    if not icon_elements:
        return None, None

    cover_urls = []
    for icon in icon_elements:
        img_tag_string = html.unescape(icon['data-volume-image'])
        img_soup = BeautifulSoup(img_tag_string, 'html.parser')
        img_tag = img_soup.find('img')
        if img_tag and 'src' in img_tag.attrs:
            cover_urls.append(img_tag['src'])
    
    cover_urls.reverse() # Re-introduce reverse here to get correct order (Volume 1, 2, ...)
    
    manga_title_match = re.search(r'/manga/[^/]+/([^/]+)', manga_url)
    if manga_title_match:
        manga_title = manga_title_match.group(1)
    else:
        manga_title = soup.title.string.strip() if soup.title else "manga"
    manga_title = re.sub(r'[\\/*?:",<>|]',"", manga_title)
    return cover_urls, manga_title

def download_selected_images(image_urls, manga_title, save_path, is_manga_cover=False):
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # Ensure image_urls is always a list
    if not isinstance(image_urls, list):
        image_urls = [image_urls]

    success = True
    for i, url in enumerate(image_urls):
        try:
            if url.startswith('//'):
                url = 'https:' + url
            
            response = requests.get(url, headers=HEADERS, stream=True)
            response.raise_for_status()
            
            parsed_url = urllib.parse.urlparse(url)
            base_filename = os.path.basename(parsed_url.path)
            file_ext = os.path.splitext(base_filename)[1]
            if not file_ext: file_ext = '.jpg'

            if is_manga_cover:
                file_name = f"{manga_title}_cover{file_ext}"
            else: # This block handles non-manga-cover images
                if len(image_urls) == 1:
                    # Try to find a volume number in the URL
                    match = re.search(r'volume-(\\d+)', url)
                    if match:
                        idx = int(match.group(1))
                    else:
                        idx = 1 # Default for single download if no number found
                else:
                    idx = i + 1 # For multiple downloads, use the enumerated index

                file_name = f"{manga_title}_{idx}{file_ext}"
            file_path = os.path.join(save_path, file_name)

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Scaricata: {file_name}")
        except Exception as e:
            print(f"Errore durante il download di {url}: {e}")
            success = False
    return success

# --- GUI Application ---

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ladro di Copertine Mangaworld")
        self.attributes('-fullscreen', True)
        self.bind('<Escape>', self.on_escape_key)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- App State and Global Enter Binding ---
        self.app_state = "search"
        self.bind('<Return>', self.on_global_enter)

        # --- Top Frame for Input ---
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Inserisci l'URL del manga e premi Invio")
        self.url_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew", columnspan=2)
        # self.url_entry.bind('<Return>', self.start_search_thread) # Removed
        self.url_entry.bind('<FocusIn>', self.set_state_to_search)

        # --- .manga File Integration Frame ---
        self.manga_integration_frame = ctk.CTkFrame(self.top_frame)
        self.manga_integration_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.manga_integration_frame.grid_columnconfigure(1, weight=1)

        self.select_manga_file_button = ctk.CTkButton(self.manga_integration_frame, text="Seleziona File .manga", command=self._select_manga_file)
        self.select_manga_file_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.manga_file_path_label = ctk.CTkLabel(self.manga_integration_frame, text="Nessun file .manga selezionato")
        self.manga_file_path_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.selected_manga_file = None # To store the path of the selected .manga file

        self.new_volume_name_entry = ctk.CTkEntry(self.manga_integration_frame, placeholder_text="Nome Nuovo Volume (opzionale)")
        self.new_volume_name_entry.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.volume_number_entry = ctk.CTkEntry(self.manga_integration_frame, placeholder_text="Numero Volume da aggiungere (es. 1, 5-7)")
        self.volume_number_entry.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.volume_url_entry = ctk.CTkEntry(self.manga_integration_frame, placeholder_text="URL MangaWorld del Manga")
        self.volume_url_entry.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.add_volume_button = ctk.CTkButton(self.manga_integration_frame, text="Aggiungi Volume a .manga", command=self._add_volume_to_manga)
        self.add_volume_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # --- Scrollable Frame for Covers ---
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Copertine Trovate")
        self.scrollable_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.checkboxes = []
        self.image_refs = [] # Keep references to images
        self.save_path = None
        self.manga_title = ""

        # Thread-safe queue for GUI updates
        self.queue = queue.Queue()
        self.after(100, self._check_queue) # Start checking the queue periodically

        # Status Label (moved to top frame)
        self.status_label = ctk.CTkLabel(self.top_frame, text="")
        self.status_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

    def on_global_enter(self, event=None):
        manga_url = self.url_entry.get()
        if "mangaworld.ac/manga/" in manga_url or "mangaworld.cc/manga/" in manga_url: # Simple check for manga URL
            print("Global Enter -> Manga Download")
            self._start_manga_download_process(manga_url)
        elif self.app_state == "search":
            print("Global Enter -> Search Covers")
            self._start_search_process()
        elif self.app_state == "download":
            print("Global Enter -> Download Covers")
            self._start_download_process()

    def _start_search_process(self):
        manga_url = self.url_entry.get()
        if not manga_url:
            return
        self.clear_covers()
        self.status_label.configure(text=f"Cerco: {manga_url}...")
        thread = threading.Thread(target=self.search_covers, args=(manga_url,))
        thread.start()

    def _start_download_process(self):
        selected_covers_info = [(var, url, idx) for var, url, idx in self.checkboxes if var.get()]
        if not selected_covers_info:
            self.status_label.configure(text="Nessuna copertina selezionata.")
            return

        # Get the original manga URL from the entry field
        manga_url = self.url_entry.get()
        if not manga_url:
            self.status_label.configure(text="URL del manga non trovato per il download del volume.")
            return

        # Ask user for save path for the manga
        manga_save_base_path = ctk.filedialog.askdirectory(title="Seleziona cartella di salvataggio per il Manga")
        if not manga_save_base_path:
            return

        # Set the download folder for the manga_downloader_lib
        set_download_folder(manga_save_base_path)

        self.status_label.configure(text=f"Avvio download di {len(selected_covers_info)} volumi...")

        def _run_volume_downloads():
            for var, cover_url, volume_idx in selected_covers_info:
                self.queue.put(lambda: self.status_label.configure(text=f"Scaricando Volume {volume_idx} da {manga_url}..."))
                
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(process_manga_download(manga_url, start_index=volume_idx, end_index=volume_idx, volume_mode=True))
                finally:
                    loop.close()

                # After volume download, get the manga title and download the cover
                cover_urls, manga_title = get_manga_covers(manga_url)
                if manga_title:
                    final_manga_folder = os.path.join(manga_save_base_path, manga_title)
                    if cover_urls:
                        self.queue.put(lambda: self.status_label.configure(text=f"Scaricando copertina per Volume {volume_idx} di '{manga_title}'..."))
                        # Find the specific cover for this volume
                        specific_cover_url = None
                        for c_var, c_url, c_idx in self.checkboxes:
                            if c_idx == volume_idx:
                                specific_cover_url = c_url
                                break
                        if specific_cover_url:
                            download_selected_images([specific_cover_url], f"{manga_title}_Volume_{volume_idx}", final_manga_folder, is_manga_cover=True)
                            self.queue.put(lambda: self.status_label.configure(text=f"Download Volume {volume_idx} e copertina completato in '{final_manga_folder}'."))
                        else:
                            self.queue.put(lambda: self.status_label.configure(text=f"Download Volume {volume_idx} completato, ma nessuna copertina specifica trovata."))
                    else:
                        self.queue.put(lambda: self.status_label.configure(text=f"Download Volume {volume_idx} completato, ma nessuna copertina trovata per '{manga_title}'."))
                else:
                    self.queue.put(lambda: self.status_label.configure(text=f"Download Volume {volume_idx} completato, ma titolo manga non trovato per '{manga_url}'."))
            self.queue.put(lambda: self.status_label.configure(text="Tutti i download dei volumi completati."))

        thread = threading.Thread(target=_run_volume_downloads)
        thread.start()

    def search_covers(self, manga_url):
        cover_urls, manga_title = get_manga_covers(manga_url)
        self.manga_title = manga_title

        if not cover_urls:
            self.status_label.configure(text="Nessuna copertina trovata.")
            return
        
        self.status_label.configure(text=f"Trovate {len(cover_urls)} copertine per '{manga_title}'")
        
        collected_data = []
        for i, url in enumerate(cover_urls):
            try:
                if url.startswith('//'): url = 'https:' + url
                response = requests.get(url, headers=HEADERS)
                response.raise_for_status()
                
                img = Image.open(io.BytesIO(response.content))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(150, 225))
                collected_data.append((i, url, ctk_img))
                print(f"Collected image for {url}")

            except Exception as e:
                print(f"Errore caricamento anteprima {url}: {e}")
        
        self.queue.put(collected_data) # Put data into the queue
        # self.after(0, self._display_covers_in_gui, collected_data) # Removed

    def _display_covers_in_gui(self, collected_data):
        print(f"Displaying {len(collected_data)} covers in GUI.")
        for i, url, ctk_img in collected_data:
            self.image_refs.append(ctk_img) # Keep reference

            row_frame = ctk.CTkFrame(self.scrollable_frame)
            row_frame.grid(row=i, column=0, sticky="ew", padx=5, pady=5)
            row_frame.grid_columnconfigure(2, weight=1)

            label = ctk.CTkLabel(row_frame, image=ctk_img, text="")
            
            var = ctk.BooleanVar()
            checkbox = ctk.CTkCheckBox(row_frame, text=f"Volume {i+1}", variable=var, onvalue=True, offvalue=False)
            
            label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            checkbox.grid(row=0, column=1, padx=10, pady=10, sticky="w")
            
            self.checkboxes.append((var, url, i + 1))

            spacer = ctk.CTkLabel(row_frame, text="")
            spacer.grid(row=0, column=2, sticky="ew")

            row_frame.bind("<Button-1>", lambda e, v=var: self.toggle_checkbox(v))
            label.bind("<Button-1>", lambda e, v=var: self.toggle_checkbox(v))
            spacer.bind("<Button-1>", lambda e, v=var: self.toggle_checkbox(v))
        
        self.app_state = "download"
        self.scrollable_frame.focus_set()
        print("State -> Download")

    def clear_covers(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.checkboxes = []
        self.image_refs = []

    def on_escape_key(self, event=None):
        self.destroy()

    def set_state_to_search(self, event=None):
        self.app_state = "search"
        print("State -> Search")

    def _start_manga_download_process(self, manga_url=None):
        if manga_url is None:
            manga_url = self.url_entry.get()
        if not manga_url:
            self.status_label.configure(text="Inserisci un URL del manga per scaricare.")
            return

        # Ask user for save path for the manga
        manga_save_base_path = ctk.filedialog.askdirectory(title="Seleziona cartella di salvataggio per il Manga")
        if not manga_save_base_path:
            return

        # Set the download folder for the manga_downloader_lib
        set_download_folder(manga_save_base_path)

        self.status_label.configure(text=f"Avvio download manga da: {manga_url}...")
        # Run process_manga_download in a separate thread
        def _run_manga_and_cover_download():
            # First, download the manga chapters/volumes
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(process_manga_download(manga_url, volume_mode=True))
            finally:
                loop.close()

            # After manga download, get the manga title and download the cover
            cover_urls, manga_title = get_manga_covers(manga_url)
            if manga_title:
                # The manga_downloader_lib creates a subfolder with manga_title
                final_manga_folder = os.path.join(manga_save_base_path, manga_title)
                
                if cover_urls:
                    # Download the first cover (usually the main one) into the manga's folder
                    self.queue.put(lambda: self.status_label.configure(text=f"Scaricando la copertina per '{manga_title}'..."))
                    download_selected_images([cover_urls[0]], manga_title, final_manga_folder, is_manga_cover=True)
                    self.queue.put(lambda: self.status_label.configure(text=f"Download manga e copertina completato in '{final_manga_folder}'."))
                else:
                    self.queue.put(lambda: self.status_label.configure(text=f"Download manga completato, ma nessuna copertina trovata per '{manga_title}'."))
            else:
                self.queue.put(lambda: self.status_label.configure(text=f"Download manga completato, ma titolo manga non trovato per '{manga_url}'."))

        thread = threading.Thread(target=_run_manga_and_cover_download)
        thread.start()
    def _select_manga_file(self):
        file_path = filedialog.askopenfilename(
            title="Seleziona un file .manga",
            filetypes=[("Manga Files", "*.manga")]
        )
        if file_path:
            self.selected_manga_file = file_path
            self.manga_file_path_label.configure(text=os.path.basename(file_path))
            self.status_label.configure(text=f"File .manga selezionato: {os.path.basename(file_path)}")
        else:
            self.status_label.configure(text="Nessun file .manga selezionato.")

    def _add_volume_to_manga(self):
        print("DEBUG: _add_volume_to_manga chiamato.")
        if not self.selected_manga_file:
            self.status_label.configure(text="Per favore, seleziona prima un file .manga.")
            print("DEBUG: Errore: Nessun file .manga selezionato.")
            return

        volume_name = self.new_volume_name_entry.get()
        volume_number_str = self.volume_number_entry.get()
        manga_world_url = self.volume_url_entry.get()

        if not manga_world_url:
            self.status_label.configure(text="Per favore, inserisci l'URL MangaWorld del manga.")
            print("DEBUG: Errore: URL MangaWorld del manga non inserito.")
            return
        
        # Parse volume number input
        start_volume = None
        end_volume = None
        if volume_number_str:
            if "-" in volume_number_str:
                try:
                    start_volume, end_volume = map(int, volume_number_str.split('-'))
                except ValueError:
                    self.status_label.configure(text="Errore: Formato numero volume non valido (es. 1 o 5-7).")
                    print("DEBUG: Errore: Formato numero volume non valido.")
                    return
            else:
                try:
                    start_volume = int(volume_number_str)
                    end_volume = int(volume_number_str)
                except ValueError:
                    self.status_label.configure(text="Errore: Formato numero volume non valido (es. 1 o 5-7).")
                    print("DEBUG: Errore: Formato numero volume non valido.")
                    return

        self.status_label.configure(text=f"Aggiungendo volume(i) '{volume_name if volume_name else 'specificato'}' da {manga_world_url} al file {os.path.basename(self.selected_manga_file)}...")
        print(f"DEBUG: Inizializzazione thread per _run_add_volume_process con file: {self.selected_manga_file}, nome volume: {volume_name}, URL: {manga_world_url}, start_volume: {start_volume}, end_volume: {end_volume}")
        thread = threading.Thread(target=self._run_add_volume_process, args=(self.selected_manga_file, volume_name, manga_world_url, start_volume, end_volume))
        thread.start()
        print("DEBUG: Thread avviato.")

    def _run_add_volume_process(self, manga_file_path, volume_name, manga_world_url, start_volume=None, end_volume=None):
        self.queue.put(lambda: self.status_label.configure(text=f"Inizio processo di aggiunta volume a {os.path.basename(manga_file_path)}..."))
        
        try:
            # 1. Download the volume chapters/pages to a temporary directory.
            temp_download_dir = os.path.join(os.getcwd(), "temp_manga_download")
            os.makedirs(temp_download_dir, exist_ok=True)
            set_download_folder(temp_download_dir) # Set the downloader to use this temp dir

            self.queue.put(lambda: self.status_label.configure(text=f"Scaricando volume da {manga_world_url} in {temp_download_dir}..."))
            
            # Create a new event loop for this thread
            asyncio.set_event_loop(asyncio.new_event_loop())
            try:
                asyncio.get_event_loop().run_until_complete(process_manga_download(manga_world_url, start_index=start_volume, end_index=end_volume, volume_mode=True))
            except Exception as e:
                self.queue.put(lambda e=e: self.status_label.configure(text=f"Errore durante il download del manga: {e}"))
                print(f"DEBUG: Errore durante il download del manga (asyncio): {e}")
                return # Exit if download fails
            finally:
                asyncio.get_event_loop().close()
            
            print(f"DEBUG: Download completato. Verifico il titolo del manga dall'URL: {manga_world_url}")
            # Get manga title from the URL for folder structure
            _, manga_title_from_url = get_manga_covers(manga_world_url)
            print(f"DEBUG: Titolo manga ottenuto: {manga_title_from_url}")
            if not manga_title_from_url:
                self.queue.put(lambda: self.status_label.configure(text="Errore: Impossibile ottenere il titolo del manga dall'URL."))
                print("DEBUG: Errore: Titolo manga non ottenuto dall'URL.")
                return

            downloaded_manga_path = os.path.join(temp_download_dir, manga_title_from_url)
            print(f"DEBUG: Percorso manga scaricato (iniziale): {downloaded_manga_path}")
            if not os.path.exists(downloaded_manga_path):
                self.queue.put(lambda: self.status_label.configure(text="Errore: Il download del manga non ha creato la cartella prevista."))
                print(f"DEBUG: Errore: Cartella manga scaricata non trovata: {downloaded_manga_path}")
                return
            print(f"DEBUG: Contenuto di {downloaded_manga_path}: {os.listdir(downloaded_manga_path)}")

            # Find the actual volume folder within the downloaded manga path
            volume_folders = [d for d in os.listdir(downloaded_manga_path) if os.path.isdir(os.path.join(downloaded_manga_path, d)) and d.startswith("Volume")]
            
            if not volume_folders:
                self.queue.put(lambda: self.status_label.configure(text="Errore: Nessuna cartella 'Volume' trovata nella directory del manga scaricato."))
                print("DEBUG: Errore: Nessuna cartella 'Volume' trovata.")
                return
            
            # Assuming only one volume is downloaded at a time, take the first one
            actual_volume_path = os.path.join(downloaded_manga_path, volume_folders[0])
            print(f"DEBUG: Percorso effettivo del volume: {actual_volume_path}")

            # 2. Read the downloaded images and cover.
            # Get cover image (now looking inside the actual_volume_path)
            cover_image_path = None
            cover_data = None

            # First, try to download the specific volume cover
            all_manga_cover_urls, _ = get_manga_covers(manga_world_url)
            if all_manga_cover_urls and start_volume is not None and 0 < start_volume <= len(all_manga_cover_urls):
                specific_cover_url = all_manga_cover_urls[start_volume - 1] # Adjust for 0-based indexing
                
                # Determine the file extension from the URL
                parsed_url = urllib.parse.urlparse(specific_cover_url)
                base_filename = os.path.basename(parsed_url.path)
                file_ext = os.path.splitext(base_filename)[1]
                if not file_ext: file_ext = '.jpg' # Default if no extension found

                # Reconstruct the filename as download_selected_images would create it
                downloaded_cover_filename = f"{manga_title_from_url}_cover{file_ext}"
                cover_image_path = os.path.join(actual_volume_path, downloaded_cover_filename)

                try:
                    # Use the existing download_selected_images function
                    download_selected_images([specific_cover_url], manga_title_from_url, actual_volume_path, is_manga_cover=True)
                    print(f"DEBUG: Copertina specifica del volume scaricata in: {cover_image_path}")
                except Exception as e:
                    print(f"DEBUG: Errore durante il download della copertina specifica del volume: {e}")
            
            if cover_image_path and os.path.exists(cover_image_path):
                with open(cover_image_path, 'rb') as f:
                    cover_data = f.read()
                print(f"DEBUG: Dati copertina letti (dimensione: {len(cover_data)} bytes)")
            else:
                print("DEBUG: Nessuna copertina trovata o letta.")
            
            # Get chapters and pages (now looking inside the actual_volume_path)
            chapters_in_temp_dir = sorted([d for d in os.listdir(actual_volume_path) if os.path.isdir(os.path.join(actual_volume_path, d))], key=extract_number)
            print(f"DEBUG: Capitoli trovati nella directory temporanea (nel volume): {chapters_in_temp_dir}")

            if not chapters_in_temp_dir:
                self.queue.put(lambda: self.status_label.configure(text="Nessun capitolo trovato nella directory temporanea del volume."))
                print("DEBUG: Errore: Nessun capitolo trovato nella directory temporanea del volume.")
                return

            # 3. Using MangaDatabaseManager to insert into the .manga file.
            print(f"DEBUG: Inizializzazione MangaDatabaseManager per {manga_file_path}...")
            db_manager = MangaDatabaseManager(manga_file_path)
            print(f"DEBUG: MangaDatabaseManager inizializzato con successo per {manga_file_path}")
            
            # Get current volumes to determine the order for the new volume
            existing_volumes = db_manager.chapters.get_volumes()
            print(f"DEBUG: Volumi esistenti: {existing_volumes}")
            new_volume_order = len(existing_volumes) + 1
            print(f"DEBUG: Nuovo ordine volume: {new_volume_order}")

            # Insert the new volume
            actual_volume_name = volume_name if volume_name else f"Volume {new_volume_order}"
            print(f"DEBUG: Inserimento volume: '{actual_volume_name}'")
            try:
                volume_id = db_manager.chapters.insert_volume(name=actual_volume_name, order=new_volume_order, cover=cover_data)
                print(f"DEBUG: Volume inserito con ID: {volume_id}")
            except ValidationError as e:
                self.queue.put(lambda: self.status_label.configure(text=f"Errore di validazione per il volume: {e}"))
                print(f"DEBUG: Errore di validazione volume: {e}")
                return
            except DatabaseError as e:
                self.queue.put(lambda: self.status_label.configure(text=f"Errore database durante l\'inserimento del volume: {e}"))
                print(f"DEBUG: Errore database inserimento volume: {e}")
                return

            if not volume_id:
                self.queue.put(lambda: self.status_label.configure(text="Errore: Impossibile inserire il nuovo volume nel database (volume_id è None)."))
                print("DEBUG: Errore: volume_id è None dopo l\'inserimento.")
                return

            self.queue.put(lambda: self.status_label.configure(text=f"Volume '{actual_volume_name}' inserito (ID: {volume_id}). Inserimento capitoli..."))

            for chapter_order, chapter_dir_name in enumerate(chapters_in_temp_dir):
                chapter_path = os.path.join(actual_volume_path, chapter_dir_name) # Corrected path for chapter
                chapter_name = chapter_dir_name # e.g., "Chapter 1"
                print(f"DEBUG: Inserimento capitolo: '{chapter_name}' (ordine: {chapter_order + 1}) per volume ID: {volume_id}")
                
                try:
                    chapter_id = db_manager.chapters.insert_chapter(name=chapter_name, order=chapter_order + 1, volume_id=volume_id)
                    print(f"DEBUG: Capitolo inserito con ID: {chapter_id}")
                except ValidationError as e:
                    self.queue.put(lambda e=e: self.status_label.configure(text=f"Errore di validazione per il capitolo '{chapter_name}': {e}"))
                    print(f"DEBUG: Errore di validazione capitolo: {e}")
                    continue
                except DatabaseError as e:
                    self.queue.put(lambda e=e: self.status_label.configure(text=f"Errore database durante l\'inserimento del capitolo '{chapter_name}': {e}"))
                    print(f"DEBUG: Errore database inserimento capitolo: {e}")
                    continue

                if not chapter_id:
                    self.queue.put(lambda: self.status_label.configure(text=f"Errore: Impossibile inserire il capitolo '{chapter_name}' (chapter_id è None)."))
                    print("DEBUG: Errore: chapter_id è None dopo l\'inserimento.")
                    continue

                self.queue.put(lambda: self.status_label.configure(text=f"Capitolo '{chapter_name}' inserito (ID: {chapter_id}). Inserimento pagine..."))

                pages_in_chapter = sorted([f for f in os.listdir(chapter_path) if os.path.isfile(os.path.join(chapter_path, f))], key=extract_number)
                print(f"DEBUG: Pagine trovate nel capitolo '{chapter_name}': {pages_in_chapter}")
                for page_number, page_filename in enumerate(pages_in_chapter):
                    page_file_path = os.path.join(chapter_path, page_filename)
                    with open(page_file_path, 'rb') as f:
                        page_data = f.read()
                    print(f"DEBUG: Inserimento pagina {page_number + 1} per capitolo ID: {chapter_id} (dimensione dati: {len(page_data)} bytes)")
                    
                    try:
                        db_manager.chapters.insert_page(chapter_id=chapter_id, page_number=page_number + 1, image_data_or_path=page_data)
                    except DatabaseError as e:
                        self.queue.put(lambda e=e: self.status_label.configure(text=f"Errore database durante l\'inserimento della pagina {page_number + 1} del capitolo '{chapter_name}': {e}"))
                        print(f"DEBUG: Errore database inserimento pagina: {e}")
                        continue
                self.queue.put(lambda: self.status_label.configure(text=f"Pagine inserite per il capitolo '{chapter_name}'."))

            self.queue.put(lambda: self.status_label.configure(text=f"Processo di aggiunta volume completato con successo per '{actual_volume_name}'."))

        except Exception as e:
            self.queue.put(lambda e=e: self.status_label.configure(text=f"Errore durante l\'aggiunta del volume: {e}"))
            print(f"DEBUG: Errore generale durante l\'aggiunta del volume: {e}")
        finally:
            # Clean up the temporary directory
            if os.path.exists(temp_download_dir):
                import shutil
                shutil.rmtree(temp_download_dir)
                self.queue.put(lambda: self.status_label.configure(text="Directory temporanea pulita."))
                print(f"DEBUG: Directory temporanea pulita: {temp_download_dir}")

    def _download_selected_covers_thread(self, selected_urls, manga_title, save_path):
        download_selected_images(selected_urls, manga_title, save_path)
        self.status_label.configure(text=f"Download completato! Controlla la cartella '{save_path}'.")

    def toggle_checkbox(self, var):
        var.set(not var.get())

    def _check_queue(self):
        try:
            while True:
                item = self.queue.get(block=False)
                if callable(item): # If it's a function (like a status update)
                    item()
                else: # Assume it's collected_data for display
                    self._display_covers_in_gui(item)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._check_queue) # Reschedule itself


if __name__ == "__main__":
    app = App()
    app.mainloop()