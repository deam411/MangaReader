"""
Modulo per la gestione centralizzata del logging.

Fornisce un sistema di logging configurabile che scrive su file e console,
con rotazione automatica dei log e livelli di severità appropriati.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str = "MangaReader",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Configura e restituisce un logger con handler per file e console.

    Args:
        name: Nome del logger (default: "MangaReader")
        level: Livello di logging (default: INFO)
        log_to_file: Se True, scrive i log su file (default: True)
        log_to_console: Se True, scrive i log su console (default: True)

    Returns:
        Logger configurato
    """
    logger = logging.getLogger(name)

    # Evita duplicazione handler se già configurato
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Formato dettagliato per i log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler per file - disabilitato per evitare conflitti con logger principale
    # Il plugin userà solo il console handler
    if log_to_file:
        # Commenta out per evitare conflitti di file lock
        pass
        # try:
        #     from .paths import get_data_dir
        #     log_dir = get_data_dir()
        #     os.makedirs(log_dir, exist_ok=True)
        #     log_file = os.path.join(log_dir, "manga_reader.log")
        #
        #     file_handler = RotatingFileHandler(
        #         log_file,
        #         maxBytes=10 * 1024 * 1024,  # 10MB
        #         backupCount=5,
        #         encoding='utf-8'
        #     )
        #     file_handler.setLevel(level)
        #     file_handler.setFormatter(formatter)
        #     logger.addHandler(file_handler)
        # except Exception as e:
        #     print(f"Errore inizializzazione file logging: {e}", file=sys.stderr)

    # Handler per console
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        # Formato più compatto per la console
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Ottiene un logger esistente o ne crea uno nuovo.

    Args:
        name: Nome del logger. Se None, usa il nome del modulo chiamante.

    Returns:
        Logger configurato
    """
    if name is None:
        # Usa il nome del modulo chiamante
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_module = inspect.getmodule(frame.f_back)
            if caller_module:
                name = caller_module.__name__
            else:
                name = "MangaReader"
        else:
            name = "MangaReader"

    logger = logging.getLogger(name)

    # Se il logger non è ancora configurato, configura con default
    if not logger.handlers:
        return setup_logger(name)

    return logger


# Logger principale dell'applicazione
main_logger = setup_logger("MangaReader", level=logging.INFO)
