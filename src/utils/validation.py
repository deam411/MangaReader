"""
Utility per validazione input e sanitizzazione dati.

Fornisce funzioni per validare e sanitizzare input utente,
prevenendo SQL injection, XSS, e altri attacchi.
"""

import re
from typing import Optional, Any
from ..exceptions import ValidationError
from ..logger import get_logger

logger = get_logger(__name__)

# Pattern per validazione
SAFE_TEXT_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?()\'\"]+$')
SAFE_TAG_PATTERN = re.compile(r'^[a-zA-Z0-9\-_,\s]+$')
YEAR_PATTERN = re.compile(r'^\d{4}$')

# Limiti lunghezza campi
MAX_TITLE_LENGTH = 200
MAX_AUTHOR_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 2000
MAX_LANGUAGE_LENGTH = 50
MAX_TAGS_LENGTH = 500
MAX_CHAPTER_NAME_LENGTH = 200
MAX_VOLUME_NAME_LENGTH = 100

# HTML tags pericolosi
DANGEROUS_HTML_TAGS = ['<script', '<iframe', '<object', '<embed', '<applet', '<meta', '<link']


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
        ValidationError: Se testo invalido
    """
    if not text:
        return ""

    # Rimuovi whitespace leading/trailing
    sanitized = text.strip()

    # Rimuovi HTML tags pericolosi (basic XSS prevention)
    for tag in DANGEROUS_HTML_TAGS:
        if tag.lower() in sanitized.lower():
            raise ValidationError(f"Contenuto HTML pericoloso rilevato: {tag}")

    # Rimuovi null bytes
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
        raise ValidationError(f"Ordine troppo grande: {order_int}")

    return order_int
