# Changelog - Manga Reader

## [0.0.4] - 2025-10-30

### Nuove Funzionalità
- **Zoom e Pan nel Lettore**:
  - Zoom in con freccia SU (↑) e zoom out con freccia GIÙ (↓)
  - Zoom fluido del 10% per pressione
  - Pan/trascinamento con click sinistro e drag
  - Scroll pagine con rotella del mouse o trackpad
  - Zoom fluido con limiti (0.1x - 5.0x)
  - Zoom centrato sul centro della viewport
  - **Pagine sempre centrate orizzontalmente** durante lo zoom
  - Transizione fluida senza flash grigio (ridimensionamento intelligente)
  - Cache automaticamente aggiornata durante lo zoom
  - Le frecce non scrollano più la pagina, sono dedicate allo zoom

- **Tema di Sistema**:
  - Rilevamento automatico del tema del sistema operativo
  - Supporto nativo per Windows (registro di sistema)
  - Fallback multi-piattaforma con Qt palette
  - Nuova opzione "Sistema" nelle impostazioni
  - Tema di sistema impostato come default

### Miglioramenti UI/UX
- **Icona Impostazioni Ingrandita**: L'icona ⚙ ora è più grande (40x40px) e più visibile
- **Cursore Visibile nel Lettore**: Rimosso il cursore nascosto per migliorare l'usabilità con zoom/pan
- **Interazione Migliorata**: Cursore cambia in "mano chiusa" durante il panning

### Modifiche Tecniche
- Aggiornata versione a 0.0.4 in tutti i file
- Modificato `src/chapter_reader_window.py` per supportare zoom e pan
- Modificato `main.py` con funzione `detect_system_theme()`
- Aggiornato `src/settings.py` per supportare tema "system"
- Aggiornato `src/settings_dialog.py` con opzione tema di sistema

---

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
