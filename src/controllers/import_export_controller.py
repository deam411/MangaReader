"""
ImportExportController - Business logic per import/export manga.

Responsabilità:
- Import file .manga nella libreria
- Import archivi CBZ/CBR e conversione in .manga
- Export manga selezionati
"""

import os
import shutil
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog, QApplication

from src.paths import get_manga_dir
from src.importers import ArchiveImporter
from src.logger import get_logger
from src.views.dialogs import ArchiveImportDialog
from src.views.utils import sanitize_filename

logger = get_logger(__name__)


class ImportExportController:
    """Controller per import/export manga."""

    def __init__(self, view):
        """
        Inizializza il controller per import/export.

        Args:
            view: L'istanza di LibraryView da controllare
        """
        self.view = view

    def import_manga(self):
        """Import a .manga file into the library."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Import .manga file",
            "",
            "Manga Files (*.manga);;All Files (*)"
        )

        if not file_path:
            return

        try:
            manga_dir = get_manga_dir()
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(manga_dir, file_name)

            # Check if file already exists
            if os.path.exists(dest_path):
                reply = QMessageBox.question(
                    self.view,
                    'File exists',
                    f'A file named "{file_name}" already exists. Do you want to overwrite it?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            # Copy the file
            shutil.copy2(file_path, dest_path)

            QMessageBox.information(self.view, 'Success', f'Successfully imported {file_name}')
            self.view.load_library()

        except Exception as e:
            QMessageBox.critical(self.view, 'Error', f'Failed to import manga: {str(e)}')

    def import_archive(self):
        """Import archivio CBZ/CBR e convertilo in formato .manga."""
        # Verifica formati supportati
        importer = ArchiveImporter()
        supported_formats = importer.get_supported_formats()
        formats_str = ' '.join([f'*{ext}' for ext in supported_formats])

        # File dialog per selezionare archivio
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Import Archivio CBZ/CBR",
            "",
            f"Comic Archives ({formats_str});;All Files (*)"
        )

        if not file_path:
            return

        # Mostra dialog per metadata
        dialog = ArchiveImportDialog(file_path, self.view)
        if dialog.exec_() != QDialog.Accepted:
            return

        metadata = dialog.get_metadata()

        # Mostra progress bar
        self.view.progress_bar.setVisible(True)
        self.view.progress_bar.setRange(0, 0)  # Indeterminate progress
        QApplication.processEvents()

        try:
            # Determina percorso output
            manga_dir = get_manga_dir()
            output_name = metadata['title'] or os.path.splitext(os.path.basename(file_path))[0]
            # Sanitizza il nome file
            output_name = sanitize_filename(output_name)
            output_path = os.path.join(manga_dir, f"{output_name}.manga")

            # Controlla se esiste già
            if os.path.exists(output_path):
                reply = QMessageBox.question(
                    self.view,
                    'File exists',
                    f'Un file "{output_name}.manga" esiste già. Vuoi sovrascriverlo?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    self.view.progress_bar.setVisible(False)
                    return

            # Esegui import
            success = importer.import_archive(
                archive_path=file_path,
                output_path=output_path,
                title=metadata['title'],
                author=metadata['author'],
                volume_name=metadata['volume_name'],
                chapter_name=metadata['chapter_name']
            )

            self.view.progress_bar.setVisible(False)

            if success:
                QMessageBox.information(
                    self.view,
                    'Import completato',
                    f'Archivio importato con successo come "{output_name}.manga"'
                )
                self.view.load_library()
            else:
                QMessageBox.critical(
                    self.view,
                    'Errore Import',
                    'Errore durante l\'importazione dell\'archivio. Verifica il file e riprova.'
                )

        except Exception as e:
            self.view.progress_bar.setVisible(False)
            QMessageBox.critical(
                self.view,
                'Errore',
                f'Errore durante l\'import: {str(e)}'
            )

    def export_manga(self):
        """Export the selected .manga file to a chosen location."""
        current_item = self.view.manga_grid_view.currentItem()

        if not current_item:
            QMessageBox.warning(self.view, 'No selection', 'Please select a manga to export.')
            return

        manga_file = current_item.data(Qt.UserRole)

        if not manga_file or not os.path.exists(manga_file):
            QMessageBox.warning(self.view, 'Error', 'Selected manga file not found.')
            return

        try:
            file_name = os.path.basename(manga_file)
            save_path, _ = QFileDialog.getSaveFileName(
                self.view,
                "Export .manga file",
                file_name,
                "Manga Files (*.manga);;All Files (*)"
            )

            if not save_path:
                return

            # Copy the file
            shutil.copy2(manga_file, save_path)

            QMessageBox.information(self.view, 'Success', f'Successfully exported to {save_path}')

        except Exception as e:
            QMessageBox.critical(self.view, 'Error', f'Failed to export manga: {str(e)}')
