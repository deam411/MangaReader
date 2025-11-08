#!/usr/bin/env python3
"""
Script di test per verificare il salvataggio e applicazione dello sfondo.

Esegui questo script per testare se l'immagine di sfondo viene salvata e applicata correttamente.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.settings import Settings

def test_background_settings():
    """Test delle impostazioni di sfondo."""
    print("=== Test Impostazioni Sfondo ===\n")

    settings = Settings()

    # Leggi impostazione corrente
    bg_image = settings.get("library.background_image", None)

    print(f"1. Impostazione corrente:")
    print(f"   library.background_image = {bg_image}")

    if bg_image:
        print(f"\n2. Verifica esistenza file:")
        if os.path.exists(bg_image):
            print(f"   ✓ File esiste: {bg_image}")
            print(f"   - Dimensione: {os.path.getsize(bg_image)} bytes")
        else:
            print(f"   ✗ File NON esiste: {bg_image}")
    else:
        print(f"\n2. Nessuna immagine configurata")
        print(f"   Per configurare un'immagine:")
        print(f"   - Apri l'applicazione")
        print(f"   - Vai in Impostazioni → Aspetto")
        print(f"   - Seleziona un'immagine per 'Sfondo Home (Libreria)'")
        print(f"   - Clicca OK per salvare")

    print(f"\n3. Test applicazione URL:")
    if bg_image and os.path.exists(bg_image):
        # Simula la conversione URL come nel codice
        bg_image_url = bg_image.replace('\\', '/')
        if not bg_image_url.startswith('file:///'):
            if bg_image_url.startswith('/'):
                bg_image_url = f'file://{bg_image_url}'
            else:
                bg_image_url = f'file:///{bg_image_url}'

        print(f"   Path originale: {bg_image}")
        print(f"   URL Qt CSS: {bg_image_url}")

        print(f"\n4. Stylesheet generato:")
        stylesheet = f"""
                QWidget#library_view {{
                    background-image: url({bg_image_url});
                    background-repeat: no-repeat;
                    background-position: center;
                    background-color: transparent;
                }}
        """
        print(stylesheet)

    print("\n=== Fine Test ===")

if __name__ == "__main__":
    test_background_settings()
