"""
Example Plugin - Dimostra come creare un plugin per Manga Reader.

Questo plugin:
- Logga quando un manga viene aggiunto/eliminato
- Conta le pagine lette durante una sessione
- Aggiunge un menu item personalizzato
"""

from plugins.plugin_base import PluginBase, PluginMetadata
from typing import Dict, Any, List


class ExamplePlugin(PluginBase):
    """Plugin di esempio che dimostra le funzionalità base."""

    def __init__(self):
        super().__init__()
        self.pages_read_count = 0

    @property
    def metadata(self) -> PluginMetadata:
        """Metadata del plugin."""
        return PluginMetadata(
            name="Example Plugin",
            version="1.0.0",
            author="Manga Reader Team",
            description="Plugin di esempio che dimostra le funzionalità base del sistema di plugin",
            requires_version="0.3.0",
            url="https://github.com/deam411/MangaReader"
        )

    def on_startup(self, context: Dict[str, Any]) -> None:
        """Chiamato all'avvio dell'applicazione."""
        logger = context.get('logger')
        if logger:
            logger.info(f"{self.metadata.name} v{self.metadata.version} started!")

        print(f"[ExamplePlugin] Plugin caricato! Conteggio pagine abilitato.")

    def on_shutdown(self, context: Dict[str, Any]) -> None:
        """Chiamato alla chiusura."""
        print(f"[ExamplePlugin] Plugin chiuso. Pagine lette in questa sessione: {self.pages_read_count}")

    def on_manga_added(self, context: Dict[str, Any]) -> None:
        """Chiamato quando un manga viene aggiunto."""
        manga_path = context.get('manga_path', 'unknown')
        metadata = context.get('metadata', {})
        title = metadata.get('title', 'Unknown')

        print(f"[ExamplePlugin] Nuovo manga aggiunto: {title} ({manga_path})")

    def on_manga_deleted(self, context: Dict[str, Any]) -> None:
        """Chiamato quando un manga viene eliminato."""
        manga_path = context.get('manga_path', 'unknown')
        print(f"[ExamplePlugin] Manga eliminato: {manga_path}")

    def post_page_load(self, context: Dict[str, Any]) -> None:
        """Conta le pagine lette."""
        self.pages_read_count += 1
        page_number = context.get('page_number', 0)
        chapter_id = context.get('chapter_id', 0)

        # Ogni 10 pagine, mostra un messaggio
        if self.pages_read_count % 10 == 0:
            print(f"[ExamplePlugin] Hai letto {self.pages_read_count} pagine! Continua così!")

    def on_chapter_change(self, context: Dict[str, Any]) -> None:
        """Notifica cambio capitolo."""
        old_ch = context.get('old_chapter_id', 0)
        new_ch = context.get('new_chapter_id', 0)
        print(f"[ExamplePlugin] Cambio capitolo: {old_ch} → {new_ch}")

    def get_custom_menu_items(self) -> List[Dict[str, Any]]:
        """Aggiunge menu item personalizzato."""
        return [
            {
                'text': 'Show Pages Read',
                'icon': None,
                'callback': self.show_pages_count
            },
            {
                'text': 'Reset Counter',
                'icon': None,
                'callback': self.reset_counter
            }
        ]

    def show_pages_count(self):
        """Mostra il conteggio delle pagine lette."""
        print(f"[ExamplePlugin] Pagine lette: {self.pages_read_count}")
        # In un plugin reale, potresti mostrare un QMessageBox

    def reset_counter(self):
        """Resetta il contatore."""
        self.pages_read_count = 0
        print(f"[ExamplePlugin] Contatore resettato!")

    def get_config_schema(self) -> Dict[str, Any]:
        """Schema configurazione del plugin."""
        return {
            'enable_notifications': {
                'type': 'bool',
                'default': True,
                'description': 'Mostra notifiche ogni 10 pagine'
            },
            'notification_interval': {
                'type': 'int',
                'default': 10,
                'description': 'Numero di pagine tra le notifiche'
            }
        }
