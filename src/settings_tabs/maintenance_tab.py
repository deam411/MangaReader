"""
Tab Manutenzione Database nelle impostazioni.

Permette di:
- Verificare integrità database manga
- Riparare manga senza dimensioni pagine salvate
- Altre operazioni di manutenzione
"""

import os
import sqlite3
from typing import List, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QProgressBar, QMessageBox,
    QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage

from src.paths import get_manga_dir
from src.logger import get_logger

logger = get_logger(__name__)


class RepairWorker(QThread):
    """Worker thread per riparare manga in background."""

    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(int, int)  # repaired_count, error_count

    def __init__(self, manga_files: List[str]):
        super().__init__()
        self.manga_files = manga_files
        self.should_stop = False

    def run(self):
        """Esegue la riparazione dei manga selezionati."""
        repaired = 0
        errors = 0
        total = len(self.manga_files)

        for idx, manga_file in enumerate(self.manga_files):
            if self.should_stop:
                break

            try:
                manga_name = os.path.basename(manga_file)
                self.progress.emit(idx, total, f"Riparando {manga_name}...")

                # Ripara il manga
                pages_updated = self._repair_manga(manga_file)

                if pages_updated > 0:
                    repaired += 1
                    logger.info(f"Repaired {manga_name}: {pages_updated} pages updated")

                # Emetti progresso dopo il completamento
                self.progress.emit(idx + 1, total, f" {manga_name} completato")

            except Exception as e:
                logger.error(f"Error repairing {manga_file}: {e}")
                errors += 1
                self.progress.emit(idx + 1, total, f" Errore: {manga_name}")

        self.finished.emit(repaired, errors)

    def _repair_manga(self, manga_file: str) -> int:
        """
        Ripara un manga aggiungendo dimensioni alle pagine che ne sono sprovviste.

        Args:
            manga_file: Percorso al file .manga

        Returns:
            Numero di pagine aggiornate
        """
        conn = sqlite3.connect(manga_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        pages_updated = 0

        try:
            # Assicura che le colonne width/height esistano
            self._ensure_dimensions_columns(cursor)

            # Trova tutte le pagine senza dimensioni
            cursor.execute('''
                SELECT chapter_id, page_number, image_data
                FROM pages
                WHERE width IS NULL OR height IS NULL
            ''')

            pages_to_fix = cursor.fetchall()

            for page in pages_to_fix:
                if self.should_stop:
                    break

                chapter_id = page['chapter_id']
                page_number = page['page_number']
                image_data = page['image_data']

                # Estrai dimensioni dall'immagine
                temp_image = QImage()
                if temp_image.loadFromData(image_data):
                    width = temp_image.width()
                    height = temp_image.height()

                    # Aggiorna il database
                    cursor.execute('''
                        UPDATE pages
                        SET width = ?, height = ?
                        WHERE chapter_id = ? AND page_number = ?
                    ''', (width, height, chapter_id, page_number))

                    pages_updated += 1

            conn.commit()

        finally:
            conn.close()

        return pages_updated

    def _ensure_dimensions_columns(self, cursor) -> None:
        """
        Assicura che le colonne width e height esistano nella tabella pages.
        Se non esistono, le aggiunge (migrazione v3).

        Args:
            cursor: Cursore del database
        """
        # Controlla se le colonne esistono
        cursor.execute("PRAGMA table_info(pages)")
        columns = [row[1] for row in cursor.fetchall()]

        needs_width = 'width' not in columns
        needs_height = 'height' not in columns

        if needs_width:
            cursor.execute("ALTER TABLE pages ADD COLUMN width INTEGER")
            logger.info("Added 'width' column to pages table")

        if needs_height:
            cursor.execute("ALTER TABLE pages ADD COLUMN height INTEGER")
            logger.info("Added 'height' column to pages table")

    def stop(self):
        """Ferma il worker."""
        self.should_stop = True


class MaintenanceTab(QWidget):
    """Tab per manutenzione database manga."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manga_to_repair: List[str] = []
        self.repair_worker = None
        self.initUI()

    def initUI(self):
        """Inizializza l'interfaccia utente."""
        layout = QVBoxLayout(self)

        # Titolo
        title = QLabel("Manutenzione Database")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Sezione riparazione dimensioni pagine
        repair_group = QGroupBox("Riparazione Dimensioni Pagine")
        repair_layout = QVBoxLayout(repair_group)

        # Info
        info_label = QLabel(
            "Alcuni manga potrebbero non avere le dimensioni delle pagine salvate.\n"
            "Questo causa spacing variabile nel reader. Usa questa funzione per ripararli."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; margin-bottom: 10px;")
        repair_layout.addWidget(info_label)

        # Pulsante scansione
        scan_layout = QHBoxLayout()
        self.scan_button = QPushButton("🔍 Scansiona Manga")
        self.scan_button.setToolTip("Cerca manga che necessitano riparazione")
        self.scan_button.clicked.connect(self.scan_manga)
        scan_layout.addWidget(self.scan_button)
        scan_layout.addStretch()
        repair_layout.addLayout(scan_layout)

        # Lista manga da riparare
        self.manga_list = QListWidget()
        self.manga_list.setSelectionMode(QListWidget.MultiSelection)
        self.manga_list.setMaximumHeight(200)
        repair_layout.addWidget(self.manga_list)

        # Pulsanti azione
        action_layout = QHBoxLayout()

        self.select_all_button = QPushButton("Seleziona Tutti")
        self.select_all_button.clicked.connect(self.select_all)
        self.select_all_button.setEnabled(False)
        action_layout.addWidget(self.select_all_button)

        self.deselect_all_button = QPushButton("Deseleziona Tutti")
        self.deselect_all_button.clicked.connect(self.deselect_all)
        self.deselect_all_button.setEnabled(False)
        action_layout.addWidget(self.deselect_all_button)

        action_layout.addStretch()

        self.repair_button = QPushButton("🔧 Ripara Selezionati")
        self.repair_button.setToolTip("Ripara i manga selezionati aggiungendo le dimensioni delle pagine")
        self.repair_button.clicked.connect(self.repair_selected)
        self.repair_button.setEnabled(False)
        action_layout.addWidget(self.repair_button)

        repair_layout.addLayout(action_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        repair_layout.addWidget(self.progress_bar)

        # Label status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #4a9eff; margin-top: 5px;")
        repair_layout.addWidget(self.status_label)

        layout.addWidget(repair_group)

        layout.addStretch()

    def scan_manga(self):
        """Scansiona tutti i manga per trovare quelli da riparare."""
        self.scan_button.setEnabled(False)
        self.status_label.setText("Scansione in corso...")
        self.manga_list.clear()
        self.manga_to_repair.clear()

        try:
            manga_dir = get_manga_dir()
            manga_files = [
                os.path.join(manga_dir, f)
                for f in os.listdir(manga_dir)
                if f.endswith('.manga')
            ]

            total = len(manga_files)
            needs_repair = []

            for idx, manga_file in enumerate(manga_files):
                # Aggiorna status
                self.status_label.setText(f"Scansione... {idx + 1}/{total}")

                # Controlla se necessita riparazione
                if self._needs_repair(manga_file):
                    manga_name = os.path.basename(manga_file)
                    needs_repair.append((manga_name, manga_file))

            # Popola lista
            if needs_repair:
                for manga_name, manga_file in needs_repair:
                    item = QListWidgetItem(manga_name)
                    item.setData(Qt.UserRole, manga_file)
                    self.manga_list.addItem(item)
                    self.manga_to_repair.append(manga_file)

                self.status_label.setText(
                    f" Trovati {len(needs_repair)} manga da riparare"
                )
                self.status_label.setStyleSheet("color: #4a9eff;")
                self.select_all_button.setEnabled(True)
                self.deselect_all_button.setEnabled(True)
                self.repair_button.setEnabled(True)
            else:
                self.status_label.setText(" Nessun manga necessita riparazione")
                self.status_label.setStyleSheet("color: green;")

        except Exception as e:
            logger.error(f"Error scanning manga: {e}")
            self.status_label.setText(f" Errore durante scansione: {str(e)}")
            self.status_label.setStyleSheet("color: red;")

        finally:
            self.scan_button.setEnabled(True)

    def _needs_repair(self, manga_file: str) -> bool:
        """
        Controlla se un manga necessita riparazione.

        Args:
            manga_file: Percorso al file .manga

        Returns:
            True se il manga ha pagine senza dimensioni o le colonne non esistono
        """
        try:
            conn = sqlite3.connect(manga_file)
            cursor = conn.cursor()

            # Controlla se le colonne width/height esistono
            cursor.execute("PRAGMA table_info(pages)")
            columns = [row[1] for row in cursor.fetchall()]

            has_width = 'width' in columns
            has_height = 'height' in columns

            # Se le colonne non esistono, il manga necessita riparazione
            if not has_width or not has_height:
                logger.debug(f"{os.path.basename(manga_file)}: Missing columns (width={has_width}, height={has_height})")
                conn.close()
                return True

            # Conta tutte le pagine
            cursor.execute('SELECT COUNT(*) FROM pages')
            total_pages = cursor.fetchone()[0]

            # Controlla se esistono pagine senza width/height
            cursor.execute('''
                SELECT COUNT(*) FROM pages
                WHERE width IS NULL OR height IS NULL
            ''')

            count = cursor.fetchone()[0]
            conn.close()

            if count > 0:
                logger.debug(f"{os.path.basename(manga_file)}: {count}/{total_pages} pages need dimensions")
            else:
                logger.debug(f"{os.path.basename(manga_file)}: OK ({total_pages} pages with dimensions)")

            return count > 0

        except Exception as e:
            logger.error(f"Error checking {manga_file}: {e}")
            return False

    def select_all(self):
        """Seleziona tutti i manga."""
        for i in range(self.manga_list.count()):
            self.manga_list.item(i).setSelected(True)

    def deselect_all(self):
        """Deseleziona tutti i manga."""
        self.manga_list.clearSelection()

    def repair_selected(self):
        """Ripara i manga selezionati."""
        selected_items = self.manga_list.selectedItems()

        if not selected_items:
            QMessageBox.warning(
                self,
                "Nessuna Selezione",
                "Seleziona almeno un manga da riparare."
            )
            return

        # Conferma
        reply = QMessageBox.question(
            self,
            "Conferma Riparazione",
            f"Riparare {len(selected_items)} manga?\n\n"
            "Questa operazione potrebbe richiedere alcuni minuti.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Ottieni file paths
        manga_files = [item.data(Qt.UserRole) for item in selected_items]

        # Disabilita controlli
        self.scan_button.setEnabled(False)
        self.repair_button.setEnabled(False)
        self.select_all_button.setEnabled(False)
        self.deselect_all_button.setEnabled(False)

        # Mostra progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(manga_files))
        self.progress_bar.setValue(0)

        # Avvia worker
        self.repair_worker = RepairWorker(manga_files)
        self.repair_worker.progress.connect(self.on_repair_progress)
        self.repair_worker.finished.connect(self.on_repair_finished)
        self.repair_worker.start()

    def on_repair_progress(self, current: int, total: int, message: str):
        """Aggiorna progresso riparazione."""
        self.progress_bar.setValue(current)
        self.status_label.setText(message)

    def on_repair_finished(self, repaired: int, errors: int):
        """Chiamato quando la riparazione è completata."""
        self.progress_bar.setVisible(False)

        if errors > 0:
            self.status_label.setText(
                f" Riparati {repaired} manga, {errors} errori"
            )
            self.status_label.setStyleSheet("color: orange;")
            QMessageBox.warning(
                self,
                "Riparazione Completata con Errori",
                f"Riparati: {repaired}\nErrori: {errors}\n\n"
                "Controlla i log per dettagli."
            )
        else:
            self.status_label.setText(f" Riparati {repaired} manga con successo!")
            self.status_label.setStyleSheet("color: green;")
            QMessageBox.information(
                self,
                "Riparazione Completata",
                f"Tutti i {repaired} manga sono stati riparati con successo!"
            )

        # Riabilita controlli
        self.scan_button.setEnabled(True)

        # Rimuovi manga riparati dalla lista
        for item in self.manga_list.selectedItems():
            row = self.manga_list.row(item)
            self.manga_list.takeItem(row)

        # Riabilita pulsanti se ci sono ancora manga
        if self.manga_list.count() > 0:
            self.select_all_button.setEnabled(True)
            self.deselect_all_button.setEnabled(True)
            self.repair_button.setEnabled(True)

    def get_values(self) -> dict:
        """Restituisce configurazione (nessuna configurazione persistente)."""
        return {}

    def set_values(self, values: dict):
        """Imposta configurazione (non applicabile)."""
        pass
