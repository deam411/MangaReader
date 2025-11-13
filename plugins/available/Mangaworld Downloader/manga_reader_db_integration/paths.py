"""
Modulo per gestire i percorsi dell'applicazione in modo centralizzato e portabile.
Tutti i percorsi sono relativi alla directory del progetto.
"""
import os
import sys


def get_project_root():
    """
    Restituisce la directory root del progetto.
    Funziona sia con Python che con eseguibile PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # Se siamo in un eseguibile compilato
        return os.path.dirname(sys.executable)
    else:
        # Se siamo in sviluppo
        current_file = os.path.abspath(__file__)
        src_dir = os.path.dirname(current_file)
        project_root = os.path.dirname(src_dir)
        return project_root


def get_manga_dir():
    """
    Restituisce il percorso della directory dove vengono salvati i file .manga
    Crea la directory se non esiste.

    Ora supporta la libreria custom tramite le settings.
    """
    # Prova a importare settings
    try:
        from .settings import Settings
        settings = Settings()
        manga_dir = settings.get_library_path()

        # Se c'è un percorso custom nelle settings, usalo
        if manga_dir:
            # Crea la directory se non esiste
            if not os.path.exists(manga_dir):
                try:
                    os.makedirs(manga_dir)
                except Exception as e:
                    print(f"Impossibile creare directory custom: {e}")
                    # Se fallisce la creazione, usa il default
                    manga_dir = None

            if manga_dir:
                return manga_dir
    except Exception as e:
        print(f"Errore caricamento settings: {e}")

    # Fallback al percorso di default SOLO se non c'è una directory custom
    manga_dir = os.path.join(get_project_root(), "manga")
    if not os.path.exists(manga_dir):
        os.makedirs(manga_dir)
    return manga_dir


def get_data_dir():
    """
    Restituisce il percorso della directory per dati generici dell'applicazione.
    Usa AppData su Windows, ~/.mangareader su Linux/Mac per persistenza.
    Crea la directory se non esiste.
    """
    if sys.platform == "win32":
        # Windows: usa AppData\Local
        appdata = os.getenv('LOCALAPPDATA')
        if appdata:
            data_dir = os.path.join(appdata, "MangaReader")
        else:
            # Fallback
            data_dir = os.path.join(os.path.expanduser("~"), ".mangareader")
    else:
        # Linux/Mac: usa home directory
        data_dir = os.path.join(os.path.expanduser("~"), ".mangareader")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir


# Alias per compatibilità con nuovi moduli v0.3.0
def get_app_data_dir():
    """Alias per get_data_dir() per compatibilità."""
    return get_data_dir()
