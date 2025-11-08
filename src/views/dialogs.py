"""
Dialogs utilizzati nelle views.

Contiene tutti i dialog per interazione utente: import archivi, bookmarks, shortcuts.
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout,
    QDialogButtonBox, QScrollArea, QWidget, QPushButton
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
