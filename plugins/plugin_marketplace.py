"""
Plugin Marketplace per scaricare e installare plugin da repository remoti.
"""

import os
import json
import shutil
import zipfile
import tarfile
import tempfile
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any
from pathlib import Path
from packaging import version
from src.logger import get_logger

logger = get_logger(__name__)


class PluginMarketplace:
    """
    Gestisce il marketplace dei plugin, permettendo di:
    - Scaricare la lista dei plugin disponibili da un repository remoto
    - Installare plugin dal marketplace
    - Verificare aggiornamenti disponibili
    - Disinstallare plugin
    """

    def __init__(self, plugin_dir: str, app_version: str = "0.5.0"):
        """
        Inizializza il PluginMarketplace.

        Args:
            plugin_dir: Directory dove installare i plugin
            app_version: Versione corrente dell'applicazione
        """
        self.plugin_dir = plugin_dir
        self.app_version = app_version
        self.marketplace_url = "https://raw.githubusercontent.com/deam411/MangaReader-Plugins/main/plugins.json"

        # Path al file locale del marketplace
        marketplace_dir = os.path.join(os.path.dirname(plugin_dir), 'marketplace')
        self.local_marketplace_file = os.path.join(marketplace_dir, 'plugins.json')

        self.available_plugins: List[Dict[str, Any]] = []

        logger.info(f"PluginMarketplace inizializzato. App version: {app_version}")
        logger.debug(f"Local marketplace file: {self.local_marketplace_file}")

    def fetch_available_plugins(self) -> bool:
        """
        Scansiona la directory marketplace locale per trovare plugin disponibili.
        Ogni sottodirectory in plugins/marketplace/ è considerata un plugin.

        Returns:
            True se scansionata con successo, False altrimenti
        """
        try:
            marketplace_dir = os.path.dirname(self.local_marketplace_file)

            if not os.path.exists(marketplace_dir):
                logger.warning(f"Marketplace directory not found: {marketplace_dir}")
                return False

            logger.info(f"Scanning marketplace directory: {marketplace_dir}")

            self.available_plugins = []

            # Scansiona tutte le sottodirectory
            for item in os.listdir(marketplace_dir):
                item_path = os.path.join(marketplace_dir, item)

                # Salta file (come plugins.json)
                if not os.path.isdir(item_path):
                    continue

                # Verifica se è un plugin valido (ha plugin.py o __init__.py)
                plugin_file = os.path.join(item_path, 'plugin.py')
                init_file = os.path.join(item_path, '__init__.py')
                manifest_file = os.path.join(item_path, 'manifest.json')

                if not (os.path.exists(plugin_file) or os.path.exists(init_file)):
                    logger.debug(f"Skipping {item}: not a valid plugin (no plugin.py or __init__.py)")
                    continue

                # Carica manifest se esiste, altrimenti usa info di base
                plugin_info = {
                    'id': item,
                    'name': item.replace('_', ' ').replace('-', ' ').title(),
                    'version': '1.0.0',
                    'author': 'Unknown',
                    'description': 'No description available',
                    'requires_version': '0.0.0',
                    'local_path': item_path
                }

                if os.path.exists(manifest_file):
                    try:
                        with open(manifest_file, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                            plugin_info.update(manifest)
                            plugin_info['local_path'] = item_path
                            logger.debug(f"Loaded manifest for {item}")
                    except Exception as e:
                        logger.warning(f"Could not read manifest for {item}: {e}")

                self.available_plugins.append(plugin_info)
                logger.debug(f"Found plugin: {plugin_info['name']} v{plugin_info['version']}")

            logger.info(f"Found {len(self.available_plugins)} plugins in marketplace directory")
            return True

        except Exception as e:
            logger.error(f"Error scanning marketplace directory: {e}", exc_info=True)
            return False

    def get_available_plugins(self) -> List[Dict[str, Any]]:
        """
        Restituisce la lista dei plugin disponibili.

        Returns:
            Lista di dict con info plugin
        """
        return self.available_plugins

    def is_plugin_installed(self, plugin_id: str) -> bool:
        """
        Verifica se un plugin è già installato.

        Args:
            plugin_id: ID del plugin

        Returns:
            True se installato
        """
        plugin_path = os.path.join(self.plugin_dir, plugin_id)
        return os.path.exists(plugin_path)

    def get_installed_version(self, plugin_id: str) -> Optional[str]:
        """
        Ottiene la versione installata di un plugin.

        Args:
            plugin_id: ID del plugin

        Returns:
            Versione installata o None
        """
        plugin_path = os.path.join(self.plugin_dir, plugin_id)
        manifest_file = os.path.join(plugin_path, 'manifest.json')

        if os.path.exists(manifest_file):
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    return manifest.get('version')
            except Exception as e:
                logger.error(f"Error reading manifest for {plugin_id}: {e}")

        return None

    def is_update_available(self, plugin_id: str, marketplace_version: str) -> bool:
        """
        Verifica se è disponibile un aggiornamento per un plugin.

        Args:
            plugin_id: ID del plugin
            marketplace_version: Versione nel marketplace

        Returns:
            True se aggiornamento disponibile
        """
        installed_version = self.get_installed_version(plugin_id)

        if installed_version is None:
            return False

        try:
            return version.parse(marketplace_version) > version.parse(installed_version)
        except Exception as e:
            logger.error(f"Error comparing versions: {e}")
            return False

    def is_compatible(self, required_version: str) -> bool:
        """
        Verifica se il plugin è compatibile con la versione dell'app.

        Args:
            required_version: Versione minima richiesta

        Returns:
            True se compatibile
        """
        try:
            return version.parse(self.app_version) >= version.parse(required_version)
        except Exception as e:
            logger.error(f"Error checking compatibility: {e}")
            return False

    def download_file(self, url: str, callback=None) -> Optional[str]:
        """
        Scarica un file e lo salva in un file temporaneo.

        Args:
            url: URL del file da scaricare
            callback: Funzione callback(downloaded, total) per progress

        Returns:
            Path al file temporaneo o None
        """
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_path = temp_file.name
            temp_file.close()

            logger.info(f"Downloading from: {url}")

            def progress_hook(block_num, block_size, total_size):
                if callback:
                    downloaded = block_num * block_size
                    callback(downloaded, total_size)

            urllib.request.urlretrieve(url, temp_path, reporthook=progress_hook)

            logger.info(f"Download completed: {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"Error downloading file: {e}", exc_info=True)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None

    def extract_plugin(self, archive_path: str, plugin_id: str) -> bool:
        """
        Estrae un plugin da un archivio ZIP o TAR.

        Args:
            archive_path: Path all'archivio
            plugin_id: ID del plugin

        Returns:
            True se estratto con successo
        """
        try:
            plugin_path = os.path.join(self.plugin_dir, plugin_id)

            # Rimuovi plugin esistente se presente
            if os.path.exists(plugin_path):
                logger.info(f"Removing existing plugin at: {plugin_path}")
                shutil.rmtree(plugin_path)

            # Crea directory plugin
            os.makedirs(plugin_path, exist_ok=True)

            # Estrai archivio
            if archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(plugin_path)
            elif archive_path.endswith(('.tar.gz', '.tgz')):
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(plugin_path)
            else:
                logger.error(f"Unsupported archive format: {archive_path}")
                return False

            logger.info(f"Plugin extracted to: {plugin_path}")
            return True

        except Exception as e:
            logger.error(f"Error extracting plugin: {e}", exc_info=True)
            return False

    def save_manifest(self, plugin_id: str, plugin_info: Dict[str, Any]) -> bool:
        """
        Salva il manifest del plugin per tracciare versione e metadata.

        Args:
            plugin_id: ID del plugin
            plugin_info: Informazioni del plugin dal marketplace

        Returns:
            True se salvato con successo
        """
        try:
            plugin_path = os.path.join(self.plugin_dir, plugin_id)
            manifest_file = os.path.join(plugin_path, 'manifest.json')

            manifest = {
                'id': plugin_id,
                'version': plugin_info.get('version'),
                'name': plugin_info.get('name'),
                'author': plugin_info.get('author'),
                'installed_at': str(Path(manifest_file).stat().st_mtime) if os.path.exists(manifest_file) else None
            }

            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)

            logger.info(f"Manifest saved for: {plugin_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving manifest: {e}")
            return False

    def install_plugin(self, plugin_info: Dict[str, Any], progress_callback=None) -> bool:
        """
        Installa un plugin dal marketplace.

        Args:
            plugin_info: Informazioni del plugin dal marketplace
            progress_callback: Callback(downloaded, total) per progress

        Returns:
            True se installato con successo
        """
        plugin_id = plugin_info.get('id')
        local_path = plugin_info.get('local_path')
        download_url = plugin_info.get('download_url')
        required_version = plugin_info.get('requires_version', '0.0.0')

        if not plugin_id:
            logger.error("Missing plugin_id")
            return False

        # Verifica compatibilità
        if not self.is_compatible(required_version):
            logger.error(
                f"Plugin {plugin_id} requires app version {required_version}, "
                f"but current version is {self.app_version}"
            )
            return False

        try:
            # Se è un plugin locale, copialo direttamente
            if local_path and os.path.exists(local_path):
                logger.info(f"Installing local plugin from: {local_path}")

                target_path = os.path.join(self.plugin_dir, plugin_id)

                # Rimuovi plugin esistente se presente
                if os.path.exists(target_path):
                    logger.info(f"Removing existing plugin at: {target_path}")
                    shutil.rmtree(target_path)

                # Copia la directory del plugin
                shutil.copytree(local_path, target_path)
                logger.info(f"Plugin copied to: {target_path}")

                # Salva manifest
                self.save_manifest(plugin_id, plugin_info)

                logger.info(f"Local plugin {plugin_id} installed successfully")
                return True

            # Altrimenti, scarica da URL
            if not download_url:
                logger.error("Missing download_url for remote plugin")
                return False

            # Download
            archive_path = self.download_file(download_url, callback=progress_callback)
            if not archive_path:
                return False

            # Estrai
            success = self.extract_plugin(archive_path, plugin_id)
            if not success:
                return False

            # Salva manifest
            self.save_manifest(plugin_id, plugin_info)

            # Rimuovi file temporaneo
            os.remove(archive_path)

            logger.info(f"Plugin {plugin_id} installed successfully")
            return True

        except Exception as e:
            logger.error(f"Error installing plugin {plugin_id}: {e}", exc_info=True)
            return False

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """
        Disinstalla un plugin.

        Args:
            plugin_id: ID del plugin

        Returns:
            True se disinstallato con successo
        """
        try:
            plugin_path = os.path.join(self.plugin_dir, plugin_id)

            if not os.path.exists(plugin_path):
                logger.warning(f"Plugin {plugin_id} not found")
                return False

            shutil.rmtree(plugin_path)
            logger.info(f"Plugin {plugin_id} uninstalled successfully")
            return True

        except Exception as e:
            logger.error(f"Error uninstalling plugin {plugin_id}: {e}", exc_info=True)
            return False
