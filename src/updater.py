"""
Auto-updater per MangaReader.

Controlla GitHub releases per nuove versioni e permette download/installazione.
"""

import os
import sys
import urllib.request
import urllib.error
import json
import tempfile
import shutil
import subprocess
import platform
from typing import Optional, Dict, Tuple
from .constants import APP_VERSION
from .logger import get_logger
from .exceptions import ValidationError

logger = get_logger(__name__)

# GitHub repository info
GITHUB_REPO = "deam411/MangaReader"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"


def get_current_version() -> str:
    """
    Ottiene la versione corrente dell'applicazione.

    Returns:
        Stringa versione (es. "0.1.0")
    """
    return APP_VERSION


def parse_version(version_string: str) -> Tuple[int, int, int]:
    """
    Parsea una stringa versione in tupla (major, minor, patch).

    Args:
        version_string: Versione come stringa (es. "0.1.0" o "v0.1.0")

    Returns:
        Tupla (major, minor, patch)

    Raises:
        ValueError: Se il formato versione non è valido
    """
    # Rimuovi prefisso 'v' se presente
    version_string = version_string.lstrip('v')

    try:
        parts = version_string.split('.')
        if len(parts) != 3:
            raise ValueError(f"Formato versione invalido: {version_string}")

        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        return (major, minor, patch)
    except (ValueError, IndexError) as e:
        raise ValueError(f"Impossibile parsare versione '{version_string}': {e}")


def is_newer_version(current: str, latest: str) -> bool:
    """
    Verifica se latest è più recente di current.

    Args:
        current: Versione corrente
        latest: Versione da controllare

    Returns:
        True se latest > current
    """
    try:
        current_tuple = parse_version(current)
        latest_tuple = parse_version(latest)
        return latest_tuple > current_tuple
    except ValueError as e:
        logger.warning(f"Errore confronto versioni: {e}")
        return False


def check_for_updates() -> Optional[Dict]:
    """
    Controlla se ci sono aggiornamenti disponibili su GitHub.

    Returns:
        Dict con info aggiornamento se disponibile, None altrimenti
        {
            'version': '0.2.0',
            'download_url': 'https://...',
            'release_notes': 'Changelog...',
            'published_at': '2025-11-08T...',
            'asset_name': 'MangaReader.exe'
        }

    Raises:
        urllib.error.URLError: Se non c'è connessione internet
        json.JSONDecodeError: Se la risposta non è JSON valido
    """
    logger.info("Controllo aggiornamenti su GitHub...")

    try:
        # Request con User-Agent (richiesto da GitHub API)
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={'User-Agent': f'MangaReader/{APP_VERSION}'}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        latest_version = data.get('tag_name', '').lstrip('v')
        current_version = get_current_version()

        logger.info(f"Versione corrente: {current_version}, Ultima versione: {latest_version}")

        if not is_newer_version(current_version, latest_version):
            logger.info("Nessun aggiornamento disponibile")
            return None

        # Determina il file da scaricare in base al sistema operativo
        asset_name, download_url = _get_platform_asset(data.get('assets', []))

        if not download_url:
            logger.warning(f"Nessun asset trovato per la piattaforma {platform.system()}")
            return None

        return {
            'version': latest_version,
            'download_url': download_url,
            'release_notes': data.get('body', 'Nessuna nota di rilascio'),
            'published_at': data.get('published_at', ''),
            'asset_name': asset_name,
            'html_url': data.get('html_url', RELEASES_URL)
        }

    except urllib.error.URLError as e:
        logger.error(f"Errore connessione a GitHub: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Errore parsing risposta GitHub: {e}")
        raise
    except Exception as e:
        logger.error(f"Errore imprevisto controllo aggiornamenti: {e}")
        raise


def _get_platform_asset(assets: list) -> Tuple[Optional[str], Optional[str]]:
    """
    Trova l'asset corretto per la piattaforma corrente.

    Args:
        assets: Lista assets dalla GitHub release

    Returns:
        Tupla (asset_name, download_url) o (None, None)
    """
    system = platform.system()

    # Mapping piattaforma -> pattern nome file
    platform_patterns = {
        'Windows': 'MangaReader.exe',
        'Darwin': 'MangaReader.dmg',  # macOS
        'Linux': 'MangaReader'
    }

    pattern = platform_patterns.get(system)
    if not pattern:
        logger.warning(f"Piattaforma non supportata: {system}")
        return None, None

    for asset in assets:
        name = asset.get('name', '')
        # Match più preciso per evitare false positive
        # Es: "MangaReader" non deve matchare "MangaReader.exe"
        if system == 'Linux':
            # Linux: match esatto o senza estensione
            if name == pattern or (name.startswith(pattern) and '.' not in name):
                return name, asset.get('browser_download_url')
        else:
            # Windows/macOS: match per estensione
            if name.endswith(pattern) or name == pattern:
                return name, asset.get('browser_download_url')

    return None, None


