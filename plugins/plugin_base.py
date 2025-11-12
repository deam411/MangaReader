"""
Base class and interfaces for Manga Reader plugins.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class PluginHook(Enum):
    """Eventi a cui i plugin possono agganciarsi."""
    # Lifecycle
    ON_STARTUP = "on_startup"
    ON_SHUTDOWN = "on_shutdown"

    # Import/Export
    PRE_IMPORT = "pre_import"
    POST_IMPORT = "post_import"
    PRE_EXPORT = "pre_export"
    POST_EXPORT = "post_export"

    # Reading
    PRE_PAGE_LOAD = "pre_page_load"
    POST_PAGE_LOAD = "post_page_load"
    ON_CHAPTER_CHANGE = "on_chapter_change"

    # Library
    ON_LIBRARY_REFRESH = "on_library_refresh"
    ON_MANGA_ADDED = "on_manga_added"
    ON_MANGA_DELETED = "on_manga_deleted"

    # UI
    CUSTOM_MENU_ITEM = "custom_menu_item"
    CUSTOM_TOOLBAR_BUTTON = "custom_toolbar_button"


@dataclass
class PluginMetadata:
    """Metadata del plugin."""
    name: str
    version: str
    author: str
    description: str
    requires_version: str = "0.3.0"  # Versione minima app richiesta
    icon: Optional[str] = None
    url: Optional[str] = None


class PluginBase(ABC):
    """
    Classe base per tutti i plugin.

    I plugin devono ereditare da questa classe e implementare
    almeno il metodo metadata() e gli hook necessari.

    Example:
        class MyPlugin(PluginBase):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="My Plugin",
                    version="1.0.0",
                    author="Author Name",
                    description="Plugin description"
                )

            def on_startup(self, context: Dict[str, Any]):
                print("Plugin started!")

            def on_manga_added(self, context: Dict[str, Any]):
                manga_path = context.get('manga_path')
                print(f"New manga added: {manga_path}")
    """

    def __init__(self):
        """Inizializza il plugin."""
        self.enabled = True
        self.config: Dict[str, Any] = {}

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """
        Restituisce i metadata del plugin.

        Returns:
            PluginMetadata con informazioni sul plugin
        """
        pass

    # Lifecycle hooks
    def on_startup(self, context: Dict[str, Any]) -> None:
        """
        Chiamato all'avvio dell'applicazione.

        Args:
            context: Contiene app_instance, settings, logger
        """
        pass

    def on_shutdown(self, context: Dict[str, Any]) -> None:
        """
        Chiamato alla chiusura dell'applicazione.

        Args:
            context: Contiene app_instance, settings
        """
        pass

    # Import/Export hooks
    def pre_import(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Chiamato prima dell'import di un manga.

        Args:
            context: Contiene file_path, metadata

        Returns:
            Modified context o None per cancellare import
        """
        return context

    def post_import(self, context: Dict[str, Any]) -> None:
        """
        Chiamato dopo l'import di un manga.

        Args:
            context: Contiene manga_path, metadata, success
        """
        pass

    def pre_export(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Chiamato prima dell'export di un manga.

        Args:
            context: Contiene manga_path, export_path

        Returns:
            Modified context o None per cancellare export
        """
        return context

    def post_export(self, context: Dict[str, Any]) -> None:
        """
        Chiamato dopo l'export di un manga.

        Args:
            context: Contiene export_path, success
        """
        pass

    # Reading hooks
    def pre_page_load(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Chiamato prima del caricamento di una pagina.

        Args:
            context: Contiene page_number, chapter_id, image_data

        Returns:
            Modified context con image_data modificata se necessario
        """
        return context

    def post_page_load(self, context: Dict[str, Any]) -> None:
        """
        Chiamato dopo il caricamento di una pagina.

        Args:
            context: Contiene page_number, chapter_id, load_time
        """
        pass

    def on_chapter_change(self, context: Dict[str, Any]) -> None:
        """
        Chiamato quando si cambia capitolo.

        Args:
            context: Contiene old_chapter_id, new_chapter_id, manga_path
        """
        pass

    # Library hooks
    def on_library_refresh(self, context: Dict[str, Any]) -> None:
        """
        Chiamato quando la libreria viene ricaricata.

        Args:
            context: Contiene manga_count, library_path
        """
        pass

    def on_manga_added(self, context: Dict[str, Any]) -> None:
        """
        Chiamato quando un manga viene aggiunto alla libreria.

        Args:
            context: Contiene manga_path, metadata
        """
        pass

    def on_manga_deleted(self, context: Dict[str, Any]) -> None:
        """
        Chiamato quando un manga viene eliminato.

        Args:
            context: Contiene manga_path
        """
        pass

    # UI hooks
    def get_custom_menu_items(self) -> List[Dict[str, Any]]:
        """
        Restituisce menu items personalizzati da aggiungere all'UI.

        Returns:
            Lista di dict con 'text', 'icon', 'callback'

        Example:
            [
                {
                    'text': 'My Action',
                    'icon': 'path/to/icon.png',
                    'callback': self.my_action_handler
                }
            ]
        """
        return []

    def get_custom_toolbar_buttons(self) -> List[Dict[str, Any]]:
        """
        Restituisce bottoni personalizzati per la toolbar.

        Returns:
            Lista di dict con 'text', 'icon', 'tooltip', 'callback'
        """
        return []

    # Configuration
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Restituisce lo schema di configurazione del plugin.

        Returns:
            Dict con schema configurazione (tipo, default, descrizione)

        Example:
            {
                'api_key': {
                    'type': 'str',
                    'default': '',
                    'description': 'API key for service'
                },
                'enabled_features': {
                    'type': 'list',
                    'default': [],
                    'description': 'List of enabled features'
                }
            }
        """
        return {}

    def set_config(self, config: Dict[str, Any]) -> None:
        """
        Imposta la configurazione del plugin.

        Args:
            config: Dizionario configurazione
        """
        self.config = config

    def get_config(self) -> Dict[str, Any]:
        """
        Ottiene la configurazione corrente del plugin.

        Returns:
            Dizionario configurazione
        """
        return self.config
