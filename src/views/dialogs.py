"""
Dialogs utilizzati nelle views.

Contiene tutti i dialog per interazione utente: import archivi, bookmarks, shortcuts.
"""

import os
from typing import Dict, Any
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout,
    QDialogButtonBox, QScrollArea, QWidget, QPushButton, QCheckBox,
    QSpinBox, QTextEdit
)
from PyQt5.QtCore import Qt
from src.constants import DIALOG_MIN_WIDTH


class ArchiveImportDialog(QDialog):
    """Dialog per raccogliere metadata durante import di archivi CBZ/CBR."""

    def __init__(self, archive_path, parent=None):
        super().__init__(parent)
        self.archive_path = archive_path
        self.setWindowTitle('Import Archivio - Metadata')
        self.setMinimumWidth(DIALOG_MIN_WIDTH)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Info file
        file_name = os.path.basename(self.archive_path)
        info_label = QLabel(f"Importazione: {file_name}")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Form per metadata
        form_layout = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setText(os.path.splitext(file_name)[0])  # Default: nome file
        form_layout.addRow("Titolo:", self.title_input)

        self.author_input = QLineEdit()
        form_layout.addRow("Autore:", self.author_input)

        self.volume_input = QLineEdit()
        self.volume_input.setText("Volume 1")
        form_layout.addRow("Nome Volume:", self.volume_input)

        self.chapter_input = QLineEdit()
        self.chapter_input.setText("Chapter 1")
        form_layout.addRow("Nome Capitolo:", self.chapter_input)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_metadata(self):
        """Restituisce i metadata inseriti."""
        return {
            'title': self.title_input.text() or None,
            'author': self.author_input.text() or None,
            'volume_name': self.volume_input.text() or "Volume 1",
            'chapter_name': self.chapter_input.text() or "Chapter 1"
        }


