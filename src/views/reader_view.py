"""
ReaderView - Vista lettore manga.

Gestisce:
- Visualizzazione pagine manga con scrolling
- Navigazione tra capitoli
- Segnalibri
- Vista doppia pagina
- Zoom e pan
"""

import os
import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
                              QScrollArea, QMessageBox, QProgressBar, QDialog)
from PyQt5.QtGui import QPixmap, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer, QRect

from src.database import MangaDatabaseManager, StatisticsManager
from src.logger import get_logger
from src.settings import Settings
from src.chapter_reader_window import PageDisplayWidget
from src.views.dialogs import BookmarkDialog

logger = get_logger(__name__)

class ReaderView(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.db_conn = None
        self.manga_file = None
        self.current_chapter_id = None
        self.db_manager = None
        self.statistics_manager = None
        self.current_session_id = None
        self.session_start_page = None
        self.settings = Settings()  # Per accedere alle impostazioni di sfondo
        self.opened_from_resume = False  # Flag per sapere se aperto da "Riprendi Lettura"

        # Timer per auto-save posizione lettura ogni 30 secondi
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave_reading_position)
        self.autosave_timer.setInterval(30000)  # 30 secondi

        self.initUI()
        self.apply_background_settings()  # Applica sfondo personalizzato reader

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Progress bar per il caricamento
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMaximumHeight(10)  # Rendi la barra più sottile
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center;
                background-color: #2b2b2b;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #4a9eff !important;
                border-radius: 4px;
            }
        """)
        # Forza il colore resettando la palette
        palette = self.progress_bar.palette()
        palette.setColor(QPalette.Highlight, QColor(74, 158, 255))
        self.progress_bar.setPalette(palette)
        main_layout.addWidget(self.progress_bar)

        self.scroll_area = QScrollArea(self)
        main_layout.addWidget(self.scroll_area)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.verticalScrollBar().setFocusPolicy(Qt.NoFocus)
        self.scroll_area.horizontalScrollBar().setFocusPolicy(Qt.NoFocus)
        self.scroll_area.installEventFilter(self)

        self.page_display_widget = PageDisplayWidget()
        self.scroll_area.setWidget(self.page_display_widget)

    def _cleanup_connections(self):
        """Chiude in modo sicuro le connessioni database e termina sessione statistiche."""
        self.autosave_timer.stop()

        # Termina sessione statistiche se attiva
        if self.statistics_manager and self.current_session_id:
            try:
                current_page = self.get_current_page_number()
                pages_read = max(0, current_page - self.session_start_page + 1) if self.session_start_page else 0
                self.statistics_manager.end_reading_session(
                    session_id=self.current_session_id,
                    end_chapter_id=self.current_chapter_id,
                    total_pages_read=pages_read
                )
                logger.debug(f"Cleanup: Ended reading session {self.current_session_id}")
            except Exception as e:
                logger.warning(f"Error ending statistics session: {e}")
            finally:
                self.current_session_id = None
                self.statistics_manager = None

        if self.db_conn:
            try:
                self.db_conn.close()
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")
            finally:
                self.db_conn = None
        if self.db_manager:
            try:
                self.db_manager.close()
            except Exception as e:
                logger.warning(f"Error closing database manager: {e}")
            finally:
                self.db_manager = None

    def closeEvent(self, event):
        """Chiudi le connessioni database quando il widget viene distrutto."""
        self._cleanup_connections()
        super().closeEvent(event)

    def hideEvent(self, event):
        """Fix: Chiudi le connessioni database e ferma il timer quando la view viene nascosta."""
        self._cleanup_connections()
        super().hideEvent(event)

    def load_chapter(self, manga_file, chapter_id, from_resume=False):
        """Carica i metadati del volume per caricamento on-demand."""
        self._cleanup_connections()

        self.manga_file = manga_file
        self.current_chapter_id = chapter_id
        self.opened_from_resume = from_resume  # Salva da dove è stato aperto
        try:
            self.db_conn = sqlite3.connect(manga_file)
            self.db_conn.row_factory = sqlite3.Row

            # Inizializza database manager per storia lettura
            self.db_manager = MangaDatabaseManager(manga_file)

            # Inizializza statistics manager e avvia sessione di lettura
            self.statistics_manager = StatisticsManager(manga_file)
            self.session_start_page = 1  # Inizia sempre dalla pagina 1
            self.current_session_id = self.statistics_manager.start_reading_session(
                chapter_id=chapter_id,
                page_number=self.session_start_page
            )
            logger.debug(f"Started reading session {self.current_session_id} for chapter {chapter_id}")

            # Avvia timer auto-save
            self.autosave_timer.start()

            cursor = self.db_conn.cursor()

            # Trova il volume_id del capitolo selezionato
            cursor.execute("SELECT volume_id FROM chapters WHERE id = ?", (chapter_id,))
            chapter_info = cursor.fetchone()

            if not chapter_info:
                return

            volume_id = chapter_info['volume_id']

            # Carica tutti i capitoli del volume in ordine
            cursor.execute("SELECT id, name FROM chapters WHERE volume_id = ? ORDER BY `order`", (volume_id,))
            all_chapters = cursor.fetchall()

            # Trova l'indice del capitolo selezionato
            # Converti entrambi a int per garantire il match corretto
            chapter_ids = [int(ch['id']) for ch in all_chapters]
            try:
                start_index = chapter_ids.index(int(chapter_id))
            except ValueError:
                logger.warning(f"Chapter ID {chapter_id} not found in volume chapters {chapter_ids}")
                start_index = 0

            # Crea una lista di metadati per ogni pagina (tutti i capitoli del volume)
            page_metadata = []
            selected_chapter_page_index = 0  # Indice della prima pagina del capitolo selezionato

            for i in range(0, len(all_chapters)):  # Carica TUTTI i capitoli dall'inizio
                chapter = all_chapters[i]

                # Aggiungi separatore (tranne per il primo capitolo)
                if i > 0:
                    page_metadata.append({
                        'type': 'separator',
                        'chapter_name': chapter['name'],
                        'chapter_id': None,
                        'page_number': None
                    })

                # Se questo è il capitolo selezionato, salva l'indice della sua prima pagina
                if i == start_index:
                    selected_chapter_page_index = len(page_metadata)

                # Conta le pagine del capitolo
                cursor.execute("SELECT COUNT(*) as count FROM pages WHERE chapter_id = ?", (chapter['id'],))
                page_count = cursor.fetchone()['count']

                # Aggiungi metadati per ogni pagina
                for page_num in range(1, page_count + 1):
                    page_metadata.append({
                        'type': 'page',
                        'chapter_id': chapter['id'],
                        'page_number': page_num,
                        'chapter_name': chapter['name']
                    })

            # Passa i metadati al widget con il database
            self.page_display_widget.set_pages_metadata(page_metadata, self.db_conn)

            # Scrolla alla prima pagina del capitolo selezionato
            if selected_chapter_page_index > 0:
                QTimer.singleShot(100, lambda: self.scroll_to_page_index(selected_chapter_page_index))

            self.progress_bar.setVisible(False)
        except Exception as e:
            logger.error(f"Error loading chapter {chapter_id} from {manga_file}: {e}")
            self._cleanup_connections()
            raise

    def scroll_to_page_index(self, page_index):
        """Scrolla la scroll area alla pagina specificata."""
        # Verifica che l'indice sia valido
        if page_index < 0 or page_index >= len(self.page_display_widget.page_positions):
            return

        # Ottieni la posizione della pagina
        page_rect = self.page_display_widget.page_positions[page_index]

        # Scrolla alla posizione Y della pagina
        self.scroll_area.verticalScrollBar().setValue(page_rect.y())

    def autosave_reading_position(self):
        """Salva automaticamente la posizione di lettura corrente e aggiorna statistiche."""
        if not self.db_manager or not self.current_chapter_id:
            return

        # Calcola la pagina corrente basandosi sulla posizione di scroll
        current_page = self.get_current_page_number()

        if current_page > 0:
            self.db_manager.save_reading_position(self.current_chapter_id, current_page)

            # Aggiorna sessione statistiche se attiva
            if self.statistics_manager and self.current_session_id and self.session_start_page:
                # Calcola pagine lette in questa sessione
                pages_read = max(0, current_page - self.session_start_page + 1)
                self.statistics_manager.update_reading_session(
                    session_id=self.current_session_id,
                    current_chapter_id=self.current_chapter_id,
                    pages_read=pages_read
                )

    def get_current_page_number(self):
        """Determina il numero della pagina attualmente visibile."""
        if not self.page_display_widget or not self.page_display_widget.page_positions:
            return 1

        # Ottieni la posizione di scroll corrente
        scroll_pos = self.scroll_area.verticalScrollBar().value()

        # Trova la pagina più vicina alla posizione di scroll corrente
        page_positions = self.page_display_widget.page_positions
        for page_index, page_rect in enumerate(page_positions):
            # page_rect è un QRect, quindi usiamo .y() per ottenere la posizione Y
            if page_rect.y() > scroll_pos:
                # Restituisci la pagina precedente (quella attualmente visibile)
                return max(1, page_index)

        # Se siamo oltre l'ultima pagina, restituisci l'ultima
        return len(page_positions)

    def back_to_manga_details(self):
        # Salva posizione prima di uscire
        self.autosave_reading_position()

        # Termina sessione statistiche se attiva
        if self.statistics_manager and self.current_session_id:
            current_page = self.get_current_page_number()
            pages_read = max(0, current_page - self.session_start_page + 1) if self.session_start_page else 0
            self.statistics_manager.end_reading_session(
                session_id=self.current_session_id,
                end_chapter_id=self.current_chapter_id,
                total_pages_read=pages_read
            )
            logger.debug(f"Ended reading session {self.current_session_id}, pages read: {pages_read}")
            self.current_session_id = None

        # Ferma timer auto-save
        self.autosave_timer.stop()

        # Pulisce la cache del widget
        self.page_display_widget.loaded_pages_cache.clear()
        self.page_display_widget.image_cache.clear()

        # Se aperto da "Riprendi Lettura", torna alla libreria invece che al volume
        if self.opened_from_resume:
            self.opened_from_resume = False  # Reset flag
            self.stacked_widget.setCurrentIndex(0)  # Torna alla LibraryView
        else:
            self.stacked_widget.setCurrentIndex(2)  # Torna alla VolumeView

    def eventFilter(self, obj, event):
        """Intercetta gli eventi della scroll area per gestire ESC."""
        if event.type() == event.KeyPress:
            if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Backspace:
                self.back_to_manga_details()
                return True
        return super().eventFilter(obj, event)

    def toggle_view_mode(self):
        """Alterna tra vista singola e doppia pagina."""
        if hasattr(self.page_display_widget, 'toggle_view_mode'):
            new_mode = self.page_display_widget.toggle_view_mode()
            # Opzionale: mostra messaggio temporaneo all'utente
            mode_text = "Doppia Pagina" if new_mode == "double" else "Singola Pagina"
            logger.info(f"Modalità vista cambiata: {mode_text}")

    def add_bookmark(self):
        """Aggiunge un segnalibro alla posizione corrente."""
        if not self.db_manager or not self.current_chapter_id:
            QMessageBox.warning(self, "Errore", "Impossibile aggiungere segnalibro: nessun capitolo caricato.")
            return

        # Ottieni pagina corrente
        current_page = self.get_current_page_number()

        # Genera nome default con timestamp
        import datetime
        default_name = f"Segnalibro {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"

        # Mostra dialog per nome
        dialog = BookmarkDialog(title="Nuovo Segnalibro", default_name=default_name, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            bookmark_name = dialog.get_name()
            if bookmark_name:
                bookmark_id = self.db_manager.add_bookmark(
                    self.current_chapter_id,
                    current_page,
                    bookmark_name
                )
                if bookmark_id > 0:
                    QMessageBox.information(
                        self,
                        "Segnalibro Aggiunto",
                        f"Segnalibro '{bookmark_name}' aggiunto alla pagina {current_page}"
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Errore",
                        "Impossibile aggiungere il segnalibro. Controlla i log per dettagli."
                    )

    def keyPressEvent(self, event):
        """Gestisce ESC, Backspace e shortcut speciali."""
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Backspace:
            self.back_to_manga_details()
        elif event.key() == Qt.Key_N and event.modifiers() == Qt.ControlModifier:
            # Ctrl+N: Toggle filtro luce blu (night mode)
            enabled = self.page_display_widget.toggle_blue_light_filter()
            status = "attivato" if enabled else "disattivato"
            logger.info(f"Filtro luce blu {status}")
        else:
            super().keyPressEvent(event)

    def apply_background_settings(self):
        """
        Applica le impostazioni di sfondo personalizzato al ReaderView.

        Legge da reader.background_color e applica il colore di sfondo
        allo scroll_area (area di visualizzazione pagine manga).
        """
        # Leggi impostazione colore sfondo
        bg_color = self.settings.get("reader.background_color", None)

        # Applica colore di sfondo se presente
        if bg_color:
            stylesheet = f"""
                QScrollArea {{
                    background-color: {bg_color};
                }}
            """
            self.scroll_area.setStyleSheet(stylesheet)
            logger.info(f"Applied reader background color: {bg_color}")
        else:
            # Reset stylesheet se non c'è colore
            self.scroll_area.setStyleSheet("")
            logger.debug("No reader background color set")
