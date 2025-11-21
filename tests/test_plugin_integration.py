"""
Test script per debuggare il plugin Mangaworld Downloader
"""
import sys
import os

# Aggiungi il plugin al path
plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins', 'available', 'Mangaworld Downloader')
sys.path.insert(0, plugin_dir)

from plugin import MangaworldDownloaderPlugin

# Parametri di test
manga_file = input("Inserisci il percorso completo del file .manga: ")
url = "https://www.mangaworld.mx/manga/3033/mob-psycho-100"
volume_num = "1"
volume_name = "Volume 1"

print("\n" + "="*80)
print("TEST INTEGRAZIONE PLUGIN MANGAWORLD DOWNLOADER")
print("="*80)
print(f"File .manga: {manga_file}")
print(f"URL: {url}")
print(f"Volume: {volume_num}")
print(f"Nome: {volume_name}")
print("="*80 + "\n")

# Progress callback
progress_data = {
    'current_step': 'Inizializzazione...',
    'current_chapter': 0,
    'total_chapters': 0,
    'current_page': 0,
    'total_pages': 0
}

print("Inizio download e integrazione...\n")

try:
    success = MangaworldDownloaderPlugin.add_volume_to_manga_file(
        manga_file_path=manga_file,
        mangaworld_url=url,
        volume_number=volume_num,
        volume_name=volume_name,
        progress_callback=progress_data
    )

    print("\n" + "="*80)
    if success:
        print("✓ SUCCESSO! Volume aggiunto correttamente al file .manga")
    else:
        print("✗ FALLITO! Il volume NON è stato aggiunto")
    print("="*80)

except Exception as e:
    print("\n" + "="*80)
    print("✗ ERRORE DURANTE L'ESECUZIONE:")
    print("="*80)
    import traceback
    traceback.print_exc()
    print("="*80)
