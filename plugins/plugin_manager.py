"""
Plugin Manager per il caricamento e gestione dei plugin.
"""

import os
import sys
import json
import importlib.util
from typing import Dict, List, Any, Optional
from pathlib import Path
from .plugin_base import PluginBase, PluginHook, PluginMetadata
from src.logger import get_logger
from src.paths import get_data_dir

logger = get_logger(__name__)


class PluginManager:
    """
    Gestisce il caricamento, configurazione e lifecycle dei plugin.

    Attributes:
        plugins: Dict di plugin caricati {plugin_name: plugin_instance}
        enabled_plugins: Set di plugin abilitati
        plugin_dir: Directory dove cercare i plugin
    """

    def __init__(self, plugin_dir: Optional[str] = None):
        """
        Inizializza il PluginManager.

        Args:
            plugin_dir: Directory dei plugin (default: plugins/available/)
        """
        if plugin_dir is None:
            # Default: plugins/available/ nella root del progetto
            if getattr(sys, 'frozen', False):
                # Eseguibile compilato
                base_dir = os.path.dirname(sys.executable)
            else:
                # Sviluppo
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            plugin_dir = os.path.join(base_dir, 'plugins', 'available')

        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, PluginBase] = {}
        self.enabled_plugins: set = set()
        self.config_file = os.path.join(get_data_dir(), 'plugins_config.json')

        # Crea directory se non esiste
        os.makedirs(self.plugin_dir, exist_ok=True)

        logger.info(f"PluginManager inizializzato. Plugin directory: {self.plugin_dir}")

    def discover_plugins(self) -> List[str]:
        """
        Scopre tutti i plugin disponibili nella directory.

        Returns:
            Lista di nomi plugin trovati
        """
        discovered = []

        if not os.path.exists(self.plugin_dir):
            logger.warning(f"Plugin directory non trovata: {self.plugin_dir}")
            return discovered

        for item in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, item)

            # Verifica se è una directory con __init__.py o plugin.py
            if os.path.isdir(plugin_path):
                init_file = os.path.join(plugin_path, '__init__.py')
                plugin_file = os.path.join(plugin_path, 'plugin.py')

                if os.path.exists(init_file) or os.path.exists(plugin_file):
                    discovered.append(item)
                    logger.debug(f"Plugin scoperto: {item}")

        logger.info(f"Trovati {len(discovered)} plugin: {discovered}")
        return discovered

    def load_plugin(self, plugin_name: str) -> bool:
        """
        Carica un singolo plugin.

        Args:
            plugin_name: Nome della directory del plugin

        Returns:
            True se caricato con successo, False altrimenti
        """
        try:
            plugin_path = os.path.join(self.plugin_dir, plugin_name)

            # Prova prima plugin.py, poi __init__.py
            plugin_file = os.path.join(plugin_path, 'plugin.py')
            if not os.path.exists(plugin_file):
                plugin_file = os.path.join(plugin_path, '__init__.py')

            if not os.path.exists(plugin_file):
                logger.error(f"File plugin non trovato per: {plugin_name}")
                return False

            # Carica il modulo dinamicamente
            spec = importlib.util.spec_from_file_location(
                f"plugins.available.{plugin_name}",
                plugin_file
            )
            if spec is None or spec.loader is None:
                logger.error(f"Impossibile caricare spec per: {plugin_name}")
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Cerca una classe che eredita da PluginBase
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, PluginBase) and
                    attr is not PluginBase):
                    plugin_class = attr
                    break

            if plugin_class is None:
                logger.error(f"Nessuna classe PluginBase trovata in: {plugin_name}")
                return False

            # Istanzia il plugin
            plugin_instance = plugin_class()
            metadata = plugin_instance.metadata

            # Carica configurazione salvata
            config = self.load_plugin_config(plugin_name)
            if config:
                plugin_instance.set_config(config)

            self.plugins[plugin_name] = plugin_instance
            logger.info(f"Plugin caricato: {metadata.name} v{metadata.version} by {metadata.author}")

            return True

        except Exception as e:
            logger.error(f"Errore caricamento plugin {plugin_name}: {e}", exc_info=True)
            return False

    def load_all_plugins(self) -> int:
        """
        Carica tutti i plugin disponibili.

        Returns:
            Numero di plugin caricati con successo
        """
        discovered = self.discover_plugins()
        loaded = 0

        for plugin_name in discovered:
            if self.load_plugin(plugin_name):
                loaded += 1

        # Carica configurazione enabled plugins
        self.load_enabled_plugins()

        logger.info(f"Caricati {loaded}/{len(discovered)} plugin")
        return loaded

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Scarica un plugin.

        Args:
            plugin_name: Nome del plugin da scaricare

        Returns:
            True se scaricato con successo
        """
        if plugin_name in self.plugins:
            # Chiama on_shutdown hook
            try:
                self.plugins[plugin_name].on_shutdown({})
            except Exception as e:
                logger.error(f"Errore durante shutdown plugin {plugin_name}: {e}")

            del self.plugins[plugin_name]
            self.enabled_plugins.discard(plugin_name)
            logger.info(f"Plugin scaricato: {plugin_name}")
            return True

        return False

    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Ricarica un plugin (unload + load).

        Args:
            plugin_name: Nome del plugin

        Returns:
            True se ricaricato con successo
        """
        self.unload_plugin(plugin_name)
        return self.load_plugin(plugin_name)

    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Abilita un plugin.

        Args:
            plugin_name: Nome del plugin

        Returns:
            True se abilitato con successo
        """
        if plugin_name in self.plugins:
            self.enabled_plugins.add(plugin_name)
            self.plugins[plugin_name].enabled = True
            self.save_enabled_plugins()
            logger.info(f"Plugin abilitato: {plugin_name}")
            return True
        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disabilita un plugin.

        Args:
            plugin_name: Nome del plugin

        Returns:
            True se disabilitato con successo
        """
        if plugin_name in self.plugins:
            self.enabled_plugins.discard(plugin_name)
            self.plugins[plugin_name].enabled = False
            self.save_enabled_plugins()
            logger.info(f"Plugin disabilitato: {plugin_name}")
            return True
        return False

    def trigger_hook(self, hook: PluginHook, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Triggera un hook su tutti i plugin abilitati.

        Args:
            hook: Hook da triggerare
            context: Contesto da passare ai plugin

        Returns:
            Contesto modificato dai plugin (o None se cancellato)
        """
        modified_context = context

        for plugin_name in self.enabled_plugins:
            if plugin_name not in self.plugins:
                continue

            plugin = self.plugins[plugin_name]

            try:
                # Chiama il metodo appropriato basato sull'hook
                hook_method = getattr(plugin, hook.value, None)

                if hook_method and callable(hook_method):
                    result = hook_method(modified_context)

                    # Per gli hook "pre_*", se ritorna None, cancella l'operazione
                    if hook.value.startswith('pre_') and result is None:
                        logger.info(f"Plugin {plugin_name} ha cancellato l'operazione {hook.value}")
                        return None

                    # Se ritorna un dict, usa quello come nuovo context
                    if isinstance(result, dict):
                        modified_context = result

            except Exception as e:
                logger.error(f"Errore in plugin {plugin_name} durante {hook.value}: {e}", exc_info=True)

        return modified_context

    def get_plugin_list(self) -> List[Dict[str, Any]]:
        """
        Ottiene la lista di tutti i plugin con metadata.

        Returns:
            Lista di dict con info plugin
        """
        plugin_list = []

        for name, plugin in self.plugins.items():
            metadata = plugin.metadata
            plugin_list.append({
                'name': name,
                'display_name': metadata.name,
                'version': metadata.version,
                'author': metadata.author,
                'description': metadata.description,
                'enabled': name in self.enabled_plugins,
                'icon': metadata.icon,
                'url': metadata.url
            })

        return plugin_list

    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """
        Ottiene un'istanza di plugin per nome.

        Args:
            plugin_name: Nome del plugin

        Returns:
            Istanza PluginBase o None
        """
        return self.plugins.get(plugin_name)

    def save_enabled_plugins(self) -> None:
        """Salva la lista dei plugin abilitati su disco."""
        config = {
            'enabled_plugins': list(self.enabled_plugins)
        }

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            logger.debug(f"Configurazione plugin salvata: {self.config_file}")
        except Exception as e:
            logger.error(f"Errore salvataggio configurazione plugin: {e}")

    def load_enabled_plugins(self) -> None:
        """Carica la lista dei plugin abilitati da disco."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    enabled = config.get('enabled_plugins', [])

                    # Abilita solo i plugin che sono stati caricati
                    for plugin_name in enabled:
                        if plugin_name in self.plugins:
                            self.enabled_plugins.add(plugin_name)
                            self.plugins[plugin_name].enabled = True

                    logger.debug(f"Caricati {len(self.enabled_plugins)} plugin abilitati")
        except Exception as e:
            logger.error(f"Errore caricamento configurazione plugin: {e}")

    def save_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """
        Salva la configurazione di un plugin.

        Args:
            plugin_name: Nome del plugin
            config: Configurazione da salvare
        """
        config_dir = os.path.join(get_data_dir(), 'plugin_configs')
        os.makedirs(config_dir, exist_ok=True)

        config_file = os.path.join(config_dir, f"{plugin_name}.json")

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            logger.debug(f"Configurazione plugin {plugin_name} salvata")
        except Exception as e:
            logger.error(f"Errore salvataggio config plugin {plugin_name}: {e}")

    def load_plugin_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Carica la configurazione di un plugin.

        Args:
            plugin_name: Nome del plugin

        Returns:
            Dict configurazione o None
        """
        config_file = os.path.join(get_data_dir(), 'plugin_configs', f"{plugin_name}.json")

        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Errore caricamento config plugin {plugin_name}: {e}")

        return None
