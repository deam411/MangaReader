"""
Dialog per gestire le impostazioni dell'applicazione.
"""
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFileDialog, QComboBox,
                              QGroupBox, QMessageBox, QTabWidget, QWidget,
                              QCheckBox, QSpinBox, QProgressDialog, QTextEdit,
                              QApplication, QListWidget, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from .settings import Settings
from .updater import (check_for_updates, download_update, install_update,
                      get_current_version, get_update_info_text)
from .logger import get_logger

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """Dialog per modificare le impostazioni dell'applicazione."""

    settings_changed = pyqtSignal()  # Segnale emesso quando le settings cambiano

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = Settings()
        self.setWindowTitle("Impostazioni")
        self.setMinimumSize(600, 500)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Tab widget per organizzare le impostazioni
        tabs = QTabWidget()

        # Tab Generale
        general_tab = self._create_general_tab()
        tabs.addTab(general_tab, "Generale")

        # Tab Aspetto
        appearance_tab = self._create_appearance_tab()
        tabs.addTab(appearance_tab, "Aspetto")

        # Tab Performance
        performance_tab = self._create_performance_tab()
        tabs.addTab(performance_tab, "Performance")

        # Tab Reader
        reader_tab = self._create_reader_tab()
        tabs.addTab(reader_tab, "Reader")

        # Tab Scorciatoie
        shortcuts_tab = self._create_shortcuts_tab()
        tabs.addTab(shortcuts_tab, "Scorciatoie")

        # Tab Segnalibri
        bookmarks_tab = self._create_bookmarks_tab()
        tabs.addTab(bookmarks_tab, "Segnalibri")

        layout.addWidget(tabs)

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

    def _create_general_tab(self):
        """Crea il tab delle impostazioni generali."""
        widget = QWidget()
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
            from .paths import get_project_root
            import os
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
        widget.setLayout(layout)
        return widget

    def _create_appearance_tab(self):
        """Crea il tab delle impostazioni di aspetto."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Gruppo Tema
        theme_group = QGroupBox("Tema")
        theme_layout = QVBoxLayout()

        theme_label = QLabel("Seleziona tema:")
        theme_layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Sistema", "Scuro", "Chiaro"])
        current_theme = self.settings.get_theme()
        if current_theme == "system":
            self.theme_combo.setCurrentText("Sistema")
        elif current_theme == "dark":
            self.theme_combo.setCurrentText("Scuro")
        else:
            self.theme_combo.setCurrentText("Chiaro")
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)

        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_performance_tab(self):
        """Crea il tab delle impostazioni di performance."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Gruppo Cache
        cache_group = QGroupBox("Cache Immagini")
        cache_layout = QVBoxLayout()

        # Cache size
        cache_size_layout = QHBoxLayout()
        cache_size_label = QLabel("Dimensione cache (numero immagini):")
        cache_size_layout.addWidget(cache_size_label)

        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setMinimum(10)
        self.cache_size_spin.setMaximum(200)
        self.cache_size_spin.setValue(self.settings.get("performance.image_cache_size", 50))
        cache_size_layout.addWidget(self.cache_size_spin)
        cache_size_layout.addStretch()

        cache_layout.addLayout(cache_size_layout)

        # Lazy loading
        self.lazy_loading_check = QCheckBox("Abilita lazy loading")
        self.lazy_loading_check.setChecked(self.settings.get("performance.lazy_loading", True))
        cache_layout.addWidget(self.lazy_loading_check)

        # Preload pages
        preload_layout = QHBoxLayout()
        preload_label = QLabel("Pagine da precaricare:")
        preload_layout.addWidget(preload_label)

        self.preload_spin = QSpinBox()
        self.preload_spin.setMinimum(0)
        self.preload_spin.setMaximum(10)
        self.preload_spin.setValue(self.settings.get("performance.preload_pages", 2))
        preload_layout.addWidget(self.preload_spin)
        preload_layout.addStretch()

        cache_layout.addLayout(preload_layout)

        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_reader_tab(self):
        """Crea il tab delle impostazioni del lettore."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Gruppo Modalità Lettura
        reading_group = QGroupBox("Modalità di Lettura")
        reading_layout = QVBoxLayout()

        # Direzione lettura
        direction_layout = QHBoxLayout()
        direction_label = QLabel("Direzione lettura:")
        direction_layout.addWidget(direction_label)

        self.reading_direction_combo = QComboBox()
        self.reading_direction_combo.addItem("Left to Right (LTR)", "ltr")
        self.reading_direction_combo.addItem("Right to Left (RTL)", "rtl")

        # Imposta valore corrente
        current_direction = self.settings.get("reader.reading_direction", "ltr")
        index = self.reading_direction_combo.findData(current_direction)
        if index >= 0:
            self.reading_direction_combo.setCurrentIndex(index)

        direction_layout.addWidget(self.reading_direction_combo)
        direction_layout.addStretch()
        reading_layout.addLayout(direction_layout)

        # Info
        info_label = QLabel("RTL è utilizzato tipicamente per manga giapponesi")
        info_label.setStyleSheet("color: gray; font-size: 10px; font-style: italic;")
        reading_layout.addWidget(info_label)

        reading_group.setLayout(reading_layout)
        layout.addWidget(reading_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_shortcuts_tab(self):
        """Crea il tab delle scorciatoie tastiera."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Info header
        info_label = QLabel(
            "Personalizza le scorciatoie tastiera. Usa formati come: Ctrl+K, Alt+F, F11, ecc.\n"
            "Lascia vuoto per disabilitare una scorciatoia."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 10px; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

        # Ottieni tutte le scorciatoie
        shortcuts = self.settings.get_all_shortcuts()

        # Dizionario per memorizzare i widget input
        self.shortcut_inputs = {}

        # Gruppo Navigazione
        nav_group = QGroupBox("Navigazione")
        nav_layout = QVBoxLayout()

        nav_shortcuts = {
            "next_page": "Pagina successiva",
            "prev_page": "Pagina precedente",
            "back": "Indietro",
            "quit": "Esci"
        }

        for key, label in nav_shortcuts.items():
            if key in shortcuts:
                row = QHBoxLayout()
                row.addWidget(QLabel(label + ":"))

                input_field = QLineEdit()
                input_field.setText(shortcuts.get(key, ""))
                input_field.setPlaceholderText("Es: Ctrl+N, F5, etc.")
                self.shortcut_inputs[key] = input_field

                row.addWidget(input_field)
                nav_layout.addLayout(row)

        nav_group.setLayout(nav_layout)
        layout.addWidget(nav_group)

        # Gruppo Interfaccia
        ui_group = QGroupBox("Interfaccia")
        ui_layout = QVBoxLayout()

        ui_shortcuts = {
            "fullscreen": "Schermo intero",
            "settings": "Impostazioni",
            "help": "Aiuto",
            "search": "Cerca",
            "bookmarks": "Segnalibri"
        }

        for key, label in ui_shortcuts.items():
            if key in shortcuts:
                row = QHBoxLayout()
                row.addWidget(QLabel(label + ":"))

                input_field = QLineEdit()
                input_field.setText(shortcuts.get(key, ""))
                input_field.setPlaceholderText("Es: F11, Ctrl+F, etc.")
                self.shortcut_inputs[key] = input_field

                row.addWidget(input_field)
                ui_layout.addLayout(row)

        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)

        # Gruppo Manga
        manga_group = QGroupBox("Gestione Manga")
        manga_layout = QVBoxLayout()

        manga_shortcuts = {
            "new_manga": "Nuovo Manga",
            "import": "Importa",
            "export": "Esporta",
            "refresh": "Aggiorna"
        }

        for key, label in manga_shortcuts.items():
            if key in shortcuts:
                row = QHBoxLayout()
                row.addWidget(QLabel(label + ":"))

                input_field = QLineEdit()
                input_field.setText(shortcuts.get(key, ""))
                input_field.setPlaceholderText("Es: Ctrl+N, F5, etc.")
                self.shortcut_inputs[key] = input_field

                row.addWidget(input_field)
                manga_layout.addLayout(row)

        manga_group.setLayout(manga_layout)
        layout.addWidget(manga_group)

        # Pulsante ripristina default scorciatoie
        reset_shortcuts_btn = QPushButton("Ripristina Scorciatoie Default")
        reset_shortcuts_btn.clicked.connect(self._reset_shortcuts_to_default)
        layout.addWidget(reset_shortcuts_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _reset_shortcuts_to_default(self):
        """Ripristina le scorciatoie ai valori di default."""
        reply = QMessageBox.question(
            self,
            "Ripristina scorciatoie",
            "Ripristinare tutte le scorciatoie ai valori di default?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Ottieni shortcuts default
            from .constants import DEFAULT_THEME
            default_settings = self.settings._get_default_settings()
            default_shortcuts = default_settings.get("shortcuts", {})

            # Aggiorna i campi UI
            for key, value in default_shortcuts.items():
                if key in self.shortcut_inputs:
                    self.shortcut_inputs[key].setText(value)

            QMessageBox.information(
                self,
                "Scorciatoie ripristinate",
                "Le scorciatoie sono state ripristinate ai valori di default.\n"
                "Clicca OK per salvare le modifiche."
            )

    def _create_bookmarks_tab(self):
        """Crea il tab delle impostazioni segnalibri."""
        widget = QWidget()
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
        widget.setLayout(layout)
        return widget

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

        # Chiedi conferma
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

    def browse_library_path(self):
        """Apre un dialog per selezionare la directory della libreria."""
        # Ottieni il percorso attuale, rimuovendo "(default)" se presente
        current_path = self.library_path_input.text().replace(" (default)", "").strip()

        # Se non esiste un percorso, usa la home dell'utente
        if not current_path or not os.path.exists(current_path):
            current_path = os.path.expanduser("~")

        new_path = QFileDialog.getExistingDirectory(
            self,
            "Seleziona directory libreria",
            current_path
        )

        if new_path:
            self.library_path_input.setText(new_path)
            # Salva subito la modifica
            self.settings.set_library_path(new_path)
            self.settings_changed.emit()
            QMessageBox.information(
                self,
                "Libreria spostata",
                f"La libreria è stata spostata in:\n{new_path}\n\n"
                "Riavvia l'applicazione per vedere i manga nella nuova posizione.\n"
                "Ricorda di spostare manualmente i file .manga nella nuova directory!"
            )

    def on_theme_changed(self, text):
        """Gestisce il cambio di tema."""
        if text == "Sistema":
            theme = "system"
        elif text == "Scuro":
            theme = "dark"
        else:
            theme = "light"
        self.settings.set_theme(theme)
        self.settings_changed.emit()

    def accept(self):
        """Salva le impostazioni quando l'utente clicca OK."""
        # Salva performance settings
        self.settings.set("performance.image_cache_size", self.cache_size_spin.value())
        self.settings.set("performance.lazy_loading", self.lazy_loading_check.isChecked())
        self.settings.set("performance.preload_pages", self.preload_spin.value())

        # Salva reader settings
        reading_direction = self.reading_direction_combo.currentData()
        self.settings.set("reader.reading_direction", reading_direction)

        # Salva shortcuts
        if hasattr(self, 'shortcut_inputs'):
            for action, input_field in self.shortcut_inputs.items():
                shortcut_value = input_field.text().strip()
                self.settings.set_shortcut(action, shortcut_value)

        # Salva bookmarks settings
        if hasattr(self, 'auto_bookmark_check'):
            self.settings.set("bookmarks.auto_bookmark", self.auto_bookmark_check.isChecked())

        self.settings.save()
        self.settings_changed.emit()
        super().accept()

    def reset_settings(self):
        """Ripristina le impostazioni di default."""
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

    def check_for_updates(self):
        """Controlla se ci sono aggiornamenti disponibili su GitHub."""
        logger.info("Controllo aggiornamenti richiesto dall'utente")

        # Mostra dialog "checking..."
        progress = QMessageBox(self)
        progress.setWindowTitle("Controllo aggiornamenti")
        progress.setText("Controllo aggiornamenti su GitHub...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()
        QApplication.processEvents()

        try:
            update_info = check_for_updates()

            progress.hide()

            if update_info is None:
                # Nessun aggiornamento disponibile
                QMessageBox.information(
                    self,
                    "Nessun aggiornamento",
                    f"Stai già utilizzando l'ultima versione (v{get_current_version()})!"
                )
                return

            # Aggiornamento disponibile - mostra dialog con dettagli
            self._show_update_dialog(update_info)

        except Exception as e:
            progress.hide()
            # Se è 404, significa semplicemente che non ci sono release pubblicate
            # Non mostrare errore all'utente
            if "404" in str(e):
                logger.info("Nessuna release pubblicata su GitHub")
                return

            logger.error(f"Errore durante controllo aggiornamenti: {e}")
            QMessageBox.warning(
                self,
                "Errore",
                f"Impossibile controllare gli aggiornamenti:\n{str(e)}\n\n"
                "Verifica la connessione internet e riprova."
            )

    def _show_update_dialog(self, update_info):
        """Mostra dialog con dettagli aggiornamento e opzione download."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Aggiornamento disponibile")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        # Titolo
        title = QLabel(f"Nuova versione disponibile: v{update_info['version']}")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        # Release notes in text edit scrollabile
        notes_text = QTextEdit()
        notes_text.setReadOnly(True)
        notes_text.setPlainText(update_info.get('release_notes', 'Nessuna nota disponibile'))
        layout.addWidget(notes_text)

        # Pulsanti
        buttons_layout = QHBoxLayout()

        download_btn = QPushButton("Scarica e installa")
        download_btn.clicked.connect(lambda: self._download_and_install(update_info, dialog))
        buttons_layout.addWidget(download_btn)

        view_github_btn = QPushButton("Vedi su GitHub")
        view_github_btn.clicked.connect(lambda: self._open_github_release(update_info))
        buttons_layout.addWidget(view_github_btn)

        cancel_btn = QPushButton("Annulla")
        cancel_btn.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        dialog.exec_()

    def _download_and_install(self, update_info, parent_dialog):
        """Scarica e installa l'aggiornamento."""
        parent_dialog.close()

        # Progress dialog
        progress = QProgressDialog("Download aggiornamento in corso...", "Annulla", 0, 100, self)
        progress.setWindowTitle("Download")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        def update_progress(downloaded, total):
            if total > 0:
                percent = int((downloaded / total) * 100)
                progress.setValue(percent)
                progress.setLabelText(f"Download: {downloaded // 1024} KB / {total // 1024} KB")
            QApplication.processEvents()

        try:
            # Download
            downloaded_file = download_update(update_info, progress_callback=update_progress)

            progress.close()

            if not downloaded_file:
                QMessageBox.warning(self, "Errore", "Download fallito. Riprova più tardi.")
                return

            # Conferma installazione
            reply = QMessageBox.question(
                self,
                "Installazione",
                f"Download completato!\n\n"
                f"L'applicazione si chiuderà per installare l'aggiornamento.\n"
                f"Verrà riavviata automaticamente dopo l'installazione.\n\n"
                f"Continuare?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                success = install_update(downloaded_file)

                if success:
                    # Chiudi l'applicazione - lo script di update la riavvierà
                    QApplication.quit()
                else:
                    QMessageBox.warning(
                        self,
                        "Errore",
                        "Installazione fallita. Prova a scaricare manualmente da GitHub."
                    )

        except Exception as e:
            progress.close()
            logger.error(f"Errore durante download/install: {e}")
            QMessageBox.warning(
                self,
                "Errore",
                f"Errore durante l'aggiornamento:\n{str(e)}"
            )

    def _open_github_release(self, update_info):
        """Apre la pagina della release su GitHub."""
        import webbrowser
        url = update_info.get('html_url', 'https://github.com/deam411/MangaReader/releases')
        webbrowser.open(url)

    def export_settings(self):
        """Esporta la configurazione corrente in un file JSON."""
        try:
            from PyQt5.QtWidgets import QFileDialog

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
            from PyQt5.QtWidgets import QFileDialog

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

                    # Ricarica i valori nella UI
                    self._load_settings()

                    QMessageBox.information(
                        self,
                        "Import Completato",
                        "Configurazione importata con successo!\n\n"
                        "Le nuove impostazioni sono state applicate."
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
