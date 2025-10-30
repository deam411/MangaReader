# 📚 Manga Reader

![Version](https://img.shields.io/badge/version-0.0.3-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Build](https://github.com/deam411/MangaReader/workflows/Build%20Multi-Platform/badge.svg)

Un lettore e gestore di manga moderno e performante con supporto multi-piattaforma.

## ✨ Funzionalità

### 📖 Lettura
- **Lettore full-screen** con scrolling verticale fluido
- **Lazy loading intelligente** per performance ottimali
- **Cache LRU** configurabile per caricamento rapido
- **Preloading** delle pagine successive

### 🎨 Interfaccia
- **Temi Dark/Light** con persistenza
- **Visualizzazione griglia/lista** per la libreria
- **Ricerca istantanea** tra i manga
- **Ordinamento** per titolo e autore

### ⚡ Performance
- **Cache immagini** configurabile (10-200 immagini)
- **Caricamento threaded** per UI responsive
- **Ottimizzazioni** per file manga di grandi dimensioni

### ⌨️ Shortcuts
- `Ctrl+F` - Ricerca
- `Ctrl+I` - Importa manga
- `Ctrl+E` - Esporta manga
- `Ctrl+N` - Nuovo manga
- `F5` - Aggiorna libreria
- `F11` - Toggle fullscreen
- `Backspace` - Indietro
- `Esc` - Esci

### 🛠️ Gestione
- **Import/Export** file .manga
- **Editor integrato** per creare e modificare manga
- **Libreria personalizzabile** - scegli dove salvare i tuoi manga
- **Formato .manga** proprietario basato su SQLite

## 📦 Download

### Rilasci Ufficiali

| Piattaforma | Download | Dimensione |
|------------|----------|-----------|
| 🪟 Windows | [MangaReader.exe](https://github.com/deam411/MangaReader/releases/latest/download/MangaReader.exe) | ~58 MB |
| 🍎 macOS | [MangaReader.dmg](https://github.com/deam411/MangaReader/releases/latest/download/MangaReader.dmg) | ~65 MB |
| 🐧 Linux | [MangaReader](https://github.com/deam411/MangaReader/releases/latest/download/MangaReader) | ~70 MB |

### Build Automatici

Ogni commit su `main` genera build automatici per tutte le piattaforme tramite GitHub Actions.
Scarica gli artifact dall'ultima [Action run](https://github.com/deam411/MangaReader/actions).

## 🚀 Installazione

### Windows
1. Scarica `MangaReader.exe`
2. Esegui il file (potrebbe apparire Windows Defender - clicca "Ulteriori informazioni" → "Esegui comunque")
3. Pronto!

### macOS
1. Scarica `MangaReader.dmg`
2. Apri il DMG e trascina l'app nella cartella Applicazioni
3. Al primo avvio: tasto destro → Apri (per bypassare Gatekeeper)
4. Pronto!

### Linux
1. Scarica `MangaReader`
2. Rendi eseguibile: `chmod +x MangaReader`
3. Esegui: `./MangaReader`
4. Pronto!

## 🔧 Build da Sorgente

### Requisiti
- Python 3.8+
- PyQt5
- Pillow

### Setup Ambiente

```bash
# Clone repository
git clone https://github.com/deam411/MangaReader.git
cd MangaReader

# Installa dipendenze
pip install -r requirements.txt
```

### Esecuzione in Sviluppo

```bash
python main.py
```

### Build Eseguibile

#### Windows
```cmd
cd BuildTools
build.bat
```

#### macOS
```bash
cd BuildTools
chmod +x build_mac.sh
./build_mac.sh
```

#### Linux
```bash
cd BuildTools
chmod +x build_linux.sh
./build_linux.sh
```

## 📂 Struttura Dati

### Impostazioni
```
Windows: %LOCALAPPDATA%\MangaReader\settings.json
macOS:   ~/.mangareader/settings.json
Linux:   ~/.mangareader/settings.json
```

### Libreria Manga
- **Default**: `[EXE Directory]/manga/`
- **Custom**: Configurabile nelle Impostazioni ⚙️

### Formato .manga
Ogni file `.manga` è un database SQLite contenente:
- Immagini delle pagine (BLOB)
- Metadata (titolo, autore, descrizione, tags)
- Struttura volumi e capitoli
- Cover immagini
- Cronologia di lettura (futuro)

## 🤝 Contribuire

Contributi benvenuti! Sentiti libero di aprire issue o pull request.

### Development Workflow

1. Fork il repository
2. Crea un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit le modifiche (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

### Guidelines

- Segui lo stile del codice esistente
- Aggiungi commenti per codice complesso
- Testa su almeno una piattaforma prima del PR
- Aggiorna CHANGELOG.md

## 📝 Changelog

Vedi [CHANGELOG.md](CHANGELOG.md) per la lista completa delle modifiche.

## 🐛 Bug Report

Hai trovato un bug? [Apri una issue](https://github.com/deam411/MangaReader/issues/new) con:
- Descrizione del problema
- Passi per riprodurlo
- Comportamento atteso vs attuale
- Screenshot (se applicabile)
- Sistema operativo e versione

## 💡 Feature Request

Hai un'idea? [Apri una issue](https://github.com/deam411/MangaReader/issues/new) con label `enhancement`.

## 📜 Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi [LICENSE](LICENSE) per dettagli.

## 🙏 Ringraziamenti

- PyQt5 per il framework GUI
- Pillow per elaborazione immagini
- PyInstaller per il packaging
- GitHub Actions per il CI/CD

## 📧 Contatti

- GitHub: [@deam411](https://github.com/deam411)
- Issues: [Manga Reader Issues](https://github.com/deam411/MangaReader/issues)

---

**Manga Reader** - Leggi i tuoi manga preferiti con stile! 📚✨
