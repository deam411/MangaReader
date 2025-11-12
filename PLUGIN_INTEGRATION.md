# Plugin System Integration Guide

## Modifiche Necessarie

### 1. main.py - Inizializzazione PluginManager

Aggiungere all'inizio del file:
```python
from plugins import PluginManager
```

Nella classe `MangaReader.__init__()`, dopo `self.setStyleSheet(...)`:
```python
# Inizializza plugin manager
self.plugin_manager = PluginManager()
self.plugin_manager.load_all_plugins()

# Trigger on_startup hook
self.plugin_manager.trigger_hook(
    PluginHook.ON_STARTUP,
    {'app_instance': self, 'settings': settings, 'logger': logger}
)
```

Nel metodo `closeEvent()`:
```python
# Trigger on_shutdown hook
self.plugin_manager.trigger_hook(
    PluginHook.ON_SHUTDOWN,
    {'app_instance': self}
)
```

### 2. settings_dialog.py - Aggiungere Tab Plugins

Nella classe `SettingsDialog.__init__()`, modificare imports:
```python
from src.settings_tabs import (
    GeneralTab, AppearanceTab, PerformanceTab, ReaderTab,
    ShortcutsTab, BookmarksTab, BackupTab, PluginsTab
)
```

Aggiungere parametro al costruttore:
```python
def __init__(self, plugin_manager, parent=None):
    super().__init__(parent)
    self.plugin_manager = plugin_manager
    ...
```

Nel metodo `init_ui()`, dopo `backup_tab`:
```python
# Tab Plugins (v0.3.0)
plugins_tab = PluginsTab(self.plugin_manager, self)
self.tabs.addTab(plugins_tab, "Plugin")
self.tab_widgets['plugins'] = plugins_tab
```

### 3. library_view.py - Hooks per Import/Add/Delete

Importare all'inizio:
```python
from plugins import PluginHook
```

Nel metodo `import_archive()`, prima dell'import:
```python
# Trigger pre_import hook
context = self.parent().plugin_manager.trigger_hook(
    PluginHook.PRE_IMPORT,
    {'file_path': file_path, 'metadata': metadata}
)
if context is None:
    return  # Plugin ha cancellato l'import
```

Dopo l'import con successo:
```python
# Trigger post_import hook
self.parent().plugin_manager.trigger_hook(
    PluginHook.POST_IMPORT,
    {'manga_path': manga_path, 'metadata': metadata, 'success': True}
)
```

Nel metodo `delete_manga()`, dopo conferma:
```python
# Trigger on_manga_deleted hook
self.parent().plugin_manager.trigger_hook(
    PluginHook.ON_MANGA_DELETED,
    {'manga_path': manga_path}
)
```

Nel metodo `load_library()`, alla fine:
```python
# Trigger on_library_refresh hook
self.parent().plugin_manager.trigger_hook(
    PluginHook.ON_LIBRARY_REFRESH,
    {'manga_count': len(manga_list), 'library_path': library_path}
)
```

### 4. reader_view.py - Hooks per Lettura

Nel metodo `load_page()` o equivalente, dopo caricamento:
```python
# Trigger post_page_load hook
self.parent().parent().plugin_manager.trigger_hook(
    PluginHook.POST_PAGE_LOAD,
    {'page_number': page_num, 'chapter_id': chapter_id, 'load_time': load_time}
)
```

### 5. Chiamata Settings Dialog

In `main.py`, metodo `show_settings()`:
```python
def show_settings(self):
    from src.settings_dialog import SettingsDialog
    dialog = SettingsDialog(self.plugin_manager, self)  # Passa plugin_manager
    ...
```

## Files Creati

- `plugins/__init__.py` - Package plugin
- `plugins/plugin_base.py` - Classe base e hooks
- `plugins/plugin_manager.py` - Manager principale
- `plugins/available/example_plugin/plugin.py` - Plugin di esempio
- `plugins/available/example_plugin/__init__.py`
- `src/settings_tabs/plugins_tab.py` - UI gestione plugin

## Prossimi Step

1. Applicare le modifiche sopra elencate
2. Testare caricamento plugin
3. Verificare hooks funzionanti
4. Aggiornare CHANGELOG
5. Commit e release
