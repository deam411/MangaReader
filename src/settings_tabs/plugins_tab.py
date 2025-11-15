"""
Tab Plugins per Settings Dialog.

Gestisce l'abilitazione/disabilitazione dei plugin e la loro configurazione.
Include anche il marketplace per scaricare nuovi plugin.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QTextEdit, QGroupBox, QCheckBox,
    QMessageBox, QTabWidget, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from typing import Optional, TYPE_CHECKING
from src.views.dialogs import PluginConfigDialog
from plugins.plugin_marketplace import PluginMarketplace
from src.logger import get_logger

if TYPE_CHECKING:
    from plugins.plugin_manager import PluginManager

logger = get_logger(__name__)


class PluginInstallWorker(QThread):
    """Worker thread per installare plugin in background."""

    progress = pyqtSignal(int, int)  # downloaded, total
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, marketplace: PluginMarketplace, plugin_info: dict):
        super().__init__()
        self.marketplace = marketplace
        self.plugin_info = plugin_info

    def run(self):
        """Installa il plugin."""
        try:
            def progress_callback(downloaded, total):
                self.progress.emit(downloaded, total)

            success = self.marketplace.install_plugin(
                self.plugin_info,
                progress_callback=progress_callback
            )

            if success:
                plugin_name = self.plugin_info.get('name', 'Plugin')
                self.finished.emit(True, f"{plugin_name} installato con successo!")
            else:
                self.finished.emit(False, "Errore durante l'installazione")

        except Exception as e:
            self.finished.emit(False, f"Errore: {str(e)}")


class PluginsTab(QWidget):
    """
    Tab per la gestione dei plugin.

    Mostra lista plugin disponibili con opzioni per abilitare/disabilitare.
    Include marketplace per scaricare nuovi plugin.
    """

    plugins_changed = pyqtSignal()  # Emesso quando i plugin cambiano

    def __init__(self, plugin_manager: 'PluginManager', parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager

        try:
            logger.info("Initializing PluginMarketplace...")
            self.marketplace = PluginMarketplace(
                plugin_dir=plugin_manager.user_plugin_dir,  # Installa nella directory utente
                app_version="0.5.0"  # TODO: Get from app
            )
            logger.info("PluginMarketplace initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PluginMarketplace: {e}", exc_info=True)
            self.marketplace = None

        self.install_worker = None

        logger.info("Initializing PluginsTab UI...")
        self.init_ui()
        self.load_plugins()
        logger.info("PluginsTab initialized")

    def init_ui(self):
        """Inizializza l'interfaccia."""
        layout = QVBoxLayout(self)

        # Tab widget per Installati/Disponibili
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Tab Plugin Installati
        logger.debug("Creating Installed tab...")
        self.installed_tab = self.create_installed_tab()
        self.tab_widget.addTab(self.installed_tab, "Installati")
        logger.debug("Installed tab created")

        # Tab Marketplace (solo se marketplace è disponibile)
        if self.marketplace is not None:
            logger.debug("Creating Marketplace tab...")
            self.marketplace_tab = self.create_marketplace_tab()
            self.tab_widget.addTab(self.marketplace_tab, "Disponibili")
            logger.info("Marketplace tab created successfully")
        else:
            logger.warning("Marketplace not available, skipping Disponibili tab")

    def create_installed_tab(self):
        """Crea il tab per i plugin installati."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_label = QLabel("Plugin installati")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header_label)

        # Descrizione
        desc_label = QLabel(
            "I plugin estendono le funzionalità di Manga Reader. "
            "Abilita o disabilita i plugin dalla lista qui sotto."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # Layout principale con lista e dettagli
        content_layout = QHBoxLayout()

        # Lista plugin (sinistra)
        self.plugin_list = QListWidget()
        self.plugin_list.currentItemChanged.connect(self.on_plugin_selected)
        content_layout.addWidget(self.plugin_list, stretch=1)

        # Dettagli plugin (destra)
        details_group = QGroupBox("Dettagli Plugin")
        details_layout = QVBoxLayout()

        # Nome plugin
        self.plugin_name_label = QLabel("Seleziona un plugin")
        self.plugin_name_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        details_layout.addWidget(self.plugin_name_label)

        # Versione e autore
        self.plugin_info_label = QLabel("")
        self.plugin_info_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        details_layout.addWidget(self.plugin_info_label)

        # Descrizione
        self.plugin_desc = QTextEdit()
        self.plugin_desc.setReadOnly(True)
        self.plugin_desc.setMaximumHeight(100)
        details_layout.addWidget(self.plugin_desc)

        # Checkbox abilita
        self.enable_checkbox = QCheckBox("Abilita questo plugin")
        self.enable_checkbox.stateChanged.connect(self.on_enable_changed)
        details_layout.addWidget(self.enable_checkbox)

        # Pulsanti azione
        button_layout = QHBoxLayout()

        self.reload_btn = QPushButton("Ricarica")
        self.reload_btn.setToolTip("Ricarica il plugin senza riavviare l'app")
        self.reload_btn.clicked.connect(self.reload_selected_plugin)
        button_layout.addWidget(self.reload_btn)

        self.configure_btn = QPushButton("Configura")
        self.configure_btn.setToolTip("Configura le impostazioni del plugin")
        self.configure_btn.clicked.connect(self.configure_selected_plugin)
        button_layout.addWidget(self.configure_btn)

        details_layout.addLayout(button_layout)
        details_layout.addStretch()

        details_group.setLayout(details_layout)
        content_layout.addWidget(details_group, stretch=1)

        layout.addLayout(content_layout)

        # Pulsanti generali
        general_buttons = QHBoxLayout()

        self.refresh_btn = QPushButton("Aggiorna Lista")
        self.refresh_btn.setToolTip("Cerca nuovi plugin nella directory")
        self.refresh_btn.clicked.connect(self.refresh_plugin_list)
        general_buttons.addWidget(self.refresh_btn)

        self.open_folder_btn = QPushButton("Apri Cartella Plugin")
        self.open_folder_btn.setToolTip("Apri la cartella dei plugin nel file manager")
        self.open_folder_btn.clicked.connect(self.open_plugin_folder)
        general_buttons.addWidget(self.open_folder_btn)

        general_buttons.addStretch()

        layout.addLayout(general_buttons)

        # Info footer
        footer_label = QLabel(
            f"Directory plugin: {self.plugin_manager.plugin_dir}"
        )
        footer_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(footer_label)

        return tab

    def create_marketplace_tab(self):
        """Crea il tab per il marketplace dei plugin."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_label = QLabel("Plugin Disponibili")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header_label)

        # Descrizione
        desc_label = QLabel(
            "Scarica e installa plugin dalla community. "
            "I plugin saranno installati nella cartella locale."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # Layout principale
        content_layout = QHBoxLayout()

        # Lista plugin marketplace (sinistra)
        self.marketplace_list = QListWidget()
        self.marketplace_list.currentItemChanged.connect(self.on_marketplace_plugin_selected)
        content_layout.addWidget(self.marketplace_list, stretch=1)

        # Dettagli plugin marketplace (destra)
        details_group = QGroupBox("Dettagli Plugin")
        details_layout = QVBoxLayout()

        # Nome plugin
        self.marketplace_name_label = QLabel("Seleziona un plugin")
        self.marketplace_name_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        details_layout.addWidget(self.marketplace_name_label)

        # Versione e autore
        self.marketplace_info_label = QLabel("")
        self.marketplace_info_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        details_layout.addWidget(self.marketplace_info_label)

        # Descrizione
        self.marketplace_desc = QTextEdit()
        self.marketplace_desc.setReadOnly(True)
        self.marketplace_desc.setMaximumHeight(100)
        details_layout.addWidget(self.marketplace_desc)

        # Progress bar
        self.download_progress = QProgressBar()
        self.download_progress.setVisible(False)
        details_layout.addWidget(self.download_progress)

        # Status label
        self.marketplace_status_label = QLabel("")
        details_layout.addWidget(self.marketplace_status_label)

        # Pulsanti azione
        button_layout = QHBoxLayout()

        self.install_btn = QPushButton("Installa")
        self.install_btn.setToolTip("Installa questo plugin")
        self.install_btn.clicked.connect(self.install_marketplace_plugin)
        self.install_btn.setEnabled(False)
        button_layout.addWidget(self.install_btn)

        self.uninstall_btn = QPushButton("Disinstalla")
        self.uninstall_btn.setToolTip("Rimuovi questo plugin")
        self.uninstall_btn.clicked.connect(self.uninstall_marketplace_plugin)
        self.uninstall_btn.setEnabled(False)
        button_layout.addWidget(self.uninstall_btn)

        details_layout.addLayout(button_layout)
        details_layout.addStretch()

        details_group.setLayout(details_layout)
        content_layout.addWidget(details_group, stretch=1)

        layout.addLayout(content_layout)

        # Pulsanti generali
        general_buttons = QHBoxLayout()

        self.fetch_marketplace_btn = QPushButton(" Aggiorna Marketplace")
        self.fetch_marketplace_btn.setToolTip("Scarica la lista aggiornata dei plugin disponibili")
        self.fetch_marketplace_btn.clicked.connect(self.fetch_marketplace)
        general_buttons.addWidget(self.fetch_marketplace_btn)

        general_buttons.addStretch()

        layout.addLayout(general_buttons)

        # Info footer
        footer_label = QLabel(
            f"Repository: {self.marketplace.marketplace_url}"
        )
        footer_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(footer_label)

        return tab

    def load_plugins(self, select_plugin: Optional[str] = None):
        """
        Carica la lista dei plugin.

        Args:
            select_plugin: Nome del plugin da selezionare dopo il caricamento (opzionale)
        """
        self.plugin_list.clear()

        plugins = self.plugin_manager.get_plugin_list()

        if not plugins:
            item = QListWidgetItem("Nessun plugin installato")
            item.setFlags(Qt.NoItemFlags)
            self.plugin_list.addItem(item)
            return

        item_to_select = None

        for plugin_info in plugins:
            display_name = plugin_info['display_name']
            version = plugin_info['version']
            enabled = plugin_info['enabled']

            item_text = f"{display_name} v{version}"
            if enabled:
                item_text += " "

            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, plugin_info['name'])  # Store internal name

            if enabled:
                item.setForeground(Qt.darkGreen)

            self.plugin_list.addItem(item)

            # Memorizza l'item se corrisponde al plugin da selezionare
            if select_plugin and plugin_info['name'] == select_plugin:
                item_to_select = item

        # Seleziona il plugin specificato dopo il caricamento
        if item_to_select:
            self.plugin_list.setCurrentItem(item_to_select)

    def on_plugin_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        """Chiamato quando viene selezionato un plugin."""
        if current is None:
            self.clear_details()
            return

        plugin_name = current.data(Qt.UserRole)
        if plugin_name is None:
            return

        # Ottieni dettagli plugin
        plugins = self.plugin_manager.get_plugin_list()
        plugin_info = next((p for p in plugins if p['name'] == plugin_name), None)

        if plugin_info:
            self.show_plugin_details(plugin_info)

    def show_plugin_details(self, plugin_info: dict):
        """Mostra i dettagli di un plugin."""
        self.plugin_name_label.setText(plugin_info['display_name'])

        info_text = f"v{plugin_info['version']} by {plugin_info['author']}"
        self.plugin_info_label.setText(info_text)

        self.plugin_desc.setPlainText(plugin_info['description'])

        # Block signals per evitare trigger durante update
        self.enable_checkbox.blockSignals(True)
        self.enable_checkbox.setChecked(plugin_info['enabled'])
        self.enable_checkbox.blockSignals(False)

        self.enable_checkbox.setEnabled(True)
        self.reload_btn.setEnabled(True)

    def clear_details(self):
        """Pulisce i dettagli del plugin."""
        self.plugin_name_label.setText("Seleziona un plugin")
        self.plugin_info_label.setText("")
        self.plugin_desc.setPlainText("")
        self.enable_checkbox.setChecked(False)
        self.enable_checkbox.setEnabled(False)
        self.reload_btn.setEnabled(False)

    def on_enable_changed(self, state: int):
        """Chiamato quando checkbox enable cambia."""
        current = self.plugin_list.currentItem()
        if current is None:
            return

        plugin_name = current.data(Qt.UserRole)
        if plugin_name is None:
            return

        enabled = state == Qt.Checked

        if enabled:
            self.plugin_manager.enable_plugin(plugin_name)
        else:
            self.plugin_manager.disable_plugin(plugin_name)

        # Ricarica lista per aggiornare il , mantenendo la selezione corrente
        self.load_plugins(select_plugin=plugin_name)
        self.plugins_changed.emit()

    def reload_selected_plugin(self):
        """Ricarica il plugin selezionato."""
        current = self.plugin_list.currentItem()
        if current is None:
            return

        plugin_name = current.data(Qt.UserRole)
        if plugin_name is None:
            return

        success = self.plugin_manager.reload_plugin(plugin_name)

        if success:
            QMessageBox.information(
                self,
                "Plugin Ricaricato",
                f"Il plugin '{plugin_name}' è stato ricaricato con successo."
            )
            # Mantieni la selezione dopo il ricaricamento
            self.load_plugins(select_plugin=plugin_name)
            self.plugins_changed.emit()
        else:
            QMessageBox.warning(
                self,
                "Errore Ricaricamento",
                f"Impossibile ricaricare il plugin '{plugin_name}'."
            )

    def configure_selected_plugin(self):
        """Configura il plugin selezionato."""
        selected_items = self.plugin_list.selectedItems()
        if not selected_items:
            return

        plugin_name = selected_items[0].data(Qt.UserRole)
        if plugin_name is None:
            return

        plugin_instance = self.plugin_manager.get_plugin(plugin_name)

        if not plugin_instance:
            QMessageBox.warning(
                self,
                "Errore",
                f"Impossibile trovare il plugin '{plugin_name}'."
            )
            return

        # Ottieni schema configurazione
        config_schema = plugin_instance.get_config_schema()
        current_config = plugin_instance.config

        # Apri dialog configurazione
        dialog = PluginConfigDialog(
            plugin_name=plugin_name,
            config_schema=config_schema,
            current_config=current_config,
            parent=self
        )

        if dialog.exec_():
            # Salva la nuova configurazione
            new_config = dialog.get_config()
            plugin_instance.set_config(new_config)

            # Persisti la configurazione (A2 task)
            self.plugin_manager.save_plugin_config(plugin_name, new_config)

            QMessageBox.information(
                self,
                "Configurazione Salvata",
                f"La configurazione del plugin '{plugin_name}' è stata salvata con successo."
            )

    def refresh_plugin_list(self):
        """Aggiorna la lista dei plugin."""
        # Salva la selezione corrente se esiste
        current = self.plugin_list.currentItem()
        selected_plugin = current.data(Qt.UserRole) if current else None

        count = self.plugin_manager.load_all_plugins()
        self.load_plugins(select_plugin=selected_plugin)
        self.plugins_changed.emit()

        QMessageBox.information(
            self,
            "Lista Aggiornata",
            f"Trovati e caricati {count} plugin."
        )

    def open_plugin_folder(self):
        """Apre la cartella dei plugin nel file manager."""
        import os
        import platform
        import subprocess

        plugin_dir = self.plugin_manager.plugin_dir

        try:
            if platform.system() == 'Windows':
                os.startfile(plugin_dir)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', plugin_dir])
            else:  # Linux
                subprocess.call(['xdg-open', plugin_dir])
        except Exception as e:
            QMessageBox.warning(
                self,
                "Errore",
                f"Impossibile aprire la cartella: {e}"
            )

    def fetch_marketplace(self):
        """Scarica la lista dei plugin dal marketplace."""
        if self.marketplace is None:
            QMessageBox.warning(
                self,
                "Errore",
                "Marketplace non disponibile. Verifica i log per dettagli."
            )
            return

        self.fetch_marketplace_btn.setEnabled(False)
        self.fetch_marketplace_btn.setText(" Scaricando...")

        success = self.marketplace.fetch_available_plugins()

        if success:
            self.load_marketplace_plugins()
            QMessageBox.information(
                self,
                "Marketplace Aggiornato",
                f"Trovati {len(self.marketplace.available_plugins)} plugin disponibili."
            )
        else:
            QMessageBox.warning(
                self,
                "Errore",
                "Impossibile scaricare la lista dei plugin dal marketplace.\n"
                "Verifica la connessione internet."
            )

        self.fetch_marketplace_btn.setEnabled(True)
        self.fetch_marketplace_btn.setText(" Aggiorna Marketplace")

    def load_marketplace_plugins(self):
        """Carica la lista dei plugin dal marketplace."""
        self.marketplace_list.clear()

        plugins = self.marketplace.get_available_plugins()

        if not plugins:
            item = QListWidgetItem("Nessun plugin disponibile. Clicca 'Aggiorna Marketplace'")
            item.setFlags(Qt.NoItemFlags)
            self.marketplace_list.addItem(item)
            return

        for plugin_info in plugins:
            display_name = plugin_info.get('name', 'Unknown')
            version = plugin_info.get('version', '0.0.0')
            plugin_id = plugin_info.get('id')

            item_text = f"{display_name} v{version}"

            # Controlla se installato
            if self.marketplace.is_plugin_installed(plugin_id):
                item_text += " "

                # Controlla se aggiornamento disponibile
                if self.marketplace.is_update_available(plugin_id, version):
                    item_text += " (Aggiornamento disponibile)"

            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, plugin_info)
            self.marketplace_list.addItem(item)

    def on_marketplace_plugin_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        """Chiamato quando viene selezionato un plugin dal marketplace."""
        if current is None:
            self.clear_marketplace_details()
            return

        plugin_info = current.data(Qt.UserRole)
        if plugin_info is None:
            return

        self.show_marketplace_details(plugin_info)

    def show_marketplace_details(self, plugin_info: dict):
        """Mostra i dettagli di un plugin del marketplace."""
        name = plugin_info.get('name', 'Unknown')
        version = plugin_info.get('version', '0.0.0')
        author = plugin_info.get('author', 'Unknown')
        description = plugin_info.get('description', 'Nessuna descrizione disponibile')
        plugin_id = plugin_info.get('id')
        requires_version = plugin_info.get('requires_version', '0.0.0')

        self.marketplace_name_label.setText(name)

        info_text = f"v{version} by {author}"
        self.marketplace_info_label.setText(info_text)

        self.marketplace_desc.setPlainText(description)

        # Verifica compatibilità
        is_compatible = self.marketplace.is_compatible(requires_version)
        is_installed = self.marketplace.is_plugin_installed(plugin_id)
        is_update = self.marketplace.is_update_available(plugin_id, version) if is_installed else False

        # Aggiorna status
        if not is_compatible:
            self.marketplace_status_label.setText(
                f" Richiede app v{requires_version} o superiore"
            )
            self.marketplace_status_label.setStyleSheet("color: orange;")
            self.install_btn.setEnabled(False)
        elif is_installed and not is_update:
            self.marketplace_status_label.setText(" Installato")
            self.marketplace_status_label.setStyleSheet("color: green;")
            self.install_btn.setEnabled(False)
        elif is_update:
            self.marketplace_status_label.setText(" Aggiornamento disponibile")
            self.marketplace_status_label.setStyleSheet("color: blue;")
            self.install_btn.setText("Aggiorna")
            self.install_btn.setEnabled(True)
        else:
            self.marketplace_status_label.setText("")
            self.install_btn.setText("Installa")
            self.install_btn.setEnabled(True)

        # Pulsante disinstalla
        self.uninstall_btn.setEnabled(is_installed)

    def clear_marketplace_details(self):
        """Pulisce i dettagli del plugin marketplace."""
        self.marketplace_name_label.setText("Seleziona un plugin")
        self.marketplace_info_label.setText("")
        self.marketplace_desc.setPlainText("")
        self.marketplace_status_label.setText("")
        self.install_btn.setEnabled(False)
        self.uninstall_btn.setEnabled(False)

    def install_marketplace_plugin(self):
        """Installa il plugin selezionato dal marketplace."""
        current = self.marketplace_list.currentItem()
        if current is None:
            return

        plugin_info = current.data(Qt.UserRole)
        if plugin_info is None:
            return

        # Disabilita pulsanti durante installazione
        self.install_btn.setEnabled(False)
        self.fetch_marketplace_btn.setEnabled(False)

        # Mostra progress bar
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)

        # Avvia worker thread
        self.install_worker = PluginInstallWorker(self.marketplace, plugin_info)
        self.install_worker.progress.connect(self.on_install_progress)
        self.install_worker.finished.connect(self.on_install_finished)
        self.install_worker.start()

    def on_install_progress(self, downloaded: int, total: int):
        """Aggiorna la progress bar durante il download."""
        if total > 0:
            progress = int((downloaded / total) * 100)
            self.download_progress.setValue(progress)

    def on_install_finished(self, success: bool, message: str):
        """Chiamato quando l'installazione è completata."""
        self.download_progress.setVisible(False)
        self.install_btn.setEnabled(True)
        self.fetch_marketplace_btn.setEnabled(True)

        if success:
            QMessageBox.information(self, "Installazione Completata", message)

            # Ricarica lista plugin installati e marketplace
            self.plugin_manager.load_all_plugins()
            self.load_plugins()
            self.load_marketplace_plugins()
            self.plugins_changed.emit()
        else:
            QMessageBox.warning(self, "Errore Installazione", message)

    def uninstall_marketplace_plugin(self):
        """Disinstalla il plugin selezionato."""
        current = self.marketplace_list.currentItem()
        if current is None:
            return

        plugin_info = current.data(Qt.UserRole)
        if plugin_info is None:
            return

        plugin_id = plugin_info.get('id')
        plugin_name = plugin_info.get('name')

        reply = QMessageBox.question(
            self,
            "Conferma Disinstallazione",
            f"Sei sicuro di voler disinstallare '{plugin_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Disabilita e scarica plugin
            if plugin_id in self.plugin_manager.plugins:
                self.plugin_manager.disable_plugin(plugin_id)
                self.plugin_manager.unload_plugin(plugin_id)

            # Rimuovi file
            success = self.marketplace.uninstall_plugin(plugin_id)

            if success:
                QMessageBox.information(
                    self,
                    "Disinstallazione Completata",
                    f"'{plugin_name}' è stato disinstallato con successo."
                )

                # Ricarica liste
                self.plugin_manager.load_all_plugins()
                self.load_plugins()
                self.load_marketplace_plugins()
                self.plugins_changed.emit()
            else:
                QMessageBox.warning(
                    self,
                    "Errore",
                    f"Impossibile disinstallare '{plugin_name}'."
                )

    def get_values(self) -> dict:
        """
        Restituisce i valori correnti del tab.

        Returns:
            Dict vuoto (configurazione gestita dal PluginManager)
        """
        # I plugin sono già salvati automaticamente dal manager
        return {}
