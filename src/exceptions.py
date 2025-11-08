"""
Custom exceptions per MangaReader.

Gerarchia di eccezioni per error handling consistente e informativo.
"""


class MangaReaderError(Exception):
    """
    Eccezione base per tutte le eccezioni di MangaReader.

    Tutte le eccezioni custom dovrebbero ereditare da questa.
    """
    pass


class DatabaseError(MangaReaderError):
    """Eccezioni relative a operazioni database."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Errore connessione database."""
    pass


class DatabaseSchemaError(DatabaseError):
    """Errore schema database (migrazione, creazione, etc.)."""
    pass


class DatabaseQueryError(DatabaseError):
    """Errore esecuzione query."""
    pass


class ImportError(MangaReaderError):
    """Eccezioni durante import manga/archivi."""
    pass


class ArchiveFormatError(ImportError):
    """Formato archivio non supportato o corrotto."""
    pass


class MetadataError(ImportError):
    """Errore metadata manga (mancanti o invalidi)."""
    pass


class ValidationError(MangaReaderError):
    """Eccezioni validazione dati."""
    pass


class FileSizeError(ValidationError):
    """File troppo grande."""

    def __init__(self, actual_size_mb, max_size_mb):
        self.actual_size_mb = actual_size_mb
        self.max_size_mb = max_size_mb
        super().__init__(
            f"File troppo grande: {actual_size_mb:.1f}MB. Massimo: {max_size_mb}MB"
        )


class FileFormatError(ValidationError):
    """Formato file non supportato."""

    def __init__(self, file_path, expected_formats=None):
        self.file_path = file_path
        self.expected_formats = expected_formats
        msg = f"Formato file non supportato: {file_path}"
        if expected_formats:
            msg += f". Formati attesi: {', '.join(expected_formats)}"
        super().__init__(msg)


class CacheError(MangaReaderError):
    """Eccezioni gestione cache."""
    pass


class CacheCorruptedError(CacheError):
    """Cache corrotta o invalida."""
    pass


class SettingsError(MangaReaderError):
    """Eccezioni gestione settings."""
    pass


class SettingsLoadError(SettingsError):
    """Errore caricamento settings."""
    pass


class SettingsSaveError(SettingsError):
    """Errore salvataggio settings."""
    pass


class ReaderError(MangaReaderError):
    """Eccezioni lettore manga."""
    pass


class PageLoadError(ReaderError):
    """Errore caricamento pagina."""

    def __init__(self, page_number, chapter_id=None):
        self.page_number = page_number
        self.chapter_id = chapter_id
        msg = f"Errore caricamento pagina {page_number}"
        if chapter_id:
            msg += f" (capitolo {chapter_id})"
        super().__init__(msg)


class ChapterNotFoundError(ReaderError):
    """Capitolo non trovato."""

    def __init__(self, chapter_id):
        self.chapter_id = chapter_id
        super().__init__(f"Capitolo non trovato: {chapter_id}")
