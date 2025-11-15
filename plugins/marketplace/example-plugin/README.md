# Example Plugin

Questo è un plugin di esempio che dimostra la struttura base di un plugin per MangaReader.

## Struttura File

```
example-plugin/
 plugin.py         # File principale del plugin
 manifest.json     # Metadata del plugin
 README.md         # Documentazione
```

## Come Creare un Plugin

1. **Crea una directory** in `plugins/marketplace/` con il nome del tuo plugin (es: `my-custom-plugin`)

2. **Crea manifest.json** con i metadata:
   ```json
   {
     "id": "my-custom-plugin",
     "name": "My Custom Plugin",
     "version": "1.0.0",
     "author": "Your Name",
     "description": "Descrizione del plugin",
     "requires_version": "0.5.0"
   }
   ```

3. **Crea plugin.py** estendendo `PluginBase`:
   - Implementa `on_enable()` per inizializzazione
   - Implementa `on_disable()` per cleanup
   - Implementa `get_menu_actions()` per aggiungere azioni al menu
   - Implementa `create_plugin()` come factory function

4. **Testa il plugin**:
   - Vai in Impostazioni  Plugin  Disponibili
   - Clicca " Aggiorna Marketplace"
   - Installa il tuo plugin
   - Attivalo dal tab "Installati"

## Metodi Disponibili

### `on_enable() -> bool`
Chiamato quando il plugin viene attivato. Usa questo metodo per inizializzare risorse, caricare configurazioni, etc.

### `on_disable() -> bool`
Chiamato quando il plugin viene disattivato. Usa questo metodo per fare cleanup, salvare stati, etc.

### `get_menu_actions() -> list`
Restituisce lista di azioni da aggiungere al menu dell'applicazione:
```python
[
    {
        'name': 'Nome Azione',
        'callback': self.my_function,
        'shortcut': 'Ctrl+Alt+X'  # Opzionale
    }
]
```

## Logging

Usa il logger per debugging:
```python
from src.logger import get_logger
logger = get_logger(__name__)

logger.info("Messaggio informativo")
logger.warning("Messaggio di warning")
logger.error("Messaggio di errore")
```

## Accesso a Database e UI

Il plugin ha accesso a:
- `self.app`: Istanza dell'applicazione principale
- Database tramite `src.database.manga_manager` e `chapter_manager`
- UI tramite PyQt5

## Best Practices

1.  Sempre gestire eccezioni nei tuoi metodi
2.  Usare logging invece di print()
3.  Testare compatibilità con `requires_version`
4.  Documentare il codice con docstring
5.  Non modificare file di sistema o database senza conferma utente
