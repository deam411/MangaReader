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
            version="1.0.0",
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

            try:
                # Update progress
                if progress_callback:
                    progress_callback['current_step'] = 'Connessione a Mangaworld...'

                import time

                # Use the downloader library to download
                from manga_downloader_lib.src.config import set_download_folder
                from manga_downloader_lib.manga_downloader import process_manga_download

                set_download_folder(temp_dir)

                if progress_callback:
                    progress_callback['current_step'] = 'Download capitoli in corso...'

                # Download the volume
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
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

                finally:
                    loop.close()

                # Update progress
                if progress_callback:
                    progress_callback['current_step'] = 'Download completato! Preparazione integrazione...'
                    progress_callback['total_chapters'] = 100
                    progress_callback['current_chapter'] = 60

                # Integrate into .manga file
                from manga_reader_db_integration.database.manager import MangaDatabaseManager
                from main import get_manga_covers

                # Get manga title from URL
                _, manga_title = get_manga_covers(mangaworld_url)
                if not manga_title:
                    return False

                downloaded_path = os.path.join(temp_dir, manga_title)
                if not os.path.exists(downloaded_path):
                    return False

                # Find volume folder
                volume_folders = [d for d in os.listdir(downloaded_path)
                                  if os.path.isdir(os.path.join(downloaded_path, d)) and d.startswith("Volume")]

                if not volume_folders:
                    return False

                actual_volume_path = os.path.join(downloaded_path, volume_folders[0])

                # Use database manager to insert
                db_manager = MangaDatabaseManager(manga_file_path)

                # Get existing volumes to determine order
                existing_volumes = db_manager.chapters.get_volumes()
                new_order = len(existing_volumes) + 1

                actual_volume_name = volume_name if volume_name else f"Volume {new_order}"

                # Update progress
                if progress_callback:
                    progress_callback['current_step'] = 'Download copertina volume...'
                    progress_callback['total_chapters'] = 100
                    progress_callback['current_chapter'] = 70

                # Insert volume with cover if available
                cover_data = None
                all_covers, _ = get_manga_covers(mangaworld_url)
                if all_covers and start_volume and 0 < start_volume <= len(all_covers):
                    import urllib.parse
                    import requests
                    specific_cover_url = all_covers[start_volume - 1]

                    try:
                        response = requests.get(specific_cover_url, headers={'User-Agent': 'Mozilla/5.0'})
                        response.raise_for_status()
                        cover_data = response.content
                    except:
                        pass

                volume_id = db_manager.chapters.insert_volume(
                    name=actual_volume_name,
                    order=new_order,
                    cover=cover_data
                )

                if not volume_id:
                    return False

                # Insert chapters and pages
                from manga_downloader_lib.src.pdf_generator import extract_number

                chapters = sorted([d for d in os.listdir(actual_volume_path)
                                   if os.path.isdir(os.path.join(actual_volume_path, d))],
                                  key=extract_number)

                total_real_chapters = len(chapters)

                # Update progress - inizia da 80% per l'inserimento
                if progress_callback:
                    progress_callback['current_step'] = 'Inserimento capitoli nel database...'

                for chapter_order, chapter_dir_name in enumerate(chapters):
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

                    # Insert pages
                    pages = sorted([f for f in os.listdir(chapter_path)
                                    if os.path.isfile(os.path.join(chapter_path, f))],
                                   key=extract_number)

                    total_pages = len(pages)

                    for page_number, page_filename in enumerate(pages):
                        page_file_path = os.path.join(chapter_path, page_filename)
                        with open(page_file_path, 'rb') as f:
                            page_data = f.read()

                        # Update progress per pagina - micro incrementi
                        if progress_callback:
                            # Calcola progresso fine all'interno del capitolo
                            page_progress_within_chapter = (page_number / total_pages) * (20 / total_real_chapters)
                            current_total = base_progress + chapter_progress + int(page_progress_within_chapter)
                            progress_callback['current_chapter'] = min(current_total, 99)
                            progress_callback['total_pages'] = total_pages
                            progress_callback['current_page'] = page_number + 1

                        db_manager.chapters.insert_page(
                            chapter_id=chapter_id,
                            page_number=page_number + 1,
                            image_data_or_path=page_data
                        )

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
