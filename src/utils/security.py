"""
Security utilities per MangaReader v0.2.0.

Centralizza tutte le funzioni di validazione e sanitizzazione per:
- Input validation (titoli, autori, descrizioni)
- Path traversal prevention
- Filename sanitization
- Archive extraction security (Zip Slip protection)
- XSS prevention
- SQL injection prevention

Modulo unico per tutte le operazioni di sicurezza dell'applicazione.
"""

import os
import re
from pathlib import Path
from typing import Optional, Any
from src.logger import get_logger
from src.exceptions import ValidationError

logger = get_logger(__name__)

# ============================================================================
# PATTERN DI VALIDAZIONE
# ============================================================================

# Pattern per validazione testo sicuro
SAFE_TEXT_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?()\'\"]+$')
SAFE_TAG_PATTERN = re.compile(r'^[a-zA-Z0-9\-_,\s]+$')
YEAR_PATTERN = re.compile(r'^\d{4}$')

# Caratteri vietati nei filename (Windows + sicurezza)
FORBIDDEN_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f]'

# Nomi riservati Windows
WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
}

# HTML tags pericolosi (XSS prevention)
DANGEROUS_HTML_TAGS = ['<script', '<iframe', '<object', '<embed', '<applet', '<meta', '<link']

# ============================================================================
# LIMITI LUNGHEZZA CAMPI
# ============================================================================

MAX_TITLE_LENGTH = 200
MAX_AUTHOR_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 2000
MAX_LANGUAGE_LENGTH = 50
MAX_TAGS_LENGTH = 500
MAX_CHAPTER_NAME_LENGTH = 200
MAX_VOLUME_NAME_LENGTH = 100
MAX_FILENAME_LENGTH = 255


# ============================================================================
# SANITIZZAZIONE TESTO
# ============================================================================

def sanitize_text(text: str, allow_unicode: bool = True, max_length: Optional[int] = None) -> str:
    """
    Sanitizza testo generico rimuovendo contenuto pericoloso.

    Args:
        text: Testo da sanitizzare
        allow_unicode: Se True, permette caratteri unicode
        max_length: Lunghezza massima (opzionale)

    Returns:
        Testo sanitizzato

    Raises:
        ValidationError: Se testo contiene contenuto pericoloso

    Security:
        - Rimuove HTML tags pericolosi (XSS prevention)
        - Rimuove null bytes
        - Valida pattern caratteri safe
    """
    if not text:
        return ""

    # Rimuovi whitespace leading/trailing
    sanitized = text.strip()

    # Rimuovi HTML tags pericolosi (basic XSS prevention)
    for tag in DANGEROUS_HTML_TAGS:
        if tag.lower() in sanitized.lower():
            raise ValidationError(f"Contenuto HTML pericoloso rilevato: {tag}")

    # Rimuovi null bytes (security: SQL injection, path traversal)
    sanitized = sanitized.replace('\x00', '')

    # Limita lunghezza
    if max_length and len(sanitized) > max_length:
        logger.warning(f"Testo troncato da {len(sanitized)} a {max_length} caratteri")
        sanitized = sanitized[:max_length]

    # Se non unicode, valida solo caratteri safe
    if not allow_unicode:
        if not SAFE_TEXT_PATTERN.match(sanitized):
            raise ValidationError("Testo contiene caratteri non permessi")

    return sanitized


