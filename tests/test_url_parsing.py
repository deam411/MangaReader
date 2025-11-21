from urllib.parse import urlparse
import re
import sys

# Mocking config
NUM_URL_PATH_PARTS = 3

def conv2uppercase(string: str) -> str:
    """Convert the first letter of each word in the string to uppercase."""
    return string.group(1) + string.group(2).upper()

def extract_manga_info(url: str) -> tuple:
    """Extract manga slug and format the manga name from a given URL."""
    parsed_url = urlparse(url)

    # Check if the URL path contains the expected structure
    path_parts = parsed_url.path.strip("/").split("/")

    print(f"DEBUG: url='{url}'")
    print(f"DEBUG: path='{parsed_url.path}'")
    print(f"DEBUG: path_parts={path_parts}")

    if len(path_parts) < NUM_URL_PATH_PARTS or path_parts[0] != "manga":
        # logging.error("Invalid URL format: Expected '/manga/<id>/<name>'")
        return None

    manga_id = path_parts[1]
    manga_slug = path_parts[2]

    try:
        formatted_manga_name = re.sub(
            r"(^|\s)(\S)",
            conv2uppercase,
            manga_slug.replace("-", " "),
        )

    except IndexError:
        # logging.exception("Invalid URL format.")
        return None

    return manga_id, formatted_manga_name, manga_slug

def test_urls():
    test_cases = [
        "https://www.mangaworld.ac/manga/3033/mob-psycho-100/",
        "https://www.mangaworld.ac/manga/3033/mob-psycho-100",
        "https://www.mangaworld.mx/manga/3033/mob-psycho-100/",
        "https://www.mangaworld.mx/manga/3033/mob-psycho-100",
        "http://mangaworld.mx/manga/3033/mob-psycho-100",
        "https://www.mangaworld.mx/manga/3033/mob-psycho-100?style=list",
        # Potential failure cases
        "https://www.mangaworld.mx/manga/3033/", # Missing name
        "https://www.mangaworld.mx/manga/mob-psycho-100", # Missing ID
        "'https://www.mangaworld.mx/manga/3033/mob-psycho-100'", # With quotes
        '"https://www.mangaworld.mx/manga/3033/mob-psycho-100"', # With double quotes
    ]

    print("--- Testing extract_manga_info ---")
    for url in test_cases:
        print(f"\nTesting: {url}")
        # Simulate the fix in plugin.py
        cleaned_url = url.strip().strip('"').strip("'")
        if not cleaned_url.startswith("http"):
            cleaned_url = "https://" + cleaned_url
            print(f"Added protocol: {cleaned_url}")
        
        if cleaned_url != url:
            print(f"Cleaned URL: {cleaned_url}")
        
        result = extract_manga_info(cleaned_url)
        if result:
            print(f"SUCCESS: {result}")
        else:
            print(f"FAILURE: Invalid URL")

if __name__ == "__main__":
    test_urls()
