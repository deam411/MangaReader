"""
Mangaworld Downloader Plugin - Download manga directly from Mangaworld into Manga Reader.

This plugin integrates with the Manga Creator through Shift+Add Volume to:
- Download manga from Mangaworld and convert them to .manga format
- Integrate downloaded volumes directly into existing .manga files
- Support volume range downloading and cover fetching
- Show real-time progress during download and database insertion
"""

import sys
import os
from typing import Dict, Any

# Add the plugin directory to the Python path to import modules
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

from plugins.plugin_base import PluginBase, PluginMetadata


class MangaworldDownloaderPlugin(PluginBase):
    """Plugin for downloading manga from Mangaworld and integrating into .manga files."""

    @property
    def metadata(self) -> PluginMetadata:
        """Metadata del plugin."""
        return PluginMetadata(
            name="Mangaworld Downloader",
            version="1.0.1",
            author="deam411",
            description="Download manga from Mangaworld.ac via Shift+Add Volume in Manga Creator",
            requires_version="0.3.0",
            url="https://github.com/deam411/Mangareader-Plugin"
        )

    def on_startup(self, context: Dict[str, Any]) -> None:
        """Chiamato all'avvio dell'applicazione."""
        logger = context.get('logger')
        if logger:
            logger.info(f"{self.metadata.name} v{self.metadata.version} loaded successfully!")
        print(f"[MangaworldDownloader] Plugin caricato! Usa Shift+Aggiungi Volume per scaricare da Mangaworld.")

    def get_config_schema(self) -> Dict[str, Any]:
        """Schema configurazione del plugin."""
        return {
            'auto_import': {
                'type': 'bool',
                'default': True,
                'description': 'Automatically import downloaded manga into library'
            },
            'download_path': {
                'type': 'str',
                'default': '',
                'description': 'Custom download path (leave empty to use library path)'
            },
            'quality': {
                'type': 'list',
                'default': 'High',
                'options': ['High', 'Medium', 'Low'],
                'description': 'Download quality for manga images'
            },
            'show_notifications': {
                'type': 'bool',
                'default': True,
                'description': 'Show notifications when downloads complete'
            },
            'convert_to_manga_format': {
                'type': 'bool',
                'default': True,
                'description': 'Automatically convert downloaded manga to .manga format'
            }
        }

    @staticmethod
    def add_volume_to_manga_file(manga_file_path: str, mangaworld_url: str, volume_number: str, volume_name: str = "", progress_callback: dict = None) -> bool:
        """
        Funzione helper per aggiungere un volume a un file .manga esistente.

        Args:
            manga_file_path: Percorso al file .manga
            mangaworld_url: URL del manga su Mangaworld
            volume_number: Numero del volume da scaricare (es: "5" o "5-7")
            volume_name: Nome del volume (opzionale)
            progress_callback: Dict per tracking progresso (opzionale)

        Returns:
            True se successo, False altrimenti
        """
        try:
            import asyncio
            import tempfile
            import shutil
            from main import App
            import logging

            # Setup logger con file su disco PRIMA di tutto
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.DEBUG)

            # File handler - salva su disco
            if not logger.handlers:
                log_file = os.path.join(tempfile.gettempdir(), "mangaworld_downloader_debug.log")
                file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)

                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.DEBUG)

                formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)

                logger.addHandler(file_handler)
                logger.addHandler(console_handler)

                logger.info(f"Log salvato in: {log_file}")

            logger.info("="*60)
            logger.info("INIZIO PROCESSO DI DOWNLOAD E INTEGRAZIONE")
            logger.info(f"File .manga RAW (prima strip): '{manga_file_path}'")
            logger.info(f"Tipo: {type(manga_file_path)}")
            logger.info(f"Lunghezza: {len(manga_file_path)}")

            # Rimuovi virgolette dal percorso se presenti
            manga_file_path_original = manga_file_path
            manga_file_path = manga_file_path.strip('"').strip("'")

            if manga_file_path != manga_file_path_original:
                logger.warning(f"Virgolette rimosse dal percorso!")
                logger.warning(f"Prima: '{manga_file_path_original}'")
                logger.warning(f"Dopo: '{manga_file_path}'")
            
            # Clean URL
            mangaworld_url = mangaworld_url.strip().strip('"').strip("'")
            if not mangaworld_url.startswith("http"):
                mangaworld_url = "https://" + mangaworld_url
                logger.info(f"Aggiunto protocollo https: {mangaworld_url}")

            logger.info(f"File .manga FINAL: '{manga_file_path}'")
            logger.info(f"URL Mangaworld: {mangaworld_url}")
            logger.info(f"Volume number: {volume_number}")
            logger.info(f"Volume name: {volume_name}")
            logger.info("="*60)

            # Parse volume number
            start_volume = None
            end_volume = None
            if volume_number:
                if "-" in volume_number:
                    start_volume, end_volume = map(int, volume_number.split('-'))
                else:
                    start_volume = int(volume_number)
                    end_volume = int(volume_number)

            # Download to temp directory
            temp_dir = tempfile.mkdtemp(prefix="mangaworld_download_")
            logger.info(f"Temp directory creata: {temp_dir}")

            try:
                # Update progress
                if progress_callback:
                    progress_callback['current_step'] = 'Connessione a Mangaworld...'

                import time

                # Use the downloader library to download
                from manga_downloader_lib.src.config import set_download_folder
                from manga_downloader_lib.manga_downloader import process_manga_download

                set_download_folder(temp_dir)
                logger.info(f"Download folder impostata: {temp_dir}")
                logger.info(f"URL: {mangaworld_url}")
                logger.info(f"Volume range: {start_volume}-{end_volume}")

                if progress_callback:
                    progress_callback['current_step'] = 'Download capitoli in corso...'

                # Download the volume
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    logger.info("Avvio download asyncrono...")
                    # Simula aggiornamenti durante il download
                    # Avvia il download in background
                    download_task = loop.create_task(
                        process_manga_download(
                            mangaworld_url,
                            start_index=start_volume,
                            end_index=end_volume,
                            volume_mode=True
                        )
                    )

                    # Aggiorna il progresso mentre aspettiamo
                    simulated_progress = 0
                    while not download_task.done():
                        loop.run_until_complete(asyncio.sleep(0.5))
                        if progress_callback and simulated_progress < 50:
                            simulated_progress += 2
                            # Usa total_chapters temporaneo per mostrare progresso
                            progress_callback['total_chapters'] = 100
                            progress_callback['current_chapter'] = simulated_progress
                            progress_callback['current_step'] = f'Download da Mangaworld... {simulated_progress}%'

                    # Assicurati che il task sia completato
                    loop.run_until_complete(download_task)
                    print(f"[MangaworldDownloader] DEBUG: Download completato!")

                finally:
                    loop.close()

                # Update progress
                if progress_callback:
                    progress_callback['current_step'] = 'Download completato! Preparazione integrazione...'
                    progress_callback['total_chapters'] = 100
                    progress_callback['current_chapter'] = 60

                # Integrate into .manga file
                from manga_reader_db_integration.database.manager import MangaDatabaseManager
                from manga_downloader_lib.src.format_utils import extract_manga_info

                logger.info("Parsing URL per ottenere titolo...")
                # Get manga title from URL (senza richiedere HTTP, usa solo parsing URL)
                manga_info = extract_manga_info(mangaworld_url)
                if not manga_info:
                    error_msg = (
                        f"URL non valido: {mangaworld_url}\n\n"
                        f"Formato atteso:\n"
                        f"https://www.mangaworld.ac/manga/<ID>/<NOME>\n"
                        f"(o altri domini supportati come .mx, .cc)\n\n"
                        f"Esempio:\n"
                        f"https://www.mangaworld.mx/manga/1234/mob-psycho-100\n\n"
                        f"Assicurati che l'URL contenga sia l'ID numerico che il nome del manga."
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                _, manga_title, _ = manga_info
                print(f"[MangaworldDownloader] DEBUG: Titolo estratto: {manga_title}")

                downloaded_path = os.path.join(temp_dir, manga_title)
                print(f"[MangaworldDownloader] DEBUG: Percorso download atteso: {downloaded_path}")

                if not os.path.exists(downloaded_path):
                    print(f"[MangaworldDownloader] ERRORE: Directory manga non trovata!")
                    print(f"[MangaworldDownloader] DEBUG: Contenuto temp_dir:")
                    for item in os.listdir(temp_dir):
                        print(f"  - {item}")
                    return False

                # Find volume folder
                volume_folders = [d for d in os.listdir(downloaded_path)
                                  if os.path.isdir(os.path.join(downloaded_path, d)) and d.startswith("Volume")]

                print(f"[MangaworldDownloader] DEBUG: Volume folders trovate: {volume_folders}")

                if not volume_folders:
                    print(f"[MangaworldDownloader] ERRORE: Nessuna folder 'Volume' trovata!")
                    print(f"[MangaworldDownloader] DEBUG: Contenuto downloaded_path:")
                    for item in os.listdir(downloaded_path):
                        print(f"  - {item}")
                    return False

                actual_volume_path = os.path.join(downloaded_path, volume_folders[0])
                print(f"[MangaworldDownloader] DEBUG: Volume path: {actual_volume_path}")

                # Use database manager to insert
                print(f"[MangaworldDownloader] DEBUG: Apertura database: {manga_file_path}")
                db_manager = MangaDatabaseManager(manga_file_path)

                # Get existing volumes to determine order
                existing_volumes = db_manager.chapters.get_volumes()
                new_order = len(existing_volumes) + 1
                print(f"[MangaworldDownloader] DEBUG: Volumi esistenti: {len(existing_volumes)}, nuovo ordine: {new_order}")

                actual_volume_name = volume_name if volume_name else f"Volume {new_order}"
                print(f"[MangaworldDownloader] DEBUG: Nome volume: {actual_volume_name}")

                # Update progress
                if progress_callback:
                    progress_callback['current_step'] = 'Download copertina volume...'
                    progress_callback['total_chapters'] = 100
                    progress_callback['current_chapter'] = 70

                # Insert volume with cover if available
                cover_data = None
                try:
                    from main import get_manga_covers
                    all_covers, _ = get_manga_covers(mangaworld_url)
                    if all_covers and start_volume and 0 < start_volume <= len(all_covers):
                        import urllib.parse
                        import requests
                        specific_cover_url = all_covers[start_volume - 1]

                        try:
                            response = requests.get(specific_cover_url, headers={'User-Agent': 'Mozilla/5.0'})
                            response.raise_for_status()
                            cover_data = response.content
                        except Exception as e:
                            print(f"[MangaworldDownloader] Impossibile scaricare copertina: {e}")
                except Exception as e:
                    print(f"[MangaworldDownloader] Impossibile recuperare lista cover: {e}")

                print(f"[MangaworldDownloader] DEBUG: Inserimento volume nel database...")
                volume_id = db_manager.chapters.insert_volume(
                    name=actual_volume_name,
                    order=new_order,
                    cover=cover_data
                )
                print(f"[MangaworldDownloader] DEBUG: Volume inserito con ID: {volume_id}")

                if not volume_id:
                    print(f"[MangaworldDownloader] ERRORE: Impossibile inserire volume nel database!")
                    return False

                # Insert chapters and pages
                from manga_downloader_lib.src.pdf_generator import extract_number

                chapters = sorted([d for d in os.listdir(actual_volume_path)
                                   if os.path.isdir(os.path.join(actual_volume_path, d))],
                                  key=extract_number)

                total_real_chapters = len(chapters)
                print(f"[MangaworldDownloader] DEBUG: Capitoli trovati: {total_real_chapters}")
                print(f"[MangaworldDownloader] DEBUG: Lista capitoli: {chapters[:5]}...")  # Primi 5

                # Update progress - inizia da 80% per l'inserimento
                if progress_callback:
                    progress_callback['current_step'] = 'Inserimento capitoli nel database...'

                for chapter_order, chapter_dir_name in enumerate(chapters):
                    print(f"[MangaworldDownloader] DEBUG: Processando capitolo {chapter_order + 1}/{total_real_chapters}: {chapter_dir_name}")
                    chapter_path = os.path.join(actual_volume_path, chapter_dir_name)

                    # Update progress - calcola progresso da 80 a 100%
                    if progress_callback:
                        # Progresso base 80% + (20% * progresso_capitoli)
                        base_progress = 80
                        chapter_progress = int((chapter_order / total_real_chapters) * 20)
                        progress_callback['total_chapters'] = 100
                        progress_callback['current_chapter'] = base_progress + chapter_progress
                        progress_callback['current_step'] = f'Inserimento capitolo {chapter_order + 1}/{total_real_chapters}...'

                    chapter_id = db_manager.chapters.insert_chapter(
                        name=chapter_dir_name,
                        order=chapter_order + 1,
                        volume_id=volume_id
                    )

                    if not chapter_id:
                        continue

                    # Insert pages - BATCH INSERT per performance ottimali
                    pages = sorted([f for f in os.listdir(chapter_path)
                                    if os.path.isfile(os.path.join(chapter_path, f))],
                                   key=extract_number)

                    total_pages = len(pages)

                    # Leggi tutte le pagine in memoria (ottimizzato per batch insert)
                    pages_data = []
                    for page_number, page_filename in enumerate(pages):
                        page_file_path = os.path.join(chapter_path, page_filename)
                        with open(page_file_path, 'rb') as f:
                            page_data = f.read()
                        pages_data.append(page_data)

                        # Update progress durante lettura
                        if progress_callback and page_number % 10 == 0:  # Aggiorna ogni 10 pagine
                            page_progress_within_chapter = (page_number / total_pages) * (20 / total_real_chapters)
                            current_total = base_progress + chapter_progress + int(page_progress_within_chapter)
                            progress_callback['current_chapter'] = min(current_total, 99)
                            progress_callback['total_pages'] = total_pages
                            progress_callback['current_page'] = page_number + 1

                    # Batch insert per performance ottimali (50x più veloce!)
                    print(f"[MangaworldDownloader] DEBUG: Inserimento batch di {total_pages} pagine per capitolo {chapter_id}...")
                    success = db_manager.chapters.insert_pages_batch(
                        chapter_id=chapter_id,
                        pages_data=pages_data,
                        start_page_number=1,
                        batch_size=50  # Ottimale per SQLite
                    )
                    if success:
                        print(f"[MangaworldDownloader] DEBUG: Batch insert completato per capitolo {chapter_id}")
                    else:
                        print(f"[MangaworldDownloader] ERRORE: Batch insert fallito per capitolo {chapter_id}!")

                    # Update progress finale
                    if progress_callback:
                        current_total = base_progress + int(((chapter_order + 1) / total_real_chapters) * 20)
                        progress_callback['current_chapter'] = min(current_total, 99)

                print(f"[MangaworldDownloader] DEBUG: Tutti i capitoli inseriti con successo!")
                return True

            finally:
                # Cleanup temp directory
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

        except Exception as e:
            print(f"[MangaworldDownloader] Error adding volume: {e}")
            import traceback
            traceback.print_exc()
            return False
