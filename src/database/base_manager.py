"""
Base manager class per gestione database.

Fornisce funzionalità comuni a tutti i manager specializzati.
"""
import sqlite3
from typing import Any, Optional
from contextlib import contextmanager
from ..logger import get_logger
from ..exceptions import DatabaseError, DatabaseConnectionError, DatabaseQueryError

logger = get_logger(__name__)


class BaseManager:
    """
    Classe base per tutti i database manager.

    Fornisce:
    - Gestione connessione database
    - Context manager per transazioni
    - Helper methods comuni
    - Error handling centralizzato
    """

    def __init__(self, db_path: str):
        """
        Inizializza il base manager.

        Args:
            db_path: Percorso al file database SQLite
        """
        self.db_path = db_path
        logger.debug(f"BaseManager: Initialized for {db_path}")

    @contextmanager
    def get_connection(self):
        """
        Context manager per connessioni database.

        Yields:
            sqlite3.Connection: Connessione al database

        Raises:
            DatabaseConnectionError: Se la connessione fallisce

        Example:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM metadata")
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Abilita accesso per nome colonna
            yield conn
            conn.commit()
        except sqlite3.OperationalError as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error for {self.db_path}: {e}")
            raise DatabaseConnectionError(
                f"Impossibile connettersi al database {self.db_path}"
            ) from e
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error for {self.db_path}: {e}")
            raise DatabaseError(
                f"Errore database per {self.db_path}"
            ) from e
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = (), fetch: str = None) -> Any:
        """
        Esegue una query SQL con gestione errori.

        Args:
            query: Query SQL da eseguire
            params: Parametri per la query (prepared statement)
            fetch: Tipo di fetch ('one', 'all', None per no fetch)

        Returns:
            Risultato della query in base al parametro fetch

        Raises:
            DatabaseQueryError: Se la query fallisce

        Example:
            result = self.execute_query(
                "SELECT * FROM metadata WHERE title = ?",
                (title,),
                fetch='one'
            )
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)

                if fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'all':
                    return cursor.fetchall()
                else:
                    return cursor.lastrowid

        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {query[:100]}... Error: {e}")
            raise DatabaseQueryError(
                f"Errore esecuzione query: {str(e)}"
            ) from e

    def table_exists(self, table_name: str) -> bool:
        """
        Verifica se una tabella esiste nel database.

        Args:
            table_name: Nome della tabella

        Returns:
            True se la tabella esiste, False altrimenti
        """
        query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """
        result = self.execute_query(query, (table_name,), fetch='one')
        return result is not None

    def column_exists(self, table_name: str, column_name: str) -> bool:
        """
        Verifica se una colonna esiste in una tabella.

        Args:
            table_name: Nome della tabella
            column_name: Nome della colonna

        Returns:
            True se la colonna esiste, False altrimenti
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                return column_name in columns
        except sqlite3.Error as e:
            logger.error(f"Error checking column existence: {e}")
            return False