def sanitize_filename(filename: str, max_length: int = MAX_FILENAME_LENGTH, replacement: str = '_') -> str:
    """
    Sanitizza un filename rimuovendo caratteri pericolosi e path traversal.

    Versione centralizzata che supporta Unicode ma rimuove caratteri riservati.

    Args:
        filename: Nome file da sanitizzare
        max_length: Lunghezza massima del filename (default 255)
        replacement: Carattere con cui sostituire i caratteri invalidi

    Returns:
        Filename sanitizzato e sicuro

    Raises:
        ValidationError: Se filename risulta vuoto dopo sanitizzazione

    Security:
        - Path traversal prevention (rimuove ../, ..\\ etc)
        - Windows reserved names protection
        - Filesystem-safe characters only
        - Null byte removal
    """
    if not filename:
        raise ValidationError("Filename vuoto")

    # SECURITY: Estrai solo il basename (rimuove path traversal ../ e simili)
    filename = os.path.basename(filename)

    # SECURITY: Rimuovi caratteri vietati (filesystem + control chars)
    # Pattern: < > : " / \ | ? * e caratteri di controllo (0x00-0x1F)
    sanitized = re.sub(FORBIDDEN_FILENAME_CHARS, replacement, filename)

    # Rimuovi spazi multipli e trailing/leading spaces
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    # SECURITY: Rimuovi punti multipli (potenziale path traversal)
    sanitized = re.sub(r'\.{2,}', replacement, sanitized)

    # Rimuovi punti e spazi finali (problematici su Windows)
    sanitized = sanitized.strip('. ')

    # SECURITY: Verifica nomi riservati Windows (case-insensitive)
    name_without_ext = Path(sanitized).stem.upper()
    if name_without_ext in WINDOWS_RESERVED_NAMES:
        sanitized = f"file_{sanitized}"
        logger.warning(f"Nome riservato Windows rilevato, rinominato in: {sanitized}")

    # Limita lunghezza preservando estensione
    if len(sanitized) > max_length:
        ext = Path(sanitized).suffix
        max_name_len = max_length - len(ext)
        sanitized = sanitized[:max_name_len] + ext
        logger.debug(f"Filename troncato a {max_length} caratteri")

    # Verifica che il risultato non sia vuoto
    if not sanitized or sanitized.isspace():
        raise ValidationError(f"Filename invalido dopo sanitizzazione: '{filename}'")

    return sanitized


def is_safe_path(base_path: str, target_path: str) -> bool:
    """
    Verifica che target_path sia contenuto in base_path (protezione path traversal).

    Previene attacchi Zip Slip e directory traversal.

    Args:
        base_path: Directory base sicura
        target_path: Path target da validare

    Returns:
        True se il path è sicuro, False se rilevato path traversal

    Security:
        - Zip Slip prevention
        - Directory traversal prevention
        - Symlink resolution
    """
    # Risolvi path assoluti (risolve anche symlink)
    base = os.path.realpath(base_path)
    target = os.path.realpath(target_path)

    # SECURITY: Verifica che target sia sotto base
    # Aggiunge os.sep per prevenire false positive (es: /base vs /base_other)
    return target.startswith(base + os.sep) or target == base


# ============================================================================
# VALIDAZIONE METADATA MANGA
# ============================================================================

def validate_title(title: str) -> str:
    """
    Valida e sanitizza titolo manga.

    Args:
        title: Titolo da validare

    Returns:
        Titolo sanitizzato

    Raises:
        ValidationError: Se titolo invalido
    """
    if not title or not title.strip():
        raise ValidationError("Titolo vuoto")

    sanitized = sanitize_text(title, allow_unicode=True, max_length=MAX_TITLE_LENGTH)

    if len(sanitized) < 1:
        raise ValidationError("Titolo troppo corto")

    return sanitized


def validate_author(author: Optional[str]) -> Optional[str]:
    """
    Valida e sanitizza autore manga.

    Args:
        author: Autore da validare (opzionale)

    Returns:
        Autore sanitizzato o None

    Raises:
        ValidationError: Se autore invalido
    """
    if not author:
        return None

    return sanitize_text(author, allow_unicode=True, max_length=MAX_AUTHOR_LENGTH)


def validate_description(description: Optional[str]) -> Optional[str]:
    """
    Valida e sanitizza descrizione manga.

    Args:
        description: Descrizione da validare (opzionale)

    Returns:
        Descrizione sanitizzata o None

    Raises:
        ValidationError: Se descrizione invalida
    """
    if not description:
        return None

    return sanitize_text(description, allow_unicode=True, max_length=MAX_DESCRIPTION_LENGTH)


def validate_language(language: Optional[str]) -> Optional[str]:
    """
    Valida e sanitizza lingua manga.

    Args:
        language: Lingua da validare (opzionale)

    Returns:
        Lingua sanitizzata o None

    Raises:
        ValidationError: Se lingua invalida
    """
    if not language:
        return None

    sanitized = sanitize_text(language, allow_unicode=True, max_length=MAX_LANGUAGE_LENGTH)

    # Verifica lunghezza minima (almeno 2 caratteri per codice lingua)
    if len(sanitized) < 2:
        raise ValidationError("Codice lingua troppo corto")

    return sanitized


