"""
Script per convertire un'immagine in formato .ico per l'icona dell'app
Supporta PNG, JPG, JPEG, BMP, GIF
"""

import sys
from PIL import Image
import os

def convert_to_ico(input_path, output_path="icon.ico"):
    """
    Converte un'immagine in formato .ico

    Args:
        input_path: Percorso dell'immagine di input
        output_path: Percorso dell'icona .ico di output (default: icon.ico)
    """
    try:
        # Apri l'immagine
        img = Image.open(input_path)

        # Converti in RGBA se necessario
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Crea diverse dimensioni per l'icona Windows
        # Windows usa diverse dimensioni: 16x16, 32x32, 48x48, 256x256
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

        # Salva come .ico con multiple dimensioni
        img.save(output_path, format='ICO', sizes=sizes)

        print(f"[OK] Icona creata con successo: {output_path}")
        print(f"     Dimensioni incluse: {', '.join([f'{w}x{h}' for w, h in sizes])}")
        return True

    except FileNotFoundError:
        print(f"[X] Errore: File non trovato '{input_path}'")
        return False
    except Exception as e:
        print(f"[X] Errore durante la conversione: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Convertitore Immagine -> .ico per Manga Reader")
    print("=" * 50)
    print()

    if len(sys.argv) < 2:
        print("Utilizzo: python convert_to_ico.py <immagine_input> [output.ico]")
        print()
        print("Esempio:")
        print("  python convert_to_ico.py logo.png")
        print("  python convert_to_ico.py logo.png ../assets/icon.ico")
        print()
        print("Formati supportati: PNG, JPG, JPEG, BMP, GIF")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join("..", "assets", "icon.ico")

    # Crea la directory di output se non esiste
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[OK] Creata directory: {output_dir}")

    if convert_to_ico(input_file, output_file):
        print()
        print("Prossimi passi:")
        print("1. Verifica l'icona in:", output_file)
        print("2. Esegui 'build.bat' per ricompilare con la nuova icona")
    else:
        sys.exit(1)
