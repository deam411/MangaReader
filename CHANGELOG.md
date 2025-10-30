# Changelog - Manga Reader

## [0.0.3] - 2025-10-30

### Nuove Funzionalità
- **Sistema di Temi**: Aggiunto supporto per temi chiaro e scuro
  - Tema scuro di default con colori ottimizzati
  - Tema chiaro disponibile nelle impostazioni
  - Cambio tema applicato a tutta l'applicazione

- **Libreria Personalizzabile**:
  - Possibilità di scegliere la posizione della directory della libreria
  - Previene l'appesantimento dell'eseguibile
  - Directory configurabile tramite dialog delle impostazioni

- **Sistema di Settings Persistenti**:
  - Impostazioni salvate in formato JSON
  - Dialog impostazioni con tab organizzati (Generale, Aspetto, Performance)
  - Possibilità di ripristinare impostazioni di default

- **Shortcuts da Tastiera**:
  - `Ctrl+F`: Focus sulla barra di ricerca
  - `Ctrl+I`: Importa manga
  - `Ctrl+E`: Esporta manga
  - `Ctrl+N`: Crea nuovo manga
  - `F5`: Aggiorna libreria
  - `F11`: Toggle fullscreen
  - `Backspace`: Torna indietro
  - `Esc`: Esci dall'applicazione

### Miglioramenti

- **Performance Ottimizzate**:
  - Implementato sistema di cache LRU per le immagini
  - Preloading intelligente delle pagine successive
  - Cache configurabile (10-200 immagini)
  - Lazy loading migliorato con tracking delle pagine in caricamento

- **Gestione Errori Migliorata**:
  - Messaggi di errore più informativi e chiari
  - Rilevamento e notifica di file .manga corrotti
  - Gestione errori per directory mancanti o inaccessibili
  - Fallback automatici per situazioni di errore

- **UI/UX**:
  - Tooltips informativi su tutti i pulsanti con shortcuts
  - Barra informazioni in basso con scorciatoie principali
  - Messaggio di aiuto quando la libreria è vuota
  - Migliore feedback visivo durante le operazioni

### Correzioni
- Risolti problemi di caricamento con metadata mancanti
- Migliorata la gestione della memoria nel lettore di capitoli
- Corretta la gestione dei percorsi per la libreria custom
- Fix tema persistente nell'eseguibile compilato (ora salvato in AppData)
- Fix messaggio "libreria vuota" che appariva ripetutamente
- Fix percorsi per eseguibili compilati con PyInstaller
- Settings ora salvate in `%LOCALAPPDATA%\MangaReader` per vera persistenza

### Modifiche Tecniche
- Aggiunto modulo `src/settings.py` per gestione impostazioni
- Aggiunto modulo `src/settings_dialog.py` per UI impostazioni
- Migliorato `src/chapter_reader_window.py` con cache LRU
- Aggiornato `src/paths.py` per supporto libreria custom
- Estese funzionalità di `views.py` e `main.py`

---

## [0.0.1] - 2024

### Funzionalità Iniziali
- Lettore manga con formato .manga proprietario
- Gestione libreria con visualizzazione griglia/lista
- Editor manga con supporto volumi, capitoli e pagine
- Importazione/esportazione file .manga
- Ricerca e ordinamento manga
- Lettura a schermo intero con scrolling verticale
- Database SQLite embedded nei file .manga
