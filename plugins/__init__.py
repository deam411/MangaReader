"""
Plugin system for Manga Reader.

Allows extending functionality through external plugins.
"""

from .plugin_base import PluginBase, PluginMetadata
from .plugin_manager import PluginManager

__all__ = ['PluginBase', 'PluginMetadata', 'PluginManager']
