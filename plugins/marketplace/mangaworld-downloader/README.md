# MangaWorld Downloader Plugin

Plugin per scaricare manga direttamente da **MangaWorld** (mangaworld.ac) nel tuo MangaReader.

## Caratteristiche

✅ **Ricerca manga** - Cerca manga per titolo su MangaWorld
✅ **Lista capitoli** - Visualizza tutti i capitoli disponibili
✅ **Download multiplo** - Scarica capitoli singoli o tutti insieme
✅ **Progress tracking** - Barra di progresso per ogni download
✅ **Salvataggio automatico** - I capitoli vengono salvati direttamente nel database locale
✅ **Multi-threaded** - Download asincrono senza bloccare l'interfaccia

## Installazione

1. Vai in **Impostazioni → Plugin → Disponibili**
2. Clicca **"🔄 Aggiorna Marketplace"**
3. Seleziona **"MangaWorld Downloader"**
4. Clicca **"Installa"**
5. Vai nel tab **"Installati"** e attiva il plugin

## Utilizzo

### Aprire il Downloader

Dopo aver attivato il plugin, puoi aprire il downloader in due modi:

1. **Dal menu**: Menu → ⬇️ Scarica da MangaWorld
2. **Scorciatoia tastiera**: `Ctrl+M`

### Scaricare un Manga

1. **Cerca** il manga:
   - Inserisci il titolo nella barra di ricerca
   - Clicca "Cerca" o premi Enter
   - Attendi che vengano caricati i risultati

2. **Seleziona** il manga:
   - Clicca sul manga dalla lista dei risultati
   - Attendi che vengano caricati i capitoli disponibili

3. **Scarica** i capitoli:
   - **Singoli**: Seleziona uno o più capitoli (Ctrl+Click per selezione multipla)
   - **Tutti**: Clicca "⬇️ Scarica Tutti" per scaricare l'intera serie

4. **Attendi** il completamento:
   - La barra di progresso mostra l'avanzamento
   - I capitoli vengono salvati automaticamente nel database
   - Puoi leggere i capitoli scaricati dalla libreria principale

## Note Tecniche

### Funzionamento

Il plugin usa:
- **Web Scraping** per estrarre informazioni da MangaWorld
- **Regex** per parsing HTML (semplificato)
- **PyQt5 QThread** per download asincroni
- **Database Manager** per salvare i capitoli

### Limitazioni

⚠️ **MangaWorld cambia spesso dominio** - Se il plugin non funziona, potrebbe essere necessario aggiornare l'URL base nel codice

⚠️ **Rate limiting** - Non scaricare troppi capitoli contemporaneamente per evitare di essere bloccati

⚠️ **Parsing HTML** - Il plugin usa regex semplificati. Per maggiore robustezza, considera di installare BeautifulSoup4

### Aggiornamenti

Per aggiornare il plugin:
1. Disattiva il plugin dal tab "Installati"
2. Torna nel tab "Disponibili"
3. Clicca "🔄 Aggiorna Marketplace"
4. Reinstalla il plugin se disponibile una nuova versione

## Troubleshooting

**Problema**: Nessun risultato nella ricerca
**Soluzione**: Verifica la connessione internet e che MangaWorld sia online

**Problema**: Errore "Nessuna immagine trovata"
**Soluzione**: Il sito potrebbe aver cambiato struttura HTML. Segnala il problema

**Problema**: Download lento
**Soluzione**: Normale, dipende dalla velocità di connessione e dal server di MangaWorld

**Problema**: Errore durante il salvataggio
**Soluzione**: Verifica che il database non sia corrotto (usa Maintenance Tab)

## Sviluppo

Vuoi contribuire? Il codice è open source!

### Miglioramenti Possibili

- [ ] Supporto per BeautifulSoup4 per parsing robusto
- [ ] Download parallelo di più capitoli
- [ ] Cache dei risultati di ricerca
- [ ] Download immagini cover
- [ ] Supporto per altri siti di manga
- [ ] Filtri avanzati (genere, anno, stato)

### Struttura Codice

```python
MangaWorldSearchWorker      # Thread per ricerca manga
MangaWorldChapterWorker     # Thread per lista capitoli
MangaWorldDownloadWorker    # Thread per download capitolo
MangaWorldDownloaderDialog  # Interfaccia utente
MangaWorldDownloaderPlugin  # Plugin principale
```

## Licenza

Questo plugin è fornito "as-is" per uso personale. Il web scraping deve rispettare i termini di servizio del sito target.

## Crediti

Sviluppato da **MangaReader Team**
Versione: 1.0.0
Compatibilità: MangaReader v0.5.0+
