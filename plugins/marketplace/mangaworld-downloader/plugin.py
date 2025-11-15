"""
MangaWorld Downloader Plugin

Plugin per scaricare manga da MangaWorld (mangaworld.ac)
"""

import os
import re
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QLabel, QProgressBar, QMessageBox, QListWidgetItem,
    QComboBox, QTextEdit
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap

from plugins.plugin_base import PluginBase
from src.logger import get_logger
from src.database.manga_manager import MangaManager
from src.database.chapter_manager import ChapterManager

logger = get_logger(__name__)


class MangaWorldSearchWorker(QThread):
    """Worker thread per la ricerca manga."""

    search_complete = pyqtSignal(list)
    search_error = pyqtSignal(str)

    def __init__(self, query: str):
        super().__init__()
        self.query = query
        self.base_url = "https://www.mangaworld.ac"

    def run(self):
        """Esegue la ricerca."""
        try:
            # Cerca manga usando l'API di ricerca di MangaWorld
            search_url = f"{self.base_url}/archive?keyword={urllib.parse.quote(self.query)}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            request = urllib.request.Request(search_url, headers=headers)

            with urllib.request.urlopen(request, timeout=10) as response:
                html = response.read().decode('utf-8')

            # Parse risultati (semplificato - in produzione usare BeautifulSoup)
            results = []

            # Cerca pattern per i manga
            # Pattern: <a href="/manga/123/nome-manga" class="manga-link">
            pattern = r'href="(/manga/\d+/[^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html)

            for url, title in matches[:20]:  # Limita a 20 risultati
                results.append({
                    'title': title.strip(),
                    'url': self.base_url + url,
                    'id': url.split('/')[2]
                })

            self.search_complete.emit(results)

        except Exception as e:
            logger.error(f"Error searching MangaWorld: {e}")
            self.search_error.emit(str(e))


class MangaWorldChapterWorker(QThread):
    """Worker thread per ottenere lista capitoli."""

    chapters_loaded = pyqtSignal(list)
    chapters_error = pyqtSignal(str)

    def __init__(self, manga_url: str):
        super().__init__()
        self.manga_url = manga_url

    def run(self):
        """Carica lista capitoli."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            request = urllib.request.Request(self.manga_url, headers=headers)

            with urllib.request.urlopen(request, timeout=10) as response:
                html = response.read().decode('utf-8')

            chapters = []

            # Cerca capitoli (pattern semplificato)
            # In produzione, usare BeautifulSoup per parsing robusto
            pattern = r'href="(/manga/\d+/[^/]+/read/([^"]+))"[^>]*>Capitolo ([^<]+)</a>'
            matches = re.findall(pattern, html)

            for url, chapter_id, chapter_num in matches:
                chapters.append({
                    'number': chapter_num.strip(),
                    'url': self.manga_url.split('/manga')[0] + url,
                    'id': chapter_id
                })

            # Ordina per numero capitolo
            chapters.reverse()

            self.chapters_loaded.emit(chapters)

        except Exception as e:
            logger.error(f"Error loading chapters: {e}")
            self.chapters_error.emit(str(e))


class MangaWorldDownloadWorker(QThread):
    """Worker thread per download capitolo."""

    progress = pyqtSignal(int, int, str)
    download_complete = pyqtSignal(str, list)
    download_error = pyqtSignal(str)

    def __init__(self, chapter_url: str, chapter_number: str):
        super().__init__()
        self.chapter_url = chapter_url
        self.chapter_number = chapter_number

    def run(self):
        """Scarica capitolo."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # Carica pagina capitolo
            request = urllib.request.Request(self.chapter_url, headers=headers)

            with urllib.request.urlopen(request, timeout=10) as response:
                html = response.read().decode('utf-8')

            # Trova immagini delle pagine
            # Pattern semplificato - in produzione usare BeautifulSoup
            image_pattern = r'<img[^>]*src="(https://[^"]*mangaworld[^"]*\.(jpg|png|jpeg))"'
            image_urls = re.findall(image_pattern, html)

            if not image_urls:
                # Prova pattern alternativo
                image_pattern = r'"(https://cdn\.mangaworld[^"]*\.(jpg|png|jpeg))"'
                image_urls = re.findall(image_pattern, html)

            if not image_urls:
                raise Exception("Nessuna immagine trovata nel capitolo")

            # Scarica immagini
            pages_data = []
            total_pages = len(image_urls)

            for idx, (img_url, _) in enumerate(image_urls):
                self.progress.emit(idx + 1, total_pages, f"Scaricando pagina {idx + 1}/{total_pages}")

                img_request = urllib.request.Request(img_url, headers=headers)

                with urllib.request.urlopen(img_request, timeout=15) as img_response:
                    image_data = img_response.read()
                    pages_data.append(image_data)

            self.download_complete.emit(self.chapter_number, pages_data)

        except Exception as e:
            logger.error(f"Error downloading chapter: {e}")
            self.download_error.emit(str(e))


