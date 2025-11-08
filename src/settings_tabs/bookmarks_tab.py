"""
Tab impostazioni segnalibri: categorie e opzioni.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QGroupBox, QListWidget,
                              QCheckBox, QInputDialog, QMessageBox)
from ..settings import Settings


class BookmarksTab(QWidget):
    """Tab per impostazioni segnalibri (categorie + auto-bookmark)."""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.parent_dialog = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Info header
        info_label = QLabel(
            "Gestisci le categorie dei segnalibri per organizzare meglio la tua libreria.\n"
            "La categoria 'Default' non può essere rimossa."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 10px; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

        # Gruppo Categorie
        categories_group = QGroupBox("Categorie Segnalibri")
        categories_layout = QVBoxLayout()

        # Lista categorie
        self.categories_list = QListWidget()
        self.categories_list.setMaximumHeight(200)
        self._load_bookmark_categories()
        categories_layout.addWidget(self.categories_list)

        # Pulsanti gestione categorie
        buttons_layout = QHBoxLayout()

        add_category_btn = QPushButton("Aggiungi Categoria")
        add_category_btn.clicked.connect(self._add_bookmark_category)
        buttons_layout.addWidget(add_category_btn)

        remove_category_btn = QPushButton("Rimuovi Categoria")
        remove_category_btn.clicked.connect(self._remove_bookmark_category)
        buttons_layout.addWidget(remove_category_btn)

        categories_layout.addLayout(buttons_layout)
        categories_group.setLayout(categories_layout)
        layout.addWidget(categories_group)

        # Gruppo Opzioni
        options_group = QGroupBox("Opzioni")
        options_layout = QVBoxLayout()

        # Auto-bookmark checkbox
        self.auto_bookmark_check = QCheckBox("Salva automaticamente l'ultima pagina letta")
        self.auto_bookmark_check.setChecked(self.settings.get("bookmarks.auto_bookmark", True))
        self.auto_bookmark_check.setToolTip(
            "Se attivato, l'app ricorderà automaticamente l'ultima pagina\n"
            "che hai letto per ogni manga"
        )
        options_layout.addWidget(self.auto_bookmark_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        layout.addStretch()
        self.setLayout(layout)

    def _load_bookmark_categories(self):
        """Carica le categorie di bookmarks nella lista."""
        self.categories_list.clear()
        categories = self.settings.get_bookmark_categories()
        for category in categories:
            self.categories_list.addItem(category)

    def _add_bookmark_category(self):
        """Aggiunge una nuova categoria di bookmarks."""
        text, ok = QInputDialog.getText(
            self,
            "Nuova Categoria",
            "Nome della nuova categoria:"
        )

        if ok and text:
            text = text.strip()
            if not text:
                return

            # Verifica che non esista già
            categories = self.settings.get_bookmark_categories()
            if text in categories:
                QMessageBox.warning(
                    self,
                    "Categoria Esistente",
                    f"La categoria '{text}' esiste già."
                )
                return

            # Aggiungi categoria
            if self.settings.add_bookmark_category(text):
                self._load_bookmark_categories()
                QMessageBox.information(
                    self,
                    "Categoria Aggiunta",
                    f"Categoria '{text}' aggiunta con successo!"
                )

    def _remove_bookmark_category(self):
        """Rimuove la categoria selezionata."""
        current_item = self.categories_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self,
                "Nessuna Selezione",
                "Seleziona una categoria da rimuovere."
            )
            return

        category = current_item.text()

        # Verifica che non sia Default
        if category == "Default":
            QMessageBox.warning(
                self,
                "Categoria Protetta",
                "La categoria 'Default' non può essere rimossa."
            )
            return

        # Conferma rimozione
        reply = QMessageBox.question(
            self,
            "Conferma Rimozione",
            f"Rimuovere la categoria '{category}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.settings.remove_bookmark_category(category):
                self._load_bookmark_categories()
                QMessageBox.information(
                    self,
                    "Categoria Rimossa",
                    f"Categoria '{category}' rimossa con successo!"
                )

    def get_values(self):
        """Ritorna i valori correnti del tab."""
        return {
            "bookmarks.auto_bookmark": self.auto_bookmark_check.isChecked()
            # Note: Le categorie vengono salvate direttamente tramite settings methods
        }