def validate_year(year: Optional[int]) -> Optional[int]:
    """
    Valida anno pubblicazione.

    Args:
        year: Anno da validare (opzionale)

    Returns:
        Anno validato o None

    Raises:
        ValidationError: Se anno invalido
    """
    if year is None:
        return None

    # Converti a int se stringa
    if isinstance(year, str):
        if not YEAR_PATTERN.match(year):
            raise ValidationError(f"Anno invalido: {year}")
        year = int(year)

    # Valida range ragionevole (1900-2100)
    if not isinstance(year, int) or year < 1900 or year > 2100:
        raise ValidationError(f"Anno fuori range (1900-2100): {year}")

    return year


def validate_tags(tags: Optional[str]) -> Optional[str]:
    """
    Valida e sanitizza tags manga.

    Args:
        tags: Tags da validare (comma-separated, opzionale)

    Returns:
        Tags sanitizzati o None

    Raises:
        ValidationError: Se tags invalidi
    """
    if not tags:
        return None

    # Rimuovi whitespace
    sanitized = tags.strip()

    # Valida pattern (solo alfanumerici, trattini, virgole)
    if not SAFE_TAG_PATTERN.match(sanitized):
        raise ValidationError("Tags contengono caratteri non permessi")

    # Limita lunghezza
    if len(sanitized) > MAX_TAGS_LENGTH:
        logger.warning(f"Tags troncati da {len(sanitized)} a {MAX_TAGS_LENGTH} caratteri")
        sanitized = sanitized[:MAX_TAGS_LENGTH]

    return sanitized


# ============================================================================
# VALIDAZIONE STRUCTURE (VOLUMES/CHAPTERS)
# ============================================================================

def validate_chapter_name(name: str) -> str:
    """
    Valida nome capitolo.

    Args:
        name: Nome da validare

    Returns:
        Nome sanitizzato

    Raises:
        ValidationError: Se nome invalido
    """
    if not name or not name.strip():
        raise ValidationError("Nome capitolo vuoto")

    return sanitize_text(name, allow_unicode=True, max_length=MAX_CHAPTER_NAME_LENGTH)


def validate_volume_name(name: str) -> str:
    """
    Valida nome volume.

    Args:
        name: Nome da validare

    Returns:
        Nome sanitizzato

    Raises:
        ValidationError: Se nome invalido
    """
    if not name or not name.strip():
        raise ValidationError("Nome volume vuoto")

    return sanitize_text(name, allow_unicode=True, max_length=MAX_VOLUME_NAME_LENGTH)


def validate_order(order: Any) -> int:
    """
    Valida numero ordine (capitolo/volume/pagina).

    Args:
        order: Ordine da validare

    Returns:
        Ordine validato

    Raises:
        ValidationError: Se ordine invalido
    """
    try:
        order_int = int(order)
    except (ValueError, TypeError):
        raise ValidationError(f"Ordine non è un numero valido: {order}")

    if order_int < 1:
        raise ValidationError(f"Ordine deve essere >= 1: {order_int}")

    if order_int > 99999:
        raise ValidationError(f"Ordine troppo grande (max 99999): {order_int}")

    return order_int


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_valid_image_extension(filename: str, allowed_extensions: tuple) -> bool:
    """
    Verifica se un file ha un'estensione immagine valida.

    Args:
        filename: Nome file da validare
        allowed_extensions: Tuple di estensioni permesse (es: ('.png', '.jpg'))

    Returns:
        True se estensione valida
    """
    ext = Path(filename).suffix.lower()
    return ext in allowed_extensions


def validate_image_size(image_data: bytes, max_size_mb: float) -> bool:
    """
    Valida dimensione immagine.

    Args:
        image_data: Dati immagine
        max_size_mb: Dimensione massima in MB

    Returns:
        True se dimensione valida, False altrimenti
    """
    image_size_mb = len(image_data) / (1024 * 1024)

    if image_size_mb > max_size_mb:
        logger.warning(f"Immagine troppo grande: {image_size_mb:.1f}MB (max: {max_size_mb}MB)")
        return False

    return True