def download_update(update_info: Dict, progress_callback=None) -> Optional[str]:
    """
    Scarica l'aggiornamento in una directory temporanea.

    Args:
        update_info: Dict con info aggiornamento da check_for_updates()
        progress_callback: Funzione opzionale callback(bytes_downloaded, total_bytes)

    Returns:
        Path al file scaricato, None se fallisce
    """
    download_url = update_info.get('download_url')
    asset_name = update_info.get('asset_name')

    if not download_url or not asset_name:
        logger.error("URL download o nome asset mancante")
        return None

    try:
        # Crea directory temporanea
        temp_dir = tempfile.mkdtemp(prefix='mangareader_update_')
        dest_path = os.path.join(temp_dir, asset_name)

        logger.info(f"Download aggiornamento da: {download_url}")
        logger.info(f"Destinazione: {dest_path}")

        # Download con progress
        def _report_progress(block_num, block_size, total_size):
            if progress_callback:
                downloaded = block_num * block_size
                progress_callback(downloaded, total_size)

        urllib.request.urlretrieve(
            download_url,
            dest_path,
            reporthook=_report_progress
        )

        logger.info(f"Download completato: {dest_path}")
        return dest_path

    except Exception as e:
        logger.error(f"Errore durante download: {e}")
        return None


def install_update(downloaded_file: str) -> bool:
    """
    Installa l'aggiornamento scaricato.

    Strategy:
    - Windows (.exe): Sostituisce exe corrente, richiede restart
    - macOS (.dmg): Apre DMG per installazione manuale
    - Linux: Sostituisce binario, richiede restart

    Args:
        downloaded_file: Path al file scaricato

    Returns:
        True se installazione avviata con successo
    """
    if not os.path.exists(downloaded_file):
        logger.error(f"File aggiornamento non trovato: {downloaded_file}")
        return False

    system = platform.system()

    try:
        if system == 'Windows':
            return _install_windows(downloaded_file)
        elif system == 'Darwin':  # macOS
            return _install_macos(downloaded_file)
        elif system == 'Linux':
            return _install_linux(downloaded_file)
        else:
            logger.error(f"Piattaforma non supportata: {system}")
            return False
    except Exception as e:
        logger.error(f"Errore durante installazione: {e}")
        return False


def _install_windows(downloaded_file: str) -> bool:
    """Installa aggiornamento su Windows."""
    try:
        # Ottieni path dell'eseguibile corrente
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            current_exe = sys.executable
        else:
            # Running as script - non supportato per auto-update
            logger.warning("Auto-update non supportato in modalità script")
            return False

        # Crea script batch per sostituire exe dopo chiusura
        batch_script = os.path.join(os.path.dirname(downloaded_file), 'update.bat')

        with open(batch_script, 'w') as f:
            f.write(f'@echo off\n')
            f.write(f'timeout /t 2 /nobreak\n')  # Attendi 2 secondi
            f.write(f'move /Y "{downloaded_file}" "{current_exe}"\n')
            f.write(f'start "" "{current_exe}"\n')
            f.write(f'del "%~f0"\n')  # Auto-elimina lo script

        # Esegui batch e chiudi applicazione
        subprocess.Popen([batch_script], shell=True)
        logger.info("Aggiornamento avviato, riavvio dell'applicazione...")

        return True

    except Exception as e:
        logger.error(f"Errore installazione Windows: {e}")
        return False


def _install_macos(downloaded_file: str) -> bool:
    """Installa aggiornamento su macOS."""
    try:
        # Su macOS, apri il DMG per installazione manuale
        subprocess.Popen(['open', downloaded_file])
        logger.info(f"DMG aperto: {downloaded_file}")
        logger.info("Trascina l'app nella cartella Applicazioni per completare l'aggiornamento")
        return True
    except Exception as e:
        logger.error(f"Errore apertura DMG: {e}")
        return False


def _install_linux(downloaded_file: str) -> bool:
    """Installa aggiornamento su Linux."""
    try:
        if getattr(sys, 'frozen', False):
            current_binary = sys.executable
        else:
            logger.warning("Auto-update non supportato in modalità script")
            return False

        # Backup del binario corrente
        backup_path = current_binary + '.backup'
        shutil.copy2(current_binary, backup_path)

        # Rendi eseguibile il nuovo file
        os.chmod(downloaded_file, 0o755)

        # Crea script shell per sostituire binario
        update_script = os.path.join(os.path.dirname(downloaded_file), 'update.sh')

        with open(update_script, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('sleep 2\n')
            f.write(f'mv "{downloaded_file}" "{current_binary}"\n')
            f.write(f'chmod +x "{current_binary}"\n')
            f.write(f'"{current_binary}" &\n')
            f.write(f'rm -- "$0"\n')  # Auto-elimina lo script

        os.chmod(update_script, 0o755)

        # Esegui script e chiudi applicazione
        subprocess.Popen([update_script])
        logger.info("Aggiornamento avviato, riavvio dell'applicazione...")

        return True

    except Exception as e:
        logger.error(f"Errore installazione Linux: {e}")
        return False


def get_update_info_text(update_info: Dict) -> str:
    """
    Formatta le informazioni sull'aggiornamento per display.

    Args:
        update_info: Dict con info aggiornamento

    Returns:
        Testo formattato
    """
    version = update_info.get('version', 'Unknown')
    notes = update_info.get('release_notes', 'Nessuna nota disponibile')
    published = update_info.get('published_at', '')

    # Limita lunghezza note
    if len(notes) > 500:
        notes = notes[:500] + "...\n\n(Vedi release completa su GitHub)"

    text = f"Nuova versione disponibile: v{version}\n\n"
    text += f"Pubblicata: {published[:10]}\n\n"
    text += f"Note di rilascio:\n{notes}\n"

    return text
