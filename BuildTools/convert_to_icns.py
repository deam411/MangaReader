"""
Script per convertire un'immagine in formato .icns per macOS
Funziona su qualsiasi piattaforma (Windows, Mac, Linux)
"""

import sys
from PIL import Image
import os

def convert_to_icns(input_path, output_path="icon.icns"):
    """
    Converte un'immagine in formato .icns per macOS

    Args:
        input_path: Percorso dell'immagine di input
        output_path: Percorso dell'icona .icns di output (default: icon.icns)
    """
    try:
        # Apri l'immagine
        img = Image.open(input_path)

        # Converti in RGBA se necessario
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # macOS richiede diverse dimensioni per .icns
        # Creiamo un iconset (cartella temporanea)
        iconset_path = output_path.replace('.icns', '.iconset')

        if not os.path.exists(iconset_path):
            os.makedirs(iconset_path)

        # Dimensioni richieste da macOS
        sizes = [
            (16, 16, 'icon_16x16.png'),
            (32, 32, 'icon_16x16@2x.png'),
            (32, 32, 'icon_32x32.png'),
            (64, 64, 'icon_32x32@2x.png'),
            (128, 128, 'icon_128x128.png'),
            (256, 256, 'icon_128x128@2x.png'),
            (256, 256, 'icon_256x256.png'),
            (512, 512, 'icon_256x256@2x.png'),
            (512, 512, 'icon_512x512.png'),
            (1024, 1024, 'icon_512x512@2x.png'),
        ]

        print(f"[1/3] Creando iconset con {len(sizes)} dimensioni...")
        for width, height, filename in sizes:
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            resized.save(os.path.join(iconset_path, filename))
            print(f"  OK {filename}")

        print(f"\n[2/3] Iconset creato in: {iconset_path}")

        # Su macOS, usa iconutil per convertire a .icns
        if sys.platform == 'darwin':
            print(f"\n[3/3] Convertendo a .icns con iconutil...")
            import subprocess
            result = subprocess.run(['iconutil', '-c', 'icns', iconset_path, '-o', output_path])
            if result.returncode == 0:
                print(f"[OK] Icona .icns creata: {output_path}")
                # Pulizia
                import shutil
                shutil.rmtree(iconset_path)
                return True
            else:
                print(f"[X] Errore nella conversione con iconutil")
                return False
        else:
            # Su Windows/Linux, salviamo l'iconset per usarlo su Mac
            print(f"\n[3/3] iconutil non disponibile (non su macOS)")
            print(f"[OK] Iconset creato: {iconset_path}")
            print(f"\nPer creare il .icns su Mac, esegui:")
            print(f"  iconutil -c icns {iconset_path} -o {output_path}")
            print(f"\nOppure usa GitHub Actions che lo farà automaticamente!")
            return True

    except FileNotFoundError:
        print(f"[X] Errore: File non trovato '{input_path}'")
        return False
    except Exception as e:
        print(f"[X] Errore durante la conversione: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Convertitore Immagine -> .icns per macOS")
    print("=" * 60)
    print()

    if len(sys.argv) < 2:
        print("Utilizzo: python convert_to_icns.py <immagine_input> [output.icns]")
        print()
        print("Esempio:")
        print("  python convert_to_icns.py logo.png")
        print("  python convert_to_icns.py logo.png ../assets/icon.icns")
        print()
        print("Formati supportati: PNG, JPG, JPEG, BMP, GIF")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join("..", "assets", "icon.icns")

    # Crea la directory di output se non esiste
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[OK] Creata directory: {output_dir}\n")

    if convert_to_icns(input_file, output_file):
        print()
        print("=" * 60)
        print("Conversione completata!")
        print("=" * 60)
    else:
        sys.exit(1)
