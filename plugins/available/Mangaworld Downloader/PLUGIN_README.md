# Mangaworld Downloader Plugin

Plugin ufficiale per Manga Reader che permette di scaricare manga direttamente da Mangaworld.ac e integrarli automaticamente nella tua libreria.

## Caratteristiche

- **Download Manga Completo**: Scarica manga completi da Mangaworld con un singolo URL
- **Download Volumi Selettivi**: Scegli esattamente quali volumi scaricare
- **Integrazione Database .manga**: I manga scaricati vengono automaticamente convertiti nel formato .manga
- **GUI Intuitiva**: Interfaccia grafica a schermo intero con anteprime delle copertine
- **Gestione Copertine**: Download automatico delle copertine dei volumi
- **Aggiunta Volumi**: Aggiungi nuovi volumi a file .manga esistenti

## Installazione

### Dipendenze

Il plugin richiede le seguenti dipendenze Python aggiuntive:

```bash
pip install customtkinter aiohttp beautifulsoup4 Pillow requests rich
```

### Installazione Plugin

1. Il plugin è già incluso nella directory `plugins/available/Mangaworld Downloader`
2. Assicurati che tutte le dipendenze siano installate
3. Avvia Manga Reader - il plugin verrà caricato automaticamente

## Utilizzo

### Accesso al Plugin

Il plugin aggiunge due menu items personalizzati al Manga Reader (se integrato nell'UI):

1. **Download from Mangaworld**: Apre la GUI del downloader
2. **Mangaworld Settings**: Mostra le impostazioni del plugin

### Download di un Manga Completo

1. Apri il downloader dal menu
2. Inserisci l'URL del manga di Mangaworld (es: `https://www.mangaworld.ac/manga/1234/nome-manga`)
3. Premi `Invio`
4. Il sistema scaricherà automaticamente:
   - Tutti i volumi del manga
   - Le copertine di ogni volume
   - Convertirà tutto in formato .manga

### Download Volumi Selettivi

1. Inserisci l'URL del manga
2. Premi `Invio` per visualizzare le anteprime delle copertine
3. Seleziona i volumi che desideri scaricare (clicca sulle righe)
4. Premi `Invio` di nuovo per avviare il download

### Aggiungere Volumi a File .manga Esistente

1. Clicca su "Seleziona File .manga"
2. Scegli il file .manga a cui vuoi aggiungere volumi
3. Inserisci:
   - Nome del nuovo volume (opzionale)
   - Numero del volume (es: `5` o `5-7` per un range)
   - URL MangaWorld del manga
4. Clicca "Aggiungi Volume a .manga"

## Configurazione

Il plugin supporta le seguenti opzioni di configurazione (gestite dal sistema plugin):

### `auto_import` (bool, default: True)
Importa automaticamente i manga scaricati nella libreria

### `download_path` (string, default: "")
Percorso personalizzato per i download (lascia vuoto per usare il percorso della libreria)

### `quality` (list: High/Medium/Low, default: High)
Qualità delle immagini scaricate

### `show_notifications` (bool, default: True)
Mostra notifiche al completamento dei download

### `convert_to_manga_format` (bool, default: True)
Converti automaticamente i manga scaricati in formato .manga

## Hook Eventi Utilizzati

Il plugin utilizza i seguenti hook del sistema plugin:

- `ON_STARTUP`: Inizializzazione del plugin all'avvio
- `ON_SHUTDOWN`: Pulizia delle risorse alla chiusura
- `ON_LIBRARY_REFRESH`: Log quando la libreria viene ricaricata
- `POST_IMPORT`: Conferma quando un manga viene importato

## Struttura Plugin

```
Mangaworld Downloader/
├── plugin.py                           # Plugin principale
├── __init__.py                         # Package init
├── main.py                             # GUI standalone
├── requirements.txt                    # Dipendenze Python
├── README.md                           # README originale
├── PLUGIN_README.md                    # Questa documentazione
│
├── manga_downloader_lib/               # Libreria download manga
│   ├── __init__.py
│   ├── manga_downloader.py             # Logica download principale
│   └── src/
│       ├── config.py                   # Configurazione
│       ├── crawler_utils.py            # Web crawling
│       ├── download_utils.py           # Utilities download
│       ├── file_utils.py               # Gestione file
│       ├── format_utils.py             # Formattazione
│       ├── general_utils.py            # Utilities generali
│       ├── pdf_generator.py            # Generazione PDF
│       └── progress_utils.py           # Progress tracking
│
└── manga_reader_db_integration/        # Integrazione database .manga
    ├── __init__.py
    ├── constants.py                    # Costanti
    ├── exceptions.py                   # Eccezioni custom
    ├── logger.py                       # Logging
    ├── paths.py                        # Gestione percorsi
    ├── database/                       # Database managers
    │   ├── connection.py               # Connessione DB
    │   ├── manager.py                  # Manager principale
    │   ├── base_manager.py             # Base manager
    │   ├── bookmark_manager.py         # Gestione bookmark
    │   ├── chapter_manager.py          # Gestione capitoli
    │   ├── history_manager.py          # Gestione cronologia
    │   └── metadata_manager.py         # Gestione metadata
    └── utils/
        └── validation.py               # Validazione dati
```

## Scorciatoie Tastiera (GUI Downloader)

- `Invio`: Cerca manga / Avvia download
- `Esc`: Chiudi applicazione
- `Click su riga`: Seleziona/deseleziona volume

## Limitazioni

- Funziona solo con Mangaworld.ac
- Richiede connessione internet attiva
- La velocità di download dipende dalla connessione e dal server di Mangaworld
- Le immagini vengono scaricate con la qualità originale del sito

## Troubleshooting

### Plugin non si carica

1. Verifica che tutte le dipendenze siano installate:
   ```bash
   pip install -r requirements.txt
   ```

2. Controlla i log del Manga Reader:
   ```
   INFO - plugins.plugin_manager - Plugin caricato: Mangaworld Downloader v1.0.0 by deam411
   ```

### Errore durante il download

- Verifica che l'URL del manga sia corretto
- Controlla che il manga esista ancora su Mangaworld
- Assicurati di avere spazio su disco sufficiente
- Verifica la connessione internet

### GUI non si apre

- Assicurati che `customtkinter` sia installato
- Verifica che non ci siano conflitti con altre GUI

## Sviluppo

### Struttura del Codice

Il plugin è composto da tre parti principali:

1. **plugin.py**: Integrazione con il sistema plugin di Manga Reader
2. **main.py**: GUI standalone con CustomTkinter
3. **manga_downloader_lib**: Logica di download e parsing
4. **manga_reader_db_integration**: Integrazione con il database .manga

### Estendere il Plugin

Per aggiungere nuove funzionalità:

1. Modifica `manga_downloader_lib` per nuove funzionalità di download
2. Aggiungi hook nel `plugin.py` per integrazione con Manga Reader
3. Estendi la GUI in `main.py` per nuovi controlli

## Crediti

- **Autore**: deam411
- **Versione**: 1.0.0
- **Richiede**: Manga Reader v0.3.0+
- **Repository**: https://github.com/deam411/Mangareader-Plugin

## Licenza

Questo plugin è distribuito sotto la stessa licenza del Manga Reader.

## Supporto

Per bug, richieste di funzionalità o domande:
- Apri una issue su: https://github.com/deam411/Mangareader-Plugin/issues
- Contatta: deam411

---

**Note**: Questo plugin è fornito "as-is" senza garanzie. Usa Mangaworld.ac in modo responsabile e rispetta i termini di servizio del sito.
