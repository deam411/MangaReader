"""
Dialog per gestire le impostazioni dell'applicazione.

Architettura v0.2.0: Modular tab-based design
- Container principale che gestisce QTabWidget
- Ogni tab è un widget separato in settings_tabs/
- Raccoglie valori da tutti i tab tramite get_values()
"""
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                              QPushButton, QMessageBox, QTabWidget, QFileDialog)
from PyQt5.QtCore import pyqtSignal
from .settings import Settings
from .settings_tabs import (GeneralTab, AppearanceTab, PerformanceTab,
                            ReaderTab, ShortcutsTab, BookmarksTab)
from .logger import get_logger

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """
    Dialog per modificare le impostazioni dell'applicazione.

    Container che organizza le impostazioni in tab separati.
    Ogni tab è responsabile della propria UI e business logic.
    """

    settings_changed = pyqtSignal()  # Segnale emesso quando le settings cambiano

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = Settings()
        self.setWindowTitle("Impostazioni")
        self.setMinimumSize(600, 500)

        # Referenze ai tab (per raccogliere valori in accept())
        self.general_tab = None
        self.appearance_tab = None
        self.performance_tab = None
        self.reader_tab = None
        self.shortcuts_tab = None
        self.bookmarks_tab = None

        self.initUI()

    def initUI(self):
        """Inizializza l'interfaccia utente del dialog."""
        layout = QVBoxLayout()

        # Tab widget per organizzare le impostazioni
        tabs = QTabWidget()

        # Crea e aggiungi tutti i tab
        self.general_tab = GeneralTab(self.settings, self)
        tabs.addTab(self.general_tab, "Generale")

        self.appearance_tab = AppearanceTab(self.settings, self)
        tabs.addTab(self.appearance_tab, "Aspetto")

        self.performance_tab = PerformanceTab(self.settings, self)
        tabs.addTab(self.performance_tab, "Performance")

        self.reader_tab = ReaderTab(self.settings, self)
        tabs.addTab(self.reader_tab, "Reader")

        self.shortcuts_tab = ShortcutsTab(self.settings, self)
        tabs.addTab(self.shortcuts_tab, "Scorciatoie")

        self.bookmarks_tab = BookmarksTab(self.settings, self)
        tabs.addTab(self.bookmarks_tab, "Segnalibri")

        layout.addWidget(tabs)

        # Connetti segnali dai tab
        self.appearance_tab.theme_changed.connect(self.settings_changed)

        # Pulsanti OK/Cancel/Reset + Export/Import
        buttons_layout = QHBoxLayout()

        reset_button = QPushButton("Ripristina Default")
        reset_button.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(reset_button)

        # Pulsanti Export/Import
        export_button = QPushButton("Esporta Configurazione")
        export_button.setToolTip("Salva tutte le impostazioni in un file")
        export_button.clicked.connect(self.export_settings)
        buttons_layout.addWidget(export_button)

        import_button = QPushButton("Importa Configurazione")
        import_button.setToolTip("Carica impostazioni da un file")
        import_button.clicked.connect(self.import_settings)
        buttons_layout.addWidget(import_button)

        buttons_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_button)

        cancel_button = QPushButton("Annulla")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def accept(self):
        """
        Salva le impostazioni quando l'utente clicca OK.

        Raccoglie i valori da tutti i tab tramite get_values()
        e li salva nelle settings.
        """
        # Raccogli valori da tutti i tab
        all_values = {}

        if self.general_tab:
            all_values.update(self.general_tab.get_values())

        if self.appearance_tab:
            all_values.update(self.appearance_tab.get_values())

        if self.performance_tab:
            all_values.update(self.performance_tab.get_values())

        if self.reader_tab:
            all_values.update(self.reader_tab.get_values())

        if self.shortcuts_tab:
            all_values.update(self.shortcuts_tab.get_values())

        if self.bookmarks_tab:
            all_values.update(self.bookmarks_tab.get_values())

        # Salva tutti i valori
        for key, value in all_values.items():
            # Gestione speciale per shortcuts (hanno prefisso "shortcuts.")
            if key.startswith("shortcuts."):
                action = key.replace("shortcuts.", "")
                self.settings.set_shortcut(action, value)
            else:
                self.settings.set(key, value)

        # Salva settings su disco
        self.settings.save()

        # Emetti segnale per notificare il cambio
        self.settings_changed.emit()

        logger.info("Settings saved successfully")
        super().accept()

    def reset_settings(self):
        """Ripristina le impostazioni ai valori di default."""
        reply = QMessageBox.question(
            self,
            "Ripristina impostazioni",
            "Sei sicuro di voler ripristinare tutte le impostazioni ai valori di default?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.settings.reset_to_default()
            self.settings_changed.emit()

            QMessageBox.information(
                self,
                "Impostazioni ripristinate",
                "Le impostazioni sono state ripristinate ai valori di default.\n"
                "Riavvia l'applicazione per applicare tutte le modifiche."
            )

            logger.info("Settings reset to default")

    def export_settings(self):
        """Esporta la configurazione corrente in un file JSON."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Esporta Configurazione",
                os.path.expanduser("~/manga_reader_config.json"),
                "File JSON (*.json)"
            )

            if file_path:
                # Assicurati che abbia estensione .json
                if not file_path.endswith('.json'):
                    file_path += '.json'

                # Esporta le impostazioni
                self.settings.export_settings(file_path)

                QMessageBox.information(
                    self,
                    "Export Completato",
                    f"Configurazione esportata con successo in:\n{file_path}"
                )
                logger.info(f"Settings exported to: {file_path}")

        except Exception as e:
            logger.error(f"Error during export: {e}")
            QMessageBox.warning(
                self,
                "Errore Export",
                f"Impossibile esportare la configurazione:\n{str(e)}"
            )

    def import_settings(self):
        """Importa una configurazione da un file JSON."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Importa Configurazione",
                os.path.expanduser("~"),
                "File JSON (*.json)"
            )

            if file_path:
                # Chiedi conferma prima di sovrascrivere
                reply = QMessageBox.question(
                    self,
                    "Conferma Import",
                    "L'importazione sovrascriverà tutte le impostazioni correnti.\n\n"
                    "Continuare?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    # Importa le impostazioni
                    self.settings.import_settings(file_path)

                    QMessageBox.information(
                        self,
                        "Import Completato",
                        "Configurazione importata con successo!\n\n"
                        "Riavvia l'applicazione per applicare tutte le modifiche."
                    )
                    logger.info(f"Settings imported from: {file_path}")

                    # Emetti segnale per aggiornare altre parti dell'app
                    self.settings_changed.emit()

        except Exception as e:
            logger.error(f"Error during import: {e}")
            QMessageBox.warning(
                self,
                "Errore Import",
                f"Impossibile importare la configurazione:\n{str(e)}"
            )