class MangaWorldDownloaderDialog(QDialog):
    """Dialog per scaricare manga da MangaWorld."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MangaWorld Downloader")
        self.setMinimumSize(800, 600)

        self.manga_manager = MangaManager()
        self.chapter_manager = ChapterManager()

        self.current_manga_url = None
        self.current_manga_title = None
        self.current_manga_file = None

        self.setup_ui()

    def setup_ui(self):
        """Configura l'interfaccia."""
        layout = QVBoxLayout(self)

        # Sezione ricerca
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Cerca manga:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Inserisci nome manga...")
        self.search_input.returnPressed.connect(self.search_manga)
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Cerca")
        self.search_button.clicked.connect(self.search_manga)
        search_layout.addWidget(self.search_button)

        layout.addLayout(search_layout)

        # Lista risultati ricerca
        layout.addWidget(QLabel("📚 Risultati:"))
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.on_manga_selected)
        layout.addWidget(self.results_list)

        # Lista capitoli
        layout.addWidget(QLabel("📖 Capitoli disponibili:"))
        self.chapters_list = QListWidget()
        self.chapters_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.chapters_list)

        # Sezione download
        download_layout = QHBoxLayout()

        self.download_button = QPushButton("⬇️ Scarica Selezionati")
        self.download_button.clicked.connect(self.download_selected_chapters)
        self.download_button.setEnabled(False)
        download_layout.addWidget(self.download_button)

        self.download_all_button = QPushButton("⬇️ Scarica Tutti")
        self.download_all_button.clicked.connect(self.download_all_chapters)
        self.download_all_button.setEnabled(False)
        download_layout.addWidget(self.download_all_button)

        layout.addLayout(download_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    def search_manga(self):
        """Cerca manga su MangaWorld."""
        query = self.search_input.text().strip()
        if not query:
            return

        self.search_button.setEnabled(False)
        self.results_list.clear()
        self.status_label.setText("🔍 Ricerca in corso...")

        self.search_worker = MangaWorldSearchWorker(query)
        self.search_worker.search_complete.connect(self.on_search_complete)
        self.search_worker.search_error.connect(self.on_search_error)
        self.search_worker.start()

    def on_search_complete(self, results: List[Dict]):
        """Chiamato quando la ricerca è completata."""
        self.search_button.setEnabled(True)

        if not results:
            self.status_label.setText("❌ Nessun risultato trovato")
            return

        self.status_label.setText(f"✅ Trovati {len(results)} manga")

        for manga in results:
            item = QListWidgetItem(manga['title'])
            item.setData(Qt.UserRole, manga)
            self.results_list.addItem(item)

    def on_search_error(self, error: str):
        """Chiamato in caso di errore nella ricerca."""
        self.search_button.setEnabled(True)
        self.status_label.setText(f"❌ Errore: {error}")
        QMessageBox.warning(self, "Errore", f"Errore durante la ricerca:\n{error}")

    def on_manga_selected(self, item: QListWidgetItem):
        """Chiamato quando un manga viene selezionato."""
        manga = item.data(Qt.UserRole)
        self.current_manga_url = manga['url']
        self.current_manga_title = manga['title']

        self.chapters_list.clear()
        self.download_button.setEnabled(False)
        self.download_all_button.setEnabled(False)
        self.status_label.setText(f"📖 Caricamento capitoli di '{manga['title']}'...")

        # Carica capitoli
        self.chapters_worker = MangaWorldChapterWorker(manga['url'])
        self.chapters_worker.chapters_loaded.connect(self.on_chapters_loaded)
        self.chapters_worker.chapters_error.connect(self.on_chapters_error)
        self.chapters_worker.start()

    def on_chapters_loaded(self, chapters: List[Dict]):
        """Chiamato quando i capitoli sono stati caricati."""
        if not chapters:
            self.status_label.setText("❌ Nessun capitolo trovato")
            return

        self.status_label.setText(f"✅ Trovati {len(chapters)} capitoli")

        for chapter in chapters:
            item = QListWidgetItem(f"Capitolo {chapter['number']}")
            item.setData(Qt.UserRole, chapter)
            self.chapters_list.addItem(item)

        self.download_button.setEnabled(True)
        self.download_all_button.setEnabled(True)

    def on_chapters_error(self, error: str):
        """Chiamato in caso di errore nel caricamento capitoli."""
        self.status_label.setText(f"❌ Errore: {error}")
        QMessageBox.warning(self, "Errore", f"Errore caricando capitoli:\n{error}")

    def download_selected_chapters(self):
        """Scarica i capitoli selezionati."""
        selected = self.chapters_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un capitolo")
            return

        self.download_chapters([item.data(Qt.UserRole) for item in selected])

    def download_all_chapters(self):
        """Scarica tutti i capitoli."""
        chapters = [self.chapters_list.item(i).data(Qt.UserRole)
                   for i in range(self.chapters_list.count())]
        self.download_chapters(chapters)

    def download_chapters(self, chapters: List[Dict]):
        """Scarica i capitoli specificati."""
        if not chapters:
            return

        # Crea o trova il manga nel database
        if not self.current_manga_file:
            manga_file = self.manga_manager.create_manga(
                title=self.current_manga_title,
                author="MangaWorld",
                status="ongoing"
            )
            self.current_manga_file = manga_file

        self.download_button.setEnabled(False)
        self.download_all_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(chapters))
        self.progress_bar.setValue(0)

        self.chapters_to_download = chapters
        self.current_chapter_idx = 0

        self.download_next_chapter()

    def download_next_chapter(self):
        """Scarica il prossimo capitolo nella coda."""
        if self.current_chapter_idx >= len(self.chapters_to_download):
            # Tutti i capitoli scaricati
            self.progress_bar.setVisible(False)
            self.download_button.setEnabled(True)
            self.download_all_button.setEnabled(True)
            self.status_label.setText("✅ Download completato!")
            QMessageBox.information(self, "Completato", "Tutti i capitoli sono stati scaricati!")
            return

        chapter = self.chapters_to_download[self.current_chapter_idx]

        self.status_label.setText(f"⬇️ Scaricando capitolo {chapter['number']}...")

        self.download_worker = MangaWorldDownloadWorker(chapter['url'], chapter['number'])
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.download_complete.connect(self.on_chapter_downloaded)
        self.download_worker.download_error.connect(self.on_download_error)
        self.download_worker.start()

    def on_download_progress(self, current: int, total: int, message: str):
        """Aggiorna progress durante download."""
        self.status_label.setText(message)

    def on_chapter_downloaded(self, chapter_number: str, pages_data: List[bytes]):
        """Chiamato quando un capitolo è stato scaricato."""
        try:
            # Salva nel database
            chapter_id = self.chapter_manager.add_chapter(
                self.current_manga_file,
                f"Capitolo {chapter_number}",
                pages_data
            )

            logger.info(f"Chapter {chapter_number} saved with ID {chapter_id}")

            # Prossimo capitolo
            self.current_chapter_idx += 1
            self.progress_bar.setValue(self.current_chapter_idx)

            self.download_next_chapter()

        except Exception as e:
            logger.error(f"Error saving chapter: {e}")
            self.on_download_error(str(e))

    def on_download_error(self, error: str):
        """Chiamato in caso di errore nel download."""
        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)
        self.download_all_button.setEnabled(True)
        self.status_label.setText(f"❌ Errore: {error}")

        reply = QMessageBox.question(
            self,
            "Errore",
            f"Errore durante il download:\n{error}\n\nContinuare con il prossimo capitolo?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.current_chapter_idx += 1
            self.progress_bar.setVisible(True)
            self.download_next_chapter()


class MangaWorldDownloaderPlugin(PluginBase):
    """Plugin per scaricare manga da MangaWorld."""

    def __init__(self):
        super().__init__()
        self.plugin_id = "mangaworld-downloader"
        self.plugin_name = "MangaWorld Downloader"
        self.plugin_version = "1.0.0"
        self.plugin_author = "MangaReader Team"
        self.plugin_description = "Scarica manga da MangaWorld"

        self.dialog = None

    def on_enable(self) -> bool:
        """Attiva il plugin."""
        logger.info(f"{self.plugin_name} v{self.plugin_version} attivato!")
        return True

    def on_disable(self) -> bool:
        """Disattiva il plugin."""
        if self.dialog:
            self.dialog.close()
            self.dialog = None

        logger.info(f"{self.plugin_name} disattivato!")
        return True

    def get_menu_actions(self) -> list:
        """Restituisce azioni per il menu."""
        return [
            {
                'name': '⬇️ Scarica da MangaWorld',
                'callback': self.open_downloader,
                'shortcut': 'Ctrl+M'
            }
        ]

    def open_downloader(self):
        """Apre la finestra del downloader."""
        if not self.dialog:
            self.dialog = MangaWorldDownloaderDialog()

        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()


def create_plugin():
    """Factory function per creare il plugin."""
    return MangaWorldDownloaderPlugin()
