import sys
import os # Import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QShortcut
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QIcon
from views import LibraryView, MangaView, ReaderView

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def detect_system_theme():
    """Rileva il tema del sistema operativo."""
    try:
        import sys
        if sys.platform == "win32":
            # Su Windows, controlla il registro per il tema
            try:
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize')
                value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
                winreg.CloseKey(key)
                # 0 = dark theme, 1 = light theme
                return "light" if value == 1 else "dark"
            except Exception:
                # Fallback: usa il palette di Qt
                pass

        # Per altri sistemi o se il registro fallisce, usa il palette di Qt
        from PyQt5.QtWidgets import QApplication
        palette = QApplication.palette()
        # Se il colore del testo è chiaro, il tema è scuro
        text_color = palette.color(palette.WindowText)
        is_dark = text_color.lightness() > 128
        return "dark" if is_dark else "light"
    except Exception as e:
        print(f"Errore nel rilevamento del tema di sistema: {e}")
        return "dark"  # Default fallback

def apply_theme_to_app(app):
    """Applica il tema salvato nelle impostazioni all'applicazione."""
    try:
        from src.settings import Settings
        settings = Settings()
        theme = settings.get_theme()

        # Se il tema è "system", rileva il tema del sistema
        if theme == "system":
            theme = detect_system_theme()

        if theme == "dark":
            # Tema scuro
            app.setStyleSheet("""
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QListWidget {
                    background-color: #1e1e1e;
                    border: 1px solid #3d3d3d;
                }
                QPushButton {
                    background-color: #3d3d3d;
                    border: 1px solid #555555;
                    padding: 5px;
                    border-radius: 3px;
                    color: #ffffff;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
                QPushButton:pressed {
                    background-color: #555555;
                }
                QLineEdit {
                    background-color: #3d3d3d;
                    border: 2px solid #555555;
                    padding: 8px;
                    border-radius: 4px;
                    color: #ffffff;
                    selection-background-color: #4a4a4a;
                    selection-color: #ffffff;
                }
                QLineEdit:focus {
                    border: 2px solid #6a6a6a;
                    background-color: #454545;
                }
                QLineEdit::placeholder {
                    color: #aaaaaa;
                }
                QComboBox {
                    background-color: #3d3d3d;
                    border: 2px solid #555555;
                    padding: 6px;
                    padding-right: 25px;
                    border-radius: 4px;
                    color: #ffffff;
                }
                QComboBox:focus {
                    border: 2px solid #6a6a6a;
                }
                QComboBox QAbstractItemView {
                    background-color: #2b2b2b;
                    selection-background-color: #4a4a4a;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QLabel {
                    background-color: transparent;
                    color: #ffffff;
                }
                QGroupBox {
                    background-color: #2b2b2b;
                    border: 1px solid #3d3d3d;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                    color: #ffffff;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #3d3d3d;
                    background-color: #2b2b2b;
                }
                QTabBar::tab {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    padding: 8px 16px;
                    border: 1px solid #555555;
                }
                QTabBar::tab:selected {
                    background-color: #4a4a4a;
                }
                QTabBar::tab:hover {
                    background-color: #4a4a4a;
                }
                QSpinBox {
                    background-color: #3d3d3d;
                    border: 2px solid #555555;
                    padding: 6px;
                    border-radius: 4px;
                    color: #ffffff;
                }
                QSpinBox:focus {
                    border: 2px solid #6a6a6a;
                    background-color: #454545;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    background-color: #4a4a4a;
                    border: 1px solid #555555;
                    width: 16px;
                }
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                    background-color: #555555;
                }
                QCheckBox {
                    color: #ffffff;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    background-color: #1e1e1e;
                }
                QCheckBox::indicator:checked {
                    background-color: #4a4a4a;
                }
                QMessageBox {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMessageBox QLabel {
                    color: #ffffff;
                }
                QMessageBox QPushButton {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    min-width: 60px;
                }
                QScrollArea {
                    background-color: #1e1e1e;
                    border: none;
                }
                QScrollBar:vertical {
                    background-color: #1e1e1e;
                    width: 12px;
                }
                QScrollBar::handle:vertical {
                    background-color: #4a4a4a;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #555555;
                }
            """)
        else:
            # Tema chiaro
            app.setStyleSheet("""
                QWidget {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QDialog {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QListWidget {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #999999;
                    padding: 5px;
                    border-radius: 3px;
                    color: #000000;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QPushButton:pressed {
                    background-color: #c0c0c0;
                }
                QLineEdit {
                    background-color: #ffffff;
                    border: 2px solid #cccccc;
                    padding: 8px;
                    border-radius: 4px;
                    color: #000000;
                    selection-background-color: #0078d7;
                    selection-color: #ffffff;
                }
                QLineEdit:focus {
                    border: 2px solid #0078d7;
                    background-color: #ffffff;
                }
                QLineEdit::placeholder {
                    color: #888888;
                }
                QComboBox {
                    background-color: #ffffff;
                    border: 2px solid #cccccc;
                    padding: 6px;
                    padding-right: 25px;
                    border-radius: 4px;
                    color: #000000;
                }
                QComboBox:focus {
                    border: 2px solid #0078d7;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    selection-background-color: #0078d7;
                    selection-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QLabel {
                    background-color: transparent;
                    color: #000000;
                }
                QGroupBox {
                    background-color: #f0f0f0;
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                    color: #000000;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                    color: #000000;
                }
                QTabWidget::pane {
                    border: 1px solid #cccccc;
                    background-color: #f0f0f0;
                }
                QTabBar::tab {
                    background-color: #e0e0e0;
                    color: #000000;
                    padding: 8px 16px;
                    border: 1px solid #999999;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                }
                QTabBar::tab:hover {
                    background-color: #d0d0d0;
                }
                QSpinBox {
                    background-color: #ffffff;
                    border: 2px solid #cccccc;
                    padding: 6px;
                    border-radius: 4px;
                    color: #000000;
                }
                QSpinBox:focus {
                    border: 2px solid #0078d7;
                    background-color: #ffffff;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    background-color: #e0e0e0;
                    border: 1px solid #999999;
                    width: 16px;
                }
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                    background-color: #d0d0d0;
                }
                QCheckBox {
                    color: #000000;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 1px solid #999999;
                    border-radius: 3px;
                    background-color: #ffffff;
                }
                QCheckBox::indicator:checked {
                    background-color: #d0d0d0;
                }
                QMessageBox {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QMessageBox QLabel {
                    color: #000000;
                }
                QMessageBox QPushButton {
                    background-color: #e0e0e0;
                    color: #000000;
                    min-width: 60px;
                }
                QScrollArea {
                    background-color: #ffffff;
                    border: none;
                }
                QScrollBar:vertical {
                    background-color: #f0f0f0;
                    width: 12px;
                }
                QScrollBar::handle:vertical {
                    background-color: #c0c0c0;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #a0a0a0;
                }
            """)
    except Exception as e:
        print(f"Errore nell'applicazione del tema: {e}")

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
        self.stacked_widget.addWidget(self.library_view)

        self.manga_view = MangaView(self.stacked_widget)
        self.stacked_widget.addWidget(self.manga_view)

        self.reader_view = ReaderView(self.stacked_widget)
        self.stacked_widget.addWidget(self.reader_view)

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
                print(f"Icona non trovata: {icon_path}")
        except Exception as e:
            print(f"Errore nel caricamento dell'icona: {e}")

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

    def go_back(self):
        """Torna alla schermata precedente."""
        current_index = self.stacked_widget.currentIndex()
        if current_index == 2:  # ReaderView -> MangaView
            self.reader_view.back_to_manga_details()
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
