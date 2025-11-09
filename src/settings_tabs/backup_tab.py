"""
Tab Backup per Settings Dialog (v0.3.0).
"""

import os
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QListWidget, QFileDialog, QMessageBox,
                              QProgressDialog, QGroupBox)
from PyQt5.QtCore import Qt
from ..backup import BackupManager
from ..paths import get_manga_dir, get_data_dir
from ..logger import get_logger

logger = get_logger(__name__)


class BackupTab(QWidget):
    """Tab per gestire backup e restore della libreria."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.backup_dir = os.path.join(get_data_dir(), "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

        self.backup_manager = BackupManager(get_manga_dir())
        self._setup_ui()
        self._refresh_backup_list()

    def _setup_ui(self):
        """Configura l'interfaccia del tab."""
        layout = QVBoxLayout(self)

        # Info section
        info_label = QLabel(
            "Backup della libreria manga\n\n"
            "Crea backup completi della tua libreria per proteggere i tuoi dati.\n"
            "I backup vengono salvati in formato .zip."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Backup actions
        backup_group = QGroupBox("Crea Backup")
        backup_layout = QVBoxLayout(backup_group)

        backup_buttons = QHBoxLayout()
        self.backup_button = QPushButton("Crea Backup Completo")
        self.backup_button.clicked.connect(self._create_backup)
        backup_buttons.addWidget(self.backup_button)

        self.backup_custom_button = QPushButton("Salva Come...")
        self.backup_custom_button.clicked.connect(self._create_backup_custom)
        backup_buttons.addWidget(self.backup_custom_button)

        backup_layout.addLayout(backup_buttons)
        layout.addWidget(backup_group)

        # Restore section
        restore_group = QGroupBox("Backup Disponibili")
        restore_layout = QVBoxLayout(restore_group)

        # Lista backup
        self.backup_list = QListWidget()
        self.backup_list.itemDoubleClicked.connect(self._restore_backup)
        restore_layout.addWidget(self.backup_list)

        # Restore buttons
        restore_buttons = QHBoxLayout()
        self.restore_button = QPushButton("Ripristina Selezionato")
        self.restore_button.clicked.connect(self._restore_backup)
        self.restore_button.setEnabled(False)
        restore_buttons.addWidget(self.restore_button)

        self.delete_backup_button = QPushButton("Elimina")
        self.delete_backup_button.clicked.connect(self._delete_backup)
        self.delete_backup_button.setEnabled(False)
        restore_buttons.addWidget(self.delete_backup_button)

        self.refresh_button = QPushButton("Aggiorna")
        self.refresh_button.clicked.connect(self._refresh_backup_list)
        restore_buttons.addWidget(self.refresh_button)

        restore_layout.addLayout(restore_buttons)
        layout.addWidget(restore_group)

        # Collega segnale selezione
        self.backup_list.itemSelectionChanged.connect(self._on_selection_changed)

        layout.addStretch()

    def _on_selection_changed(self):
        """Attiva/disattiva pulsanti basati sulla selezione."""
        has_selection = len(self.backup_list.selectedItems()) > 0
        self.restore_button.setEnabled(has_selection)
        self.delete_backup_button.setEnabled(has_selection)

    def _create_backup(self):
        """Crea un backup con nome automatico."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}.zip")

        progress = QProgressDialog("Creazione backup in corso...", "Annulla", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.show()

        success = self.backup_manager.create_backup(backup_path)

        progress.close()

        if success:
            QMessageBox.information(self, "Backup Creato",
                                   f"Backup creato con successo!\n\n{backup_path}")
            self._refresh_backup_list()
        else:
            QMessageBox.critical(self, "Errore", "Errore durante la creazione del backup.")

    def _create_backup_custom(self):
        """Crea un backup in posizione personalizzata."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salva Backup", "", "Backup Files (*.zip)"
        )

        if not file_path:
            return

        if not file_path.endswith('.zip'):
            file_path += '.zip'

        progress = QProgressDialog("Creazione backup in corso...", "Annulla", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.show()

        success = self.backup_manager.create_backup(file_path)

        progress.close()

        if success:
            QMessageBox.information(self, "Backup Creato", "Backup creato con successo!")
            self._refresh_backup_list()
        else:
            QMessageBox.critical(self, "Errore", "Errore durante la creazione del backup.")

    def _restore_backup(self):
        """Ripristina un backup selezionato."""
        selected = self.backup_list.currentItem()
        if not selected:
            return

        backup_name = selected.text().split(" - ")[0]  # Estrai nome senza size/date
        backup_path = os.path.join(self.backup_dir, backup_name)

        reply = QMessageBox.question(
            self, "Conferma Ripristino",
            "Ripristinare questo backup?\n\n"
            "ATTENZIONE: Questo sovrascriverà la libreria corrente!",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        progress = QProgressDialog("Ripristino in corso...", "Annulla", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.show()

        success = self.backup_manager.restore_backup(backup_path)

        progress.close()

        if success:
            QMessageBox.information(self, "Ripristino Completato",
                                   "Backup ripristinato con successo!\n\n"
                                   "Riavvia l'applicazione per vedere i cambiamenti.")
        else:
            QMessageBox.critical(self, "Errore", "Errore durante il ripristino del backup.")

    def _delete_backup(self):
        """Elimina un backup selezionato."""
        selected = self.backup_list.currentItem()
        if not selected:
            return

        backup_name = selected.text().split(" - ")[0]
        backup_path = os.path.join(self.backup_dir, backup_name)

        reply = QMessageBox.question(
            self, "Conferma Eliminazione",
            f"Eliminare il backup '{backup_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                os.remove(backup_path)
                QMessageBox.information(self, "Eliminato", "Backup eliminato con successo!")
                self._refresh_backup_list()
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante l'eliminazione: {e}")
                logger.error(f"Errore eliminazione backup: {e}")

    def _refresh_backup_list(self):
        """Aggiorna la lista dei backup disponibili."""
        self.backup_list.clear()

        backups = self.backup_manager.list_backups(self.backup_dir)
        backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)  # Più recenti prima

        for backup_path in backups:
            backup_name = os.path.basename(backup_path)
            size_mb = os.path.getsize(backup_path) / (1024 * 1024)
            mtime = datetime.fromtimestamp(os.path.getmtime(backup_path))
            date_str = mtime.strftime("%Y-%m-%d %H:%M")

            display_text = f"{backup_name} - {size_mb:.1f} MB - {date_str}"
            self.backup_list.addItem(display_text)

        logger.debug(f"Trovati {len(backups)} backup")
