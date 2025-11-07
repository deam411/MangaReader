"""
Test per il modulo logger.
Verifica configurazione logging, rotazione file e gestione handler.
"""
import pytest
import logging
import os
import tempfile
from unittest.mock import patch, MagicMock
from src import logger as logger_module


class TestSetupLogger:
    """Test per la funzione setup_logger()."""

    def test_setup_logger_basic(self):
        """Verifica setup logger base."""
        test_logger = logger_module.setup_logger(
            name="test_basic",
            log_to_file=False,  # Disabilita file per test più veloce
            log_to_console=True
        )

        assert isinstance(test_logger, logging.Logger)
        assert test_logger.name == "test_basic"
        assert test_logger.level == logging.INFO

    def test_setup_logger_with_level(self):
        """Verifica configurazione con livello custom."""
        test_logger = logger_module.setup_logger(
            name="test_level",
            level=logging.DEBUG,
            log_to_file=False,
            log_to_console=True
        )

        assert test_logger.level == logging.DEBUG

    def test_setup_logger_file_handler(self, temp_dir):
        """Verifica creazione handler per file."""
        # Mock get_data_dir per usare temp_dir
        with patch('src.logger.get_data_dir', return_value=str(temp_dir)):
            test_logger = logger_module.setup_logger(
                name="test_file",
                log_to_file=True,
                log_to_console=False
            )

            # Verifica che abbia almeno un handler
            assert len(test_logger.handlers) > 0

            # Verifica che ci sia un RotatingFileHandler
            from logging.handlers import RotatingFileHandler
            file_handlers = [h for h in test_logger.handlers if isinstance(h, RotatingFileHandler)]
            assert len(file_handlers) > 0

            # Verifica che il file log esista
            log_file = os.path.join(temp_dir, "manga_reader.log")
            # Scrivi qualcosa per creare il file
            test_logger.info("Test message")
            assert os.path.exists(log_file)

    def test_setup_logger_console_handler(self):
        """Verifica creazione handler per console."""
        test_logger = logger_module.setup_logger(
            name="test_console",
            log_to_file=False,
            log_to_console=True
        )

        # Verifica che abbia handler
        assert len(test_logger.handlers) > 0

        # Verifica che ci sia uno StreamHandler
        stream_handlers = [h for h in test_logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) > 0

    def test_setup_logger_no_duplicate_handlers(self):
        """Verifica che non vengano aggiunti handler duplicati."""
        name = "test_no_dup"

        # Setup iniziale
        logger1 = logger_module.setup_logger(name, log_to_file=False)
        handler_count_1 = len(logger1.handlers)

        # Setup di nuovo lo stesso logger
        logger2 = logger_module.setup_logger(name, log_to_file=False)
        handler_count_2 = len(logger2.handlers)

        # Il numero di handler dovrebbe rimanere uguale
        assert logger1 is logger2
        assert handler_count_1 == handler_count_2

    def test_setup_logger_both_handlers(self, temp_dir):
        """Verifica setup con entrambi file e console handler."""
        with patch('src.logger.get_data_dir', return_value=str(temp_dir)):
            test_logger = logger_module.setup_logger(
                name="test_both",
                log_to_file=True,
                log_to_console=True
            )

            # Dovrebbe avere almeno 2 handler
            assert len(test_logger.handlers) >= 2

    def test_setup_logger_file_error_handling(self):
        """Verifica gestione errore creazione file log."""
        # Mock get_data_dir per restituire path invalido
        with patch('src.logger.get_data_dir', side_effect=Exception("Mock error")):
            # Non dovrebbe sollevare eccezione, ma stampare errore
            test_logger = logger_module.setup_logger(
                name="test_error",
                log_to_file=True,
                log_to_console=False
            )

            # Logger dovrebbe essere creato, ma senza file handler
            assert isinstance(test_logger, logging.Logger)

    def test_setup_logger_formatter(self):
        """Verifica che i formatter siano configurati correttamente."""
        test_logger = logger_module.setup_logger(
            name="test_formatter",
            log_to_file=False,
            log_to_console=True
        )

        for handler in test_logger.handlers:
            assert handler.formatter is not None
            # Verifica formato contiene elementi essenziali
            format_str = handler.formatter._fmt
            # Console formatter è più compatto
            assert "%(levelname)s" in format_str
            assert "%(message)s" in format_str


