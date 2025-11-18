"""
LibraryController - Business logic per gestione libreria.

Responsabilità:
- Caricamento manga dalla directory
- Callback caricamento manga
- Filtri e ricerca
- Ordinamento
- Popolazione della view
"""

import os
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

from src.paths import get_manga_dir
from src.settings import Settings
from src.database import MangaDatabaseManager
from src.logger import get_logger
from src.views.widgets import LibraryLoaderThread

logger = get_logger(__name__)


class LibraryController:
    """Controller per la gestione della libreria manga."""

    def __init__(self, view):
        """
        Inizializza il controller della libreria.

        Args:
            view: L'istanza di LibraryView da controllare
        """
        self.view = view
        self.settings = Settings()

    def load_library(self):
        """Carica la libreria usando un thread in background."""
        # Previeni caricamenti multipli simultanei (es. F5 premuto ripetutamente)
        if self.view.is_loading:
            logger.debug("Caricamento già in corso, ignorando richiesta")
            return

        self.view.is_loading = True
        self.view.manga_grid_view.clear()
        self.view.all_manga_data = []

        try:
            manga_dir = get_manga_dir()
        except Exception as e:
            self.view.is_loading = False  # Reset flag in caso di errore
            QMessageBox.critical(
                self.view,
                'Errore Directory',
                f'Impossibile accedere alla directory della libreria:\n{str(e)}\n\n'
                'Controlla le impostazioni e assicurati che la directory esista.'
            )
            return

        if not os.path.exists(manga_dir):
            QMessageBox.warning(
                self.view,
                'Directory non trovata',
                f'La directory della libreria non esiste:\n{manga_dir}\n\n'
                'Verrà creata automaticamente.'
            )
            try:
                os.makedirs(manga_dir, exist_ok=True)
            except Exception as e:
                self.view.is_loading = False  # Reset flag in caso di errore
                QMessageBox.critical(
                    self.view,
                    'Errore',
                    f'Impossibile creare la directory:\n{str(e)}'
                )
                return

        # Mostra la progress bar
        self.view.progress_bar.setValue(0)
        self.view.progress_bar.setVisible(True)

        # Avvia il thread di caricamento
        self.view.loader_thread = LibraryLoaderThread(manga_dir)
        self.view.loader_thread.manga_loaded.connect(self.on_manga_loaded)
        self.view.loader_thread.progress_update.connect(self.on_progress_update)
        self.view.loader_thread.loading_complete.connect(self.on_loading_complete)
        self.view.loader_thread.start()

    def on_manga_loaded(self, manga_info):
        """
        Callback quando un manga viene caricato.

        Args:
            manga_info: Dizionario con le informazioni del manga
        """
        self.view.all_manga_data.append(manga_info)
        self._add_manga_to_view(manga_info)

    def on_progress_update(self, current, total):
        """
        Aggiorna la progress bar.

        Args:
            current: Numero di manga caricati
            total: Numero totale di manga da caricare
        """
        if total > 0:
            self.view.progress_bar.setValue(int((current / total) * 100))

    def on_loading_complete(self, corrupted_files):
        """
        Callback quando il caricamento è completato.

        Args:
            corrupted_files: Lista di file corrotti
        """
        # Fix: Pulisci il thread per prevenire memory leak
        if hasattr(self.view, 'loader_thread') and self.view.loader_thread:
            self.view.loader_thread.deleteLater()
            self.view.loader_thread = None

        # Reset flag per permettere un nuovo caricamento
        self.view.is_loading = False

        self.view.progress_bar.setVisible(False)

        # Aggiorna stats widget (v0.3.0)
        self._update_stats()

        # Ottimizzazione: Crea dizionario per lookup O(1) in filter_manga
        self.view.manga_data_map = {manga['file_name']: manga for manga in self.view.all_manga_data}

        # Mostra pulsante Riprendi se c'è almeno un manga in corso
        has_in_progress = any(
            manga.get('progress') and 0 < manga['progress']['percentage'] < 100
            for manga in self.view.all_manga_data
        )
        self.view.resume_button.setVisible(has_in_progress)

        # Popola combobox tag con tutti i tag unici
        self.populate_tag_filter()

        if corrupted_files:
            QMessageBox.warning(
                self.view,
                'File corrotti',
                f'I seguenti file .manga non possono essere caricati:\n\n' +
                '\n'.join(corrupted_files) +
                '\n\nPotrebbero essere corrotti o non validi.'
            )

        self.sort_manga(self.view.sort_combo.currentIndex())

        # Mostra un messaggio se la libreria è vuota (solo al primo caricamento)
        if len(self.view.all_manga_data) == 0 and self.view.first_load:
            self.view.first_load = False
            QMessageBox.information(
                self.view,
                'Libreria vuota',
                'La libreria è vuota!\n\n'
                'Puoi:\n'
                '• Importare file .manga esistenti (pulsante  o Ctrl+I)\n'
                '• Creare un nuovo manga (pulsante + o Ctrl+N)\n'
                '• Cambiare la directory della libreria nelle Impostazioni\n\n'
                f'Directory corrente: {get_manga_dir()}'
            )

    def _add_manga_to_view(self, manga_info):
        """
        Aggiunge un singolo manga alla vista.

        Args:
            manga_info: Dizionario con le informazioni del manga
        """
        from PyQt5.QtWidgets import QListWidgetItem

        item = QListWidgetItem(manga_info['title'])
        item.setData(Qt.UserRole, manga_info['file_name'])
        item.setData(Qt.UserRole + 1, manga_info['description'])
        item.setData(Qt.UserRole + 2, manga_info.get('progress'))  # Progresso di lettura
        if manga_info['cover']:
            item.setData(Qt.DecorationRole, manga_info['cover'])
        self.view.manga_grid_view.addItem(item)

    def populate_view(self, data_list):
        """
        Popola la vista con una lista di manga.

        Args:
            data_list: Lista di dizionari con informazioni sui manga
        """
        self.view.manga_grid_view.clear()
        for manga_info in data_list:
            self._add_manga_to_view(manga_info)

    def filter_manga(self, text=None):
        """
        Filtra i manga per testo, tag, stato e autore (v0.3.0 enhanced).

        Args:
            text: Testo di ricerca (non usato direttamente, viene letto dalla view)
        """
        search_text = self.view.search_input.text().lower()
        selected_tag = self.view.tag_filter_combo.currentText()
        selected_status = self.view.status_filter_combo.currentText() if hasattr(self.view, 'status_filter_combo') else "Tutti"
        selected_author = self.view.author_filter_combo.currentText() if hasattr(self.view, 'author_filter_combo') else "Tutti gli autori"

        # Ottimizzazione: Usa il dizionario per lookup O(1) invece di loop O(n)
        if not hasattr(self.view, 'manga_data_map'):
            self.view.manga_data_map = {manga['file_name']: manga for manga in self.view.all_manga_data}

        for i in range(self.view.manga_grid_view.count()):
            item = self.view.manga_grid_view.item(i)
            manga_title = item.text().lower()
            file_name = item.data(Qt.UserRole)

            # Ottieni i dati del manga con lookup O(1)
            manga_data = self.view.manga_data_map.get(file_name)

            # Filtro testo
            text_match = search_text in manga_title
            if manga_data and 'author' in manga_data:
                text_match = text_match or search_text in manga_data['author'].lower()

            # Filtro tag
            tag_match = True
            if selected_tag and selected_tag != "All Tags":
                if manga_data and 'tags' in manga_data:
                    manga_tags = [t.strip() for t in manga_data['tags'].split(',') if t.strip()]
                    tag_match = selected_tag in manga_tags
                else:
                    tag_match = False

            # Filtro stato lettura (v0.3.0)
            status_match = True
            if selected_status != "Tutti":
                progress = manga_data.get('progress') if manga_data else None
                if selected_status == "Non letti":
                    status_match = not progress or progress['percentage'] == 0
                elif selected_status == "In lettura":
                    status_match = progress and 0 < progress['percentage'] < 100
                elif selected_status == "Completati":
                    status_match = progress and progress['percentage'] >= 100

            # Filtro autore (v0.3.0)
            author_match = True
            if selected_author and selected_author != "Tutti gli autori":
                if manga_data and 'author' in manga_data:
                    author_match = manga_data['author'] == selected_author
                else:
                    author_match = False

            # Mostra solo se tutti i filtri passano
            item.setHidden(not (text_match and tag_match and status_match and author_match))

    def sort_manga(self, index):
        """
        Ordina i manga in base all'indice selezionato.

        Args:
            index: Indice dell'ordinamento (0=Title A-Z, 1=Title Z-A, 2=Author A-Z, 3=Author Z-A)
        """
        if index == 0:
            self.view.all_manga_data.sort(key=lambda x: x['title'] if x['title'] else '', reverse=False)
        elif index == 1:
            self.view.all_manga_data.sort(key=lambda x: x['title'] if x['title'] else '', reverse=True)
        elif index == 2:
            self.view.all_manga_data.sort(key=lambda x: x['author'] if x['author'] else '', reverse=False)
        elif index == 3:
            self.view.all_manga_data.sort(key=lambda x: x['author'] if x['author'] else '', reverse=True)
        self.populate_view(self.view.all_manga_data)

    def populate_tag_filter(self):
        """Popola la combobox tag e autori con tutti i valori unici dalla libreria (v0.3.0)."""
        all_tags = set()
        all_authors = set()

        for manga in self.view.all_manga_data:
            if 'tags' in manga and manga['tags']:
                tags = [t.strip() for t in manga['tags'].split(',') if t.strip()]
                all_tags.update(tags)

            if 'author' in manga and manga['author'] and manga['author'] != 'Sconosciuto':
                all_authors.add(manga['author'])

        # Salva selezioni correnti
        current_tag_selection = self.view.tag_filter_combo.currentText()
        current_author_selection = self.view.author_filter_combo.currentText()

        # Aggiorna la combobox tag
        self.view.tag_filter_combo.clear()
        self.view.tag_filter_combo.addItem("All Tags")

        for tag in sorted(all_tags):
            self.view.tag_filter_combo.addItem(tag)

        # Ripristina selezione tag se possibile
        index = self.view.tag_filter_combo.findText(current_tag_selection)
        if index >= 0:
            self.view.tag_filter_combo.setCurrentIndex(index)

        # Aggiorna la combobox autori (v0.3.0)
        self.view.author_filter_combo.clear()
        self.view.author_filter_combo.addItem("Tutti gli autori")

        for author in sorted(all_authors):
            self.view.author_filter_combo.addItem(author)

        # Ripristina selezione autore se possibile
        index = self.view.author_filter_combo.findText(current_author_selection)
        if index >= 0:
            self.view.author_filter_combo.setCurrentIndex(index)

    def _update_stats(self):
        """Aggiorna il widget statistiche con i dati correnti (v0.3.0)."""
        total = len(self.view.all_manga_data)
        completed = sum(1 for m in self.view.all_manga_data
                       if m.get('progress') and m['progress']['percentage'] >= 100)
        reading = sum(1 for m in self.view.all_manga_data
                     if m.get('progress') and 0 < m['progress']['percentage'] < 100)
        unread = total - completed - reading

        self.view.stats_widget.update_stats(total, completed, reading, unread)

    def clear_manga_history(self, manga_file, item):
        """
        Cancella la cronologia di lettura per un manga.

        Args:
            manga_file: Percorso del file .manga
            item: QListWidgetItem del manga nella view
        """
        try:
            db_manager = MangaDatabaseManager(manga_file)
            db_manager.clear_reading_history()

            # Aggiorna i dati del manga nella lista
            # Rimuovi il progresso
            for manga_info in self.view.all_manga_data:
                if manga_info['file_name'] == manga_file:
                    manga_info['progress'] = None
                    break

            # Aggiorna l'item nella vista
            item.setData(Qt.UserRole + 2, None)

            # Forza il ridisegno dell'item
            self.view.manga_grid_view.update(self.view.manga_grid_view.indexFromItem(item))

            # Aggiorna la visibilità del pulsante Riprendi
            has_in_progress = any(
                manga.get('progress') and 0 < manga['progress']['percentage'] < 100
                for manga in self.view.all_manga_data
            )
            self.view.resume_button.setVisible(has_in_progress)

            QMessageBox.information(
                self.view,
                'Cronologia cancellata',
                'La cronologia di lettura è stata cancellata con successo.'
            )

        except Exception as e:
            QMessageBox.critical(
                self.view,
                'Errore',
                f'Errore durante la cancellazione della cronologia: {str(e)}'
            )
