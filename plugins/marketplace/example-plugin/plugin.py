"""
Example Plugin per MangaReader

Questo è un plugin di esempio che mostra come creare plugin per MangaReader.
Usa questo file come template per creare i tuoi plugin personalizzati.
"""

from plugins.plugin_base import PluginBase
from src.logger import get_logger

logger = get_logger(__name__)


class ExamplePlugin(PluginBase):
    """
    Plugin di esempio che dimostra le funzionalità base.
    """

    def __init__(self):
        super().__init__()
        self.plugin_id = "example-plugin"
        self.plugin_name = "Example Plugin"
        self.plugin_version = "1.0.0"
        self.plugin_author = "MangaReader Team"
        self.plugin_description = "Plugin di esempio per MangaReader"

    def on_enable(self) -> bool:
        """
        Chiamato quando il plugin viene attivato.

        Returns:
            True se attivazione riuscita
        """
        logger.info(f"{self.plugin_name} v{self.plugin_version} attivato!")
        return True

    def on_disable(self) -> bool:
        """
        Chiamato quando il plugin viene disattivato.

        Returns:
            True se disattivazione riuscita
        """
        logger.info(f"{self.plugin_name} disattivato!")
        return True

    def get_menu_actions(self) -> list:
        """
        Restituisce lista di azioni da aggiungere al menu.

        Returns:
            Lista di dict con 'name', 'callback', 'shortcut' (opzionale)
        """
        return [
            {
                'name': 'Azione di Esempio',
                'callback': self.example_action,
                'shortcut': None  # Es: 'Ctrl+E'
            }
        ]

    def example_action(self):
        """
        Esempio di azione che il plugin può eseguire.
        """
        logger.info("Azione di esempio eseguita!")
        # Qui puoi aggiungere la tua logica
        # Es: aprire una finestra, modificare dati, etc.


# Punto di ingresso del plugin
def create_plugin():
    """
    Factory function che crea e restituisce l'istanza del plugin.
    Questa funzione viene chiamata dal PluginManager.
    """
    return ExamplePlugin()