class TestGetLogger:
    """Test per la funzione get_logger()."""

    def test_get_logger_with_name(self):
        """Verifica ottenimento logger con nome specifico."""
        test_logger = logger_module.get_logger("test_get_name")

        assert isinstance(test_logger, logging.Logger)
        assert "test_get_name" in test_logger.name

    def test_get_logger_without_name(self):
        """Verifica ottenimento logger senza nome (usa nome modulo)."""
        test_logger = logger_module.get_logger()

        assert isinstance(test_logger, logging.Logger)
        # Il nome dovrebbe essere il nome del modulo chiamante o "MangaReader"
        assert isinstance(test_logger.name, str)
        assert len(test_logger.name) > 0

    def test_get_logger_returns_same_instance(self):
        """Verifica che chiamate multiple restituiscano stesso logger."""
        logger1 = logger_module.get_logger("test_same")
        logger2 = logger_module.get_logger("test_same")

        assert logger1 is logger2

    def test_get_logger_auto_configures(self):
        """Verifica che get_logger configuri automaticamente se necessario."""
        # Usa nome univoco per essere sicuri che non esista già
        import uuid
        unique_name = f"test_auto_{uuid.uuid4().hex[:8]}"

        test_logger = logger_module.get_logger(unique_name)

        # Dovrebbe essere configurato con handler
        assert len(test_logger.handlers) > 0

    def test_get_logger_with_existing_logger(self):
        """Verifica comportamento con logger già esistente."""
        # Setup logger manualmente
        name = "test_existing"
        existing = logger_module.setup_logger(name, log_to_file=False)
        handler_count = len(existing.handlers)

        # Ottieni lo stesso logger
        retrieved = logger_module.get_logger(name)

        # Dovrebbe essere lo stesso, senza handler duplicati
        assert retrieved is existing
        assert len(retrieved.handlers) == handler_count


class TestLogging:
    """Test funzionalità di logging."""

    def test_log_levels(self, temp_dir):
        """Verifica che tutti i livelli di log funzionino."""
        with patch('src.logger.get_data_dir', return_value=str(temp_dir)):
            test_logger = logger_module.setup_logger(
                name="test_levels",
                level=logging.DEBUG,
                log_to_file=True,
                log_to_console=False
            )

            # Test tutti i livelli
            test_logger.debug("Debug message")
            test_logger.info("Info message")
            test_logger.warning("Warning message")
            test_logger.error("Error message")
            test_logger.critical("Critical message")

            # Verifica che il file esista e contenga messaggi
            log_file = os.path.join(temp_dir, "manga_reader.log")
            assert os.path.exists(log_file)

            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "Debug message" in content
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content
            assert "Critical message" in content

    def test_log_format(self, temp_dir):
        """Verifica formato dei messaggi di log."""
        with patch('src.logger.get_data_dir', return_value=str(temp_dir)):
            test_logger = logger_module.setup_logger(
                name="test_format",
                log_to_file=True,
                log_to_console=False
            )

            test_logger.info("Test format message")

            log_file = os.path.join(temp_dir, "manga_reader.log")
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Verifica che il formato includa elementi essenziali
            assert "INFO" in content
            assert "Test format message" in content
            # Dovrebbe avere timestamp (formato YYYY-MM-DD)
            import re
            assert re.search(r'\d{4}-\d{2}-\d{2}', content)

    def test_rotating_file_handler_config(self, temp_dir):
        """Verifica configurazione RotatingFileHandler."""
        with patch('src.logger.get_data_dir', return_value=str(temp_dir)):
            test_logger = logger_module.setup_logger(
                name="test_rotating",
                log_to_file=True,
                log_to_console=False
            )

            from logging.handlers import RotatingFileHandler
            file_handler = None
            for handler in test_logger.handlers:
                if isinstance(handler, RotatingFileHandler):
                    file_handler = handler
                    break

            assert file_handler is not None

            # Verifica configurazione rotazione
            assert file_handler.maxBytes == 10 * 1024 * 1024  # 10MB
            assert file_handler.backupCount == 5

    def test_unicode_logging(self, temp_dir):
        """Verifica gestione caratteri Unicode nei log."""
        with patch('src.logger.get_data_dir', return_value=str(temp_dir)):
            test_logger = logger_module.setup_logger(
                name="test_unicode",
                log_to_file=True,
                log_to_console=False
            )

            # Testa vari caratteri Unicode
            test_logger.info("Test con caratteri speciali: àèéìòù ñ ü ö")
            test_logger.info("Test emoji: manga reader")
            test_logger.info("Test giapponese: 漫画")

            log_file = os.path.join(temp_dir, "manga_reader.log")
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Verifica che i caratteri siano salvati correttamente
            assert "àèéìòù" in content
            assert "漫画" in content


class TestMainLogger:
    """Test per il logger principale dell'applicazione."""

    def test_main_logger_exists(self):
        """Verifica che il logger principale sia inizializzato."""
        assert hasattr(logger_module, 'main_logger')
        assert isinstance(logger_module.main_logger, logging.Logger)

    def test_main_logger_configured(self):
        """Verifica che il logger principale sia configurato."""
        # Dovrebbe avere handler configurati
        assert len(logger_module.main_logger.handlers) > 0

    def test_main_logger_level(self):
        """Verifica livello del logger principale."""
        assert logger_module.main_logger.level == logging.INFO


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
