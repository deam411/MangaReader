import sys
import os # Import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QShortcut
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QIcon
from views import LibraryView, MangaView, VolumeView, ReaderView
from src.theme_manager import apply_theme
from src.logger import get_logger

logger = get_logger(__name__)

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def apply_theme_to_app(app):
    """
    Applica il tema salvato nelle impostazioni all'applicazione.

    Questa è una funzione wrapper che delega al theme_manager per
    mantenere la compatibilità con il codice esistente.
    """
    apply_theme(app)

class MangaReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Manga Reader')
        self.setGeometry(100, 100, 1200, 800)

        # Imposta l'icona della finestra
        self.set_window_icon()

        self.showFullScreen()

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.library_view = LibraryView(self.stacked_widget)
        self.stacked_widget.addWidget(self.library_view)  # Index 0

        self.manga_view = MangaView(self.stacked_widget)
        self.stacked_widget.addWidget(self.manga_view)  # Index 1

        self.volume_view = VolumeView(self.stacked_widget)
        self.stacked_widget.addWidget(self.volume_view)  # Index 2

        self.reader_view = ReaderView(self.stacked_widget)
        self.stacked_widget.addWidget(self.reader_view)  # Index 3

        self.setup_shortcuts()

    def set_window_icon(self):
        """Imposta l'icona della finestra e della taskbar."""
        try:
            # Determina il percorso dell'icona
            if getattr(sys, 'frozen', False):
                # Se siamo in un eseguibile compilato
                base_path = sys._MEIPASS
            else:
                # Se siamo in sviluppo
                base_path = os.path.dirname(os.path.abspath(__file__))

            icon_path = os.path.join(base_path, 'assets', 'icon.ico')

            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.setWindowIcon(icon)
                # Imposta anche l'icona dell'applicazione per la taskbar
                QApplication.instance().setWindowIcon(icon)
            else:
                # Fix: Usa logger invece di print
                logger.warning(f"Icona non trovata: {icon_path}")
        except Exception as e:
            # Fix: Usa logger invece di print
            logger.error(f"Errore nel caricamento dell'icona: {e}")

    def setup_shortcuts(self):
        """Configura le scorciatoie da tastiera globali."""
        # Ctrl+F per focus sulla ricerca
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self.focus_search)

        # Ctrl+I per import
        import_shortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        import_shortcut.activated.connect(self.trigger_import)

        # Ctrl+E per export
        export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        export_shortcut.activated.connect(self.trigger_export)

        # Ctrl+N per nuovo manga
        new_manga_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_manga_shortcut.activated.connect(self.trigger_new_manga)

        # F5 per refresh
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.trigger_refresh)

        # F11 per fullscreen toggle
        fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        fullscreen_shortcut.activated.connect(self.toggle_fullscreen)

        # Backspace per tornare indietro
        back_shortcut = QShortcut(QKeySequence("Backspace"), self)
        back_shortcut.activated.connect(self.go_back)

        # Ctrl+D per toggle vista doppia pagina
        toggle_view_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        toggle_view_shortcut.activated.connect(self.toggle_double_page_view)

        # Ctrl+B per aggiungere segnalibro
        bookmark_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        bookmark_shortcut.activated.connect(self.add_bookmark)

        # F1 per mostrare pannello scorciatoie
        help_shortcut = QShortcut(QKeySequence("F1"), self)
        help_shortcut.activated.connect(self.show_shortcuts_dialog)

    def show_shortcuts_dialog(self):
        """Mostra il dialog con tutte le scorciatoie."""
        from views import ShortcutsDialog
        dialog = ShortcutsDialog(self)
        dialog.exec_()

    def focus_search(self):
        """Mette il focus sulla barra di ricerca se siamo nella library view."""
        if self.stacked_widget.currentIndex() == 0:
            self.library_view.search_input.setFocus()
            self.library_view.search_input.selectAll()

    def trigger_import(self):
        """Trigger dell'import se siamo nella library view."""
        if self.stacked_widget.currentIndex() == 0:
            self.library_view.import_manga()

    def trigger_export(self):
        """Trigger dell'export se siamo nella library view."""
        if self.stacked_widget.currentIndex() == 0:
            self.library_view.export_manga()

    def trigger_new_manga(self):
        """Trigger della creazione nuovo manga se siamo nella library view."""
        if self.stacked_widget.currentIndex() == 0:
            self.library_view.launch_manga_creator()

    def trigger_refresh(self):
        """Refresh della library view."""
        if self.stacked_widget.currentIndex() == 0:
            self.library_view.load_library()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def toggle_double_page_view(self):
        """Toggle vista doppia pagina se siamo nella reader view."""
        if self.stacked_widget.currentIndex() == 3:  # ReaderView
            self.reader_view.toggle_view_mode()

    def add_bookmark(self):
        """Aggiunge segnalibro se siamo nella reader view."""
        if self.stacked_widget.currentIndex() == 3:  # ReaderView
            self.reader_view.add_bookmark()

    def go_back(self):
        """Torna alla schermata precedente."""
        current_index = self.stacked_widget.currentIndex()
        if current_index == 3:  # ReaderView -> VolumeView
            self.reader_view.back_to_manga_details()
        elif current_index == 2:  # VolumeView -> MangaView
            self.volume_view.back_to_manga()
        elif current_index == 1:  # MangaView -> LibraryView
            self.manga_view.back_to_library()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Applica il tema salvato all'avvio
    apply_theme_to_app(app)

    ex = MangaReader()
    ex.show()
    sys.exit(app.exec_())
