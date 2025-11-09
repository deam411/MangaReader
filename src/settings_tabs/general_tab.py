"""
Tab impostazioni generali: libreria e aggiornamenti.
"""
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFileDialog, QGroupBox,
                              QMessageBox, QProgressDialog, QTextEdit, QApplication)
from PyQt5.QtCore import QThread, pyqtSignal
from ..settings import Settings
from ..updater import (check_for_updates, download_update, install_update,
                       get_current_version, get_update_info_text)
from ..logger import get_logger

logger = get_logger(__name__)


class UpdateThread(QThread):
    """Thread per controllare gli aggiornamenti senza bloccare la UI."""
    update_found = pyqtSignal(dict)  # Emette info sull'aggiornamento
    no_update = pyqtSignal()
    error = pyqtSignal(str)

    def run(self):
        try:
            update_info = check_for_updates()
            if update_info:
                self.update_found.emit(update_info)
            else:
                self.no_update.emit()
        except Exception as e:
            self.error.emit(str(e))


class GeneralTab(QWidget):
    """Tab per impostazioni generali (libreria + aggiornamenti)."""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.parent_dialog = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Gruppo Libreria
        library_group = QGroupBox("Libreria Manga")
        library_layout = QVBoxLayout()

        # Path della libreria
        path_layout = QHBoxLayout()
        path_label = QLabel("Percorso libreria:")
        path_layout.addWidget(path_label)

        self.library_path_input = QLineEdit()
        # Se il percorso è None, mostra il default tra parentesi
        current_path = self.settings.get_library_path()
        if current_path:
            self.library_path_input.setText(current_path)
        else:
            # Mostra il percorso di default calcolato
            from ..paths import get_project_root
            default_path = os.path.join(get_project_root(), "manga")
            self.library_path_input.setText(f"{default_path} (default)")
            self.library_path_input.setPlaceholderText("Percorso di default")
        self.library_path_input.setReadOnly(True)
        path_layout.addWidget(self.library_path_input)

        browse_button = QPushButton("Sfoglia...")
        browse_button.clicked.connect(self.browse_library_path)
        path_layout.addWidget(browse_button)

        library_layout.addLayout(path_layout)

        # Info label
        info_label = QLabel("La libreria contiene tutti i file .manga.\n"
                            "Puoi cambiare la posizione per non appesantire l'eseguibile.")
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        info_label.setWordWrap(True)
        library_layout.addWidget(info_label)

        library_group.setLayout(library_layout)
        layout.addWidget(library_group)

        # Gruppo Aggiornamenti (v0.1.0)
        update_group = QGroupBox("Aggiornamenti")
        update_layout = QVBoxLayout()

        # Versione corrente
        version_label = QLabel(f"Versione corrente: v{get_current_version()}")
        version_label.setStyleSheet("font-weight: bold;")
        update_layout.addWidget(version_label)

        # Pulsante controlla aggiornamenti
        check_update_btn = QPushButton("Controlla aggiornamenti")
        check_update_btn.clicked.connect(self.check_for_updates)
        check_update_btn.setToolTip("Controlla su GitHub se è disponibile una nuova versione")
        update_layout.addWidget(check_update_btn)

        # Info label
        update_info = QLabel("Controlla automaticamente su GitHub se ci sono nuove versioni disponibili.")
        update_info.setStyleSheet("color: gray; font-size: 10px;")
        update_info.setWordWrap(True)
        update_layout.addWidget(update_info)

        update_group.setLayout(update_layout)
        layout.addWidget(update_group)

        layout.addStretch()
        self.setLayout(layout)

    def browse_library_path(self):
        """Apre dialog per selezionare il percorso della libreria."""
        current_path = self.settings.get_library_path()
        if not current_path:
            from ..paths import get_project_root
            current_path = os.path.join(get_project_root(), "manga")

        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleziona Directory Libreria",
            current_path
        )

        if directory:
            self.library_path_input.setText(directory)

    def check_for_updates(self):
        """Controlla se ci sono aggiornamenti disponibili."""
        # Mostra dialog di attesa
        progress = QProgressDialog("Controllo aggiornamenti...", None, 0, 0, self)
        progress.setWindowTitle("Aggiornamenti")
        progress.setModal(True)
        progress.setCancelButton(None)
        progress.show()
        QApplication.processEvents()

        # Crea e avvia thread
        self.update_thread = UpdateThread()
        self.update_thread.update_found.connect(lambda info: self._on_update_found(info, progress))
        self.update_thread.no_update.connect(lambda: self._on_no_update(progress))
        self.update_thread.error.connect(lambda err: self._on_update_error(err, progress))
        self.update_thread.start()

    def _on_update_found(self, update_info, progress_dialog):
        """Gestisce quando viene trovato un aggiornamento."""
        progress_dialog.close()

        # Mostra dialog con info aggiornamento
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Aggiornamento Disponibile")
        dialog.setIcon(QMessageBox.Information)

        # Crea il messaggio
        message = get_update_info_text(update_info)
        dialog.setText("È disponibile una nuova versione!")
        dialog.setInformativeText(message)

        # Pulsanti
        dialog.addButton("Installa", QMessageBox.AcceptRole)
        dialog.addButton("Più tardi", QMessageBox.RejectRole)

        # Mostra dialog
        result = dialog.exec_()

        if result == QMessageBox.AcceptRole:
            self._download_and_install_update(update_info)

    def _on_no_update(self, progress_dialog):
        """Gestisce quando non ci sono aggiornamenti."""
        progress_dialog.close()
        QMessageBox.information(
            self,
            "Nessun Aggiornamento",
            f"Stai già usando l'ultima versione (v{get_current_version()})."
        )

    def _on_update_error(self, error, progress_dialog):
        """Gestisce errori durante il controllo aggiornamenti."""
        progress_dialog.close()
        QMessageBox.warning(
            self,
            "Errore",
            f"Impossibile controllare gli aggiornamenti:\n{error}"
        )

    def _download_and_install_update(self, update_info):
        """Scarica e installa l'aggiornamento."""
        # Progress dialog per download
        progress = QProgressDialog("Download aggiornamento...", "Annulla", 0, 100, self)
        progress.setWindowTitle("Download")
        progress.setModal(True)
        progress.show()

        # Callback per aggiornare la progress bar
        def update_progress(downloaded, total):
            if total > 0:
                percent = int((downloaded / total) * 100)
                progress.setValue(percent)
                QApplication.processEvents()
                # Controlla se l'utente ha annullato
                if progress.wasCanceled():
                    raise Exception("Download annullato dall'utente")

        try:
            # Download con callback per progress
            update_file = download_update(update_info, update_progress)

            if not update_file:
                progress.close()
                QMessageBox.warning(
                    self,
                    "Errore",
                    "Download fallito.\n\nControlla i log per maggiori dettagli:\n"
                    "AppData/Local/MangaReader/manga_reader.log"
                )
                return

            progress.setLabelText("Installazione in corso...")
            progress.setCancelButton(None)
            QApplication.processEvents()

            # Installa
            if install_update(update_file):
                progress.close()
                QMessageBox.information(
                    self,
                    "Aggiornamento Completato",
                    "L'applicazione si chiuderà per completare l'aggiornamento.\n"
                    "Rilancia MangaReader per usare la nuova versione."
                )
                # Chiudi l'applicazione
                QApplication.quit()
            else:
                progress.close()
                QMessageBox.warning(
                    self,
                    "Errore",
                    "Installazione fallita. Riprova più tardi."
                )

        except Exception as e:
            progress.close()
            error_msg = str(e)
            if "annullato dall'utente" in error_msg.lower():
                QMessageBox.information(
                    self,
                    "Download annullato",
                    "Download annullato dall'utente."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Errore",
                    f"Errore durante l'aggiornamento:\n{error_msg}\n\n"
                    "Controlla i log per maggiori dettagli:\n"
                    "AppData/Local/MangaReader/manga_reader.log"
                )

    def get_values(self):
        """Ritorna i valori correnti del tab."""
        library_path = self.library_path_input.text()
        # Rimuovi "(default)" se presente
        if "(default)" in library_path:
            library_path = library_path.replace(" (default)", "").strip()

        return {
            "library_path": library_path  # Fix: usa underscore invece di punto
        }