class BookmarkDialog(QDialog):
    """Dialog per aggiungere o rinominare un segnalibro."""

    def __init__(self, title="Nuovo Segnalibro", default_name="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        self.initUI(default_name)

    def initUI(self, default_name):
        layout = QVBoxLayout(self)

        # Label istruzioni
        info_label = QLabel("Inserisci un nome per il segnalibro:")
        layout.addWidget(info_label)

        # Input nome
        self.name_input = QLineEdit()
        self.name_input.setText(default_name)
        self.name_input.selectAll()
        layout.addWidget(self.name_input)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Focus sull'input
        self.name_input.setFocus()

    def get_name(self):
        """Restituisce il nome inserito."""
        return self.name_input.text().strip()


class ShortcutsDialog(QDialog):
    """Dialog che mostra tutte le scorciatoie da tastiera disponibili."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scorciatoie da Tastiera")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Titolo
        title = QLabel("<h2>Scorciatoie da Tastiera</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Scroll area per le scorciatoie
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Widget contenitore
        container = QWidget()
        scroll.setWidget(container)
        shortcuts_layout = QVBoxLayout(container)

        # Definisci tutte le scorciatoie organizzate per categoria
        shortcuts_data = {
            "Navigazione Generale": [
                ("Esc", "Chiudi applicazione / Esci dalla schermata"),
                ("Backspace", "Torna alla schermata precedente"),
                ("F11", "Toggle fullscreen"),
            ],
            "Libreria": [
                ("Ctrl+F", "Focus sulla barra di ricerca"),
                ("Ctrl+I", "Importa manga (.manga)"),
                ("Ctrl+E", "Esporta manga selezionato"),
                ("Ctrl+N", "Crea nuovo manga (apri editor)"),
                ("F5", "Aggiorna libreria"),
                ("Z", "Importa archivio CBZ/CBR"),
            ],
            "Lettore": [
                ("↑", "Zoom in (10%)"),
                ("↓", "Zoom out (10%)"),
                ("Mouse Drag", "Pan/sposta immagine (tenere click sinistro)"),
                ("Scroll", "Scorri pagine verticalmente"),
                ("Ctrl+D", "Toggle vista doppia pagina"),
                ("Ctrl+B", "Aggiungi segnalibro alla pagina corrente"),
            ],
            "Impostazioni": [
                ("Pulsante Impostazioni", "Apri pannello impostazioni"),
                ("F1", "Mostra questo pannello scorciatoie"),
            ],
        }

        # Crea sezioni per ogni categoria
        for category, shortcuts in shortcuts_data.items():
            # Titolo categoria
            category_label = QLabel(f"<h3>{category}</h3>")
            shortcuts_layout.addWidget(category_label)

            # Tabella scorciatoie
            for key, description in shortcuts:
                shortcut_widget = QWidget()
                shortcut_layout = QHBoxLayout(shortcut_widget)
                shortcut_layout.setContentsMargins(20, 5, 20, 5)

                # Tasto/combinazione
                key_label = QLabel(f"<b>{key}</b>")
                key_label.setMinimumWidth(150)
                key_label.setStyleSheet("""
                    QLabel {
                        background-color: #404040;
                        padding: 5px 10px;
                        border-radius: 5px;
                        color: white;
                    }
                """)
                shortcut_layout.addWidget(key_label)

                # Descrizione
                desc_label = QLabel(description)
                desc_label.setWordWrap(True)
                shortcut_layout.addWidget(desc_label, 1)

                shortcuts_layout.addWidget(shortcut_widget)

            # Spaziatore tra categorie
            shortcuts_layout.addSpacing(10)

        shortcuts_layout.addStretch()

        # Pulsante Chiudi
        close_button = QPushButton("Chiudi")
        close_button.clicked.connect(self.accept)
        close_button.setMaximumWidth(100)
        layout.addWidget(close_button, alignment=Qt.AlignCenter)


class PluginConfigDialog(QDialog):
    """Dialog per configurare un plugin basato sul suo schema."""

    def __init__(self, plugin_name: str, config_schema: Dict[str, Any],
                 current_config: Dict[str, Any], parent=None):
        """
        Inizializza il dialog di configurazione plugin.

        Args:
            plugin_name: Nome del plugin
            config_schema: Schema configurazione dal plugin.get_config_schema()
            current_config: Configurazione corrente del plugin
            parent: Widget genitore
        """
        super().__init__(parent)
        self.plugin_name = plugin_name
        self.config_schema = config_schema
        self.current_config = current_config
        self.widgets = {}  # Memorizza i widget per recuperare i valori

        self.setWindowTitle(f"Configura Plugin: {plugin_name}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Titolo
        title = QLabel(f"<h2>Configurazione: {self.plugin_name}</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Info
        info_label = QLabel("Configura le opzioni del plugin:")
        info_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Scroll area per i campi di configurazione
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Container per i campi
        container = QWidget()
        scroll.setWidget(container)
        form_layout = QFormLayout(container)
        form_layout.setSpacing(15)

        # Genera dinamicamente i widget in base allo schema
        if not self.config_schema:
            no_config_label = QLabel("Questo plugin non ha opzioni configurabili.")
            no_config_label.setStyleSheet("color: gray; font-style: italic;")
            no_config_label.setAlignment(Qt.AlignCenter)
            form_layout.addRow(no_config_label)
        else:
            for field_name, field_info in self.config_schema.items():
                widget = self._create_widget_for_field(field_name, field_info)
                if widget:
                    # Label con descrizione
                    label = QLabel(field_name.replace('_', ' ').title() + ":")
                    label.setToolTip(field_info.get('description', ''))

                    # Descrizione sotto il campo
                    field_container = QWidget()
                    field_layout = QVBoxLayout(field_container)
                    field_layout.setContentsMargins(0, 0, 0, 0)
                    field_layout.addWidget(widget)

                    desc = field_info.get('description', '')
                    if desc:
                        desc_label = QLabel(desc)
                        desc_label.setStyleSheet("color: gray; font-size: 10px;")
                        desc_label.setWordWrap(True)
                        field_layout.addWidget(desc_label)

                    form_layout.addRow(label, field_container)
                    self.widgets[field_name] = widget

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_widget_for_field(self, field_name: str, field_info: Dict[str, Any]):
        """
        Crea il widget appropriato per un campo di configurazione.

        Args:
            field_name: Nome del campo
            field_info: Informazioni sul campo (type, default, description)

        Returns:
            Widget PyQt appropriato o None
        """
        field_type = field_info.get('type', 'str')
        default_value = field_info.get('default')
        current_value = self.current_config.get(field_name, default_value)

        if field_type == 'bool':
            widget = QCheckBox()
            widget.setChecked(current_value if current_value is not None else default_value)
            return widget

        elif field_type == 'int':
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(current_value if current_value is not None else default_value)
            return widget

        elif field_type == 'str':
            widget = QLineEdit()
            widget.setText(str(current_value if current_value is not None else default_value))
            return widget

        elif field_type == 'text':
            widget = QTextEdit()
            widget.setPlainText(str(current_value if current_value is not None else default_value))
            widget.setMaximumHeight(100)
            return widget

        elif field_type == 'list':
            # Per liste, usiamo QTextEdit con una riga per elemento
            widget = QTextEdit()
            if current_value is not None:
                widget.setPlainText('\n'.join(str(item) for item in current_value))
            elif default_value:
                widget.setPlainText('\n'.join(str(item) for item in default_value))
            widget.setMaximumHeight(100)
            widget.setToolTip("Inserisci un elemento per riga")
            return widget

        else:
            # Fallback: campo testo generico
            widget = QLineEdit()
            widget.setText(str(current_value if current_value is not None else default_value or ''))
            return widget

    def get_config(self) -> Dict[str, Any]:
        """
        Restituisce la configurazione impostata dall'utente.

        Returns:
            Dict con la configurazione aggiornata
        """
        config = {}

        for field_name, widget in self.widgets.items():
            field_type = self.config_schema[field_name].get('type', 'str')

            if field_type == 'bool':
                config[field_name] = widget.isChecked()

            elif field_type == 'int':
                config[field_name] = widget.value()

            elif field_type == 'str':
                config[field_name] = widget.text()

            elif field_type == 'text':
                config[field_name] = widget.toPlainText()

            elif field_type == 'list':
                text = widget.toPlainText().strip()
                config[field_name] = [line.strip() for line in text.split('\n') if line.strip()]

            else:
                # Fallback
                if isinstance(widget, QLineEdit):
                    config[field_name] = widget.text()
                elif isinstance(widget, QTextEdit):
                    config[field_name] = widget.toPlainText()

        return config
