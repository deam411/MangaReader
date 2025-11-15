# Plugin Marketplace - Guida Setup

Questa guida spiega come creare un repository GitHub per ospitare plugin di MangaReader.

## Setup Repository Plugin Marketplace

### 1. Crea un nuovo repository GitHub

Crea un repository pubblico (es: `MangaReader-Plugins`)

### 2. Crea il file `plugins.json`

Nel repository, crea un file `plugins.json` nella root con la lista dei plugin disponibili:

```json
{
  "plugins": [
    {
      "id": "plugin-id",
      "name": "Nome Plugin",
      "version": "1.0.0",
      "author": "Tuo Nome",
      "description": "Descrizione del plugin",
      "download_url": "https://github.com/username/repo/releases/download/v1.0.0/plugin.zip",
      "requires_version": "0.5.0",
      "homepage": "https://github.com/username/repo"
    }
  ]
}
```

### 3. Prepara il plugin per il rilascio

Ogni plugin deve essere un archivio ZIP con questa struttura:

```
plugin-id.zip
 plugin.py          # File principale del plugin
 __init__.py        # (opzionale)
 ... altri file
```

**Importante**: Il nome della cartella estratta dallo ZIP deve corrispondere al `id` del plugin nel file `plugins.json`.

### 4. Crea una Release su GitHub

1. Vai su "Releases" nel tuo repository
2. Clicca "Create a new release"
3. Tag version: `v1.0.0` (deve corrispondere alla versione nel `plugins.json`)
4. Allega il file ZIP del plugin
5. Pubblica la release

Il `download_url` nel `plugins.json` deve puntare a questo file ZIP:
```
https://github.com/username/repo/releases/download/v1.0.0/plugin-id.zip
```

### 5. Configura l'URL del Marketplace

Di default, MangaReader cerca il file `plugins.json` qui:
```
https://raw.githubusercontent.com/deam411/MangaReader-Plugins/main/plugins.json
```

Per usare il tuo repository, modifica l'URL in `plugins/plugin_marketplace.py`:

```python
self.marketplace_url = "https://raw.githubusercontent.com/TUO_USERNAME/TUO_REPO/main/plugins.json"
```

## Campi del plugins.json

| Campo | Obbligatorio | Descrizione |
|-------|-------------|-------------|
| `id` |  | ID univoco del plugin (deve corrispondere al nome della cartella) |
| `name` |  | Nome visualizzato del plugin |
| `version` |  | Versione del plugin (formato: X.Y.Z) |
| `author` |  | Nome dell'autore |
| `description` |  | Descrizione breve del plugin |
| `download_url` |  | URL diretto al file ZIP del plugin |
| `requires_version` |  | Versione minima dell'app richiesta (default: "0.0.0") |
| `homepage` |  | URL della pagina del plugin |
| `icon_url` |  | URL dell'icona del plugin |

## Esempio Completo

Vedi `plugins_marketplace_example.json` per un esempio completo.

## Aggiornamento Plugin

Per aggiornare un plugin:

1. Incrementa la `version` nel `plugins.json`
2. Crea una nuova release su GitHub con il nuovo tag
3. Aggiorna il `download_url` per puntare alla nuova release

Gli utenti che hanno già installato il plugin vedranno "Aggiornamento disponibile" nella lista.

## Test

Per testare il marketplace localmente:

1. Avvia MangaReader
2. Vai in Impostazioni  Plugin
3. Clicca sul tab "Disponibili"
4. Clicca " Aggiorna Marketplace"
5. Dovresti vedere la lista dei plugin dal tuo repository

## Note

- I file ZIP devono contenere direttamente i file del plugin, non una cartella wrapping
- L'estrazione creerà automaticamente una cartella con nome `id` del plugin
- Il marketplace supporta solo ZIP e TAR.GZ
- URL HTTPS richiesto per sicurezza
