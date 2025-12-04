import sys
import os
import logging

# Add plugin directory to path
plugin_dir = os.path.abspath("plugins/available/Mangaworld Downloader")
sys.path.insert(0, plugin_dir)

from manga_downloader_lib.src.format_utils import extract_manga_info
from manga_downloader_lib.src.crawler_utils import clean_chapter_title

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_url_parsing():
    url = "https://www.mangaworld.mx/manga/3033/mob-psycho-100"
    print(f"Testing URL: {url}")
    
    try:
        info = extract_manga_info(url)
        if info:
            manga_id, manga_title, _ = info
            print(f"SUCCESS: ID={manga_id}, Title={manga_title}")
        else:
            print("FAILURE: extract_manga_info returned None")
    except Exception as e:
        print(f"EXCEPTION in extract_manga_info: {e}")

def test_chapter_titles():
    # Test some potential chapter titles from Mob Psycho 100
    titles = [
        "Capitolo 1",
        "Volume 1 Capitolo 1",
        "Mob Psycho 100 1",
        "Capitolo 100.5",
        "Volume 1"
    ]
    
    print("\nTesting Chapter Titles:")
    for t in titles:
        cleaned = clean_chapter_title(t)
        print(f"'{t}' -> '{cleaned}'")

if __name__ == "__main__":
    test_url_parsing()
    test_chapter_titles()
