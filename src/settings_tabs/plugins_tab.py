"""
Tab Plugins per Settings Dialog.

Gestisce l'abilitazione/disabilitazione dei plugin e la loro configurazione.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QTextEdit, QGroupBox, QCheckBox,
    QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from plugins.plugin_manager import PluginManager


class PluginsTab(QWidget):
    """
    Tab per la gestione dei plugin.

    Mostra lista plugin disponibili con opzioni per abilitare/disabilitare.
    """

    plugins_changed = pyqtSignal()  # Emesso quando i plugin cambiano

    def __init__(self, plugin_manager: 'PluginManager', parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.init_ui()
        self.load_plugins()

    def init_ui(self):
        """Inizializza l'interfaccia."""
        layout = QVBoxLayout(self)

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
        self.configure_btn.setEnabled(False)  # TODO: implementare dialog config
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

    def load_plugins(self):
        """Carica la lista dei plugin."""
        self.plugin_list.clear()

        plugins = self.plugin_manager.get_plugin_list()

        if not plugins:
            item = QListWidgetItem("Nessun plugin installato")
            item.setFlags(Qt.NoItemFlags)
            self.plugin_list.addItem(item)
            return

        for plugin_info in plugins:
            display_name = plugin_info['display_name']
            version = plugin_info['version']
            enabled = plugin_info['enabled']

            item_text = f"{display_name} v{version}"
            if enabled:
                item_text += " ✓"

            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, plugin_info['name'])  # Store internal name

            if enabled:
                item.setForeground(Qt.darkGreen)

            self.plugin_list.addItem(item)

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

        # Ricarica lista per aggiornare il ✓
        self.load_plugins()
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
            self.load_plugins()
            self.plugins_changed.emit()
        else:
            QMessageBox.warning(
                self,
                "Errore Ricaricamento",
                f"Impossibile ricaricare il plugin '{plugin_name}'."
            )

    def configure_selected_plugin(self):
        """Configura il plugin selezionato."""
        # TODO: Implementare dialog configurazione basato su get_config_schema()
        QMessageBox.information(
            self,
            "Configurazione Plugin",
            "La configurazione dei plugin sarà disponibile in una versione futura."
        )

    def refresh_plugin_list(self):
        """Aggiorna la lista dei plugin."""
        count = self.plugin_manager.load_all_plugins()
        self.load_plugins()
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

    def get_values(self) -> dict:
        """
        Restituisce i valori correnti del tab.

        Returns:
            Dict vuoto (configurazione gestita dal PluginManager)
        """
        # I plugin sono già salvati automaticamente dal manager
        return {}
