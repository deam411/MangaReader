"""
Dialog per gestire le impostazioni dell'applicazione.
"""
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFileDialog, QComboBox,
                              QGroupBox, QMessageBox, QTabWidget, QWidget,
                              QCheckBox, QSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal
from .settings import Settings


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

        layout.addWidget(tabs)

        # Pulsanti OK/Cancel/Reset
        buttons_layout = QHBoxLayout()

        reset_button = QPushButton("Ripristina Default")
        reset_button.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(reset_button)

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
            self.accept()
