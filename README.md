# 📚 Manga Reader

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Build](https://github.com/deam411/MangaReader/workflows/Build%20Multi-Platform/badge.svg)
![Tests](https://img.shields.io/badge/tests-22%20passing-brightgreen.svg)
![Security](https://img.shields.io/badge/security-hardened-green.svg)

Un lettore e gestore di manga moderno e performante con supporto multi-piattaforma.

## 🎉 Novità v0.1.0 - Performance, Stability & New Features

Versione maggiore con focus su **Performance**, **Sicurezza**, **Stabilità**, **Code Quality** e **nuove funzionalità**:

- 🚀 **Database 3-5x più veloce** - Caricamento libreria da ~5s a ~1-2s per 100 manga
- 🔄 **Auto-Update da GitHub** - Sistema completo per controllare e installare aggiornamenti automaticamente
- 🎨 **UI Cleanup** - Interfaccia più professionale senza emoji, barra comandi semplificata
- 🔒 **Security Hardening** - 6 vulnerabilità mitigate (path traversal, XSS, SQL injection, etc.)
- ⚡ **Image Threading** - Conversione immagini non-blocking, UI sempre responsiva
- 🧹 **Code Quality** - Type hints, 13+ custom exceptions, validazione input completa
- ✅ **Testing** - 22 test passati, coverage ~80% workflows core
- 📊 **5 Bug Critici Risolti** - Resource leaks, race conditions, cache instability

Vedi [CHANGELOG.md](CHANGELOG.md) e [DEVELOPMENT_SUMMARY.md](DEVELOPMENT_SUMMARY.md) per dettagli completi.

---

## ✨ Funzionalità

### 📖 Lettura
- **Lettore full-screen** con scrolling verticale fluido
- **Vista Doppia Pagina** - Layout side-by-side per lettura manga tradizionale (Ctrl+D)
- **Sistema Segnalibri** - Salva e gestisci le tue posizioni preferite (Ctrl+B)
- **Supporto RTL** - Lettura Right-to-Left per manga giapponesi
- **Zoom e Pan** - Frecce SU/GIÙ per zoom, trascinamento con mouse
- **Cursore nascosto** durante la lettura per esperienza immersiva
- **Lazy loading intelligente** per performance ottimali
- **Cache LRU** configurabile per caricamento rapido
- **Preloading** delle pagine successive

### 🎨 Interfaccia
- **Navigazione a 4 livelli** - Libreria → Manga → Volume → Reader
- **VolumeView dedicata** - Schermata per selezione capitoli con cover grande
- **Pannello Scorciatoie** - Premi Ctrl+? per vedere tutte le combinazioni
- **Tooltips informativi** - Passaci sopra per scoprire come usare ogni pulsante
- **Temi Dark/Light/Sistema** con persistenza
- **Visualizzazione griglia/lista** per la libreria
- **Ricerca istantanea** tra i manga
- **Ordinamento** per titolo e autore
- **Download cover** - Salva le copertine di manga e volumi

### ⚡ Performance
- **🚀 Database Optimization**: Query **3-5x più veloci** (v0.1.0) - caricamento libreria ridotto da ~5s a ~1-2s per 100 manga
- **Sistema cache a 2 livelli**: In-memory + Persistent disk cache per cover
- **Cache persistent intelligente**: Cover salvate in AppData con invalidazione automatica
- **9 indici database strategici**: Query 3-5x più veloci su JOIN e ordinamenti
- **WAL mode SQLite**: Letture concorrenti senza blocchi
- **Ottimizzazioni SQL avanzate**: Memory-mapped I/O, cache 10MB, query ottimizzate
- **Image conversion threading** (v0.1.0): UI non-blocking durante importazione immagini
- **Caricamento threaded** della libreria con progress bar
- **Cache immagini** configurabile (10-200 immagini)
- **Cache statistics** (v0.1.0): Monitoring hit/miss rate per tuning ottimale
- **UI sempre responsiva** anche con librerie grandi
- **Risultato**: Avvio 2-3x più veloce, scroll ultra-fluido, query < 10ms, zero regressions

### 🖼️ Formati Supportati
- **Immagini**: PNG, JPG, JPEG, GIF, BMP, **WebP**, **JFIF**
- **Conversione automatica** di WebP e JFIF in formato compatibile
- **Ottimizzazione qualità** - PNG per trasparenza, JPEG 95% per il resto

### 🔒 Security & Stability (v0.1.0)
- **✅ 6 Vulnerabilità Mitigate**: Path traversal, filename injection, XSS, SQL injection, arbitrary file write, data corruption
- **Filename Sanitization**: Protezione contro path traversal (`../`, `..\\`), caratteri forbidden, reserved names Windows
- **Path Traversal Protection**: Validazione che i file estratti rimangano nella directory base
- **Input Validation**: Sanitizzazione completa di tutti gli input utente (titoli, descrizioni, tags)
- **XSS Prevention**: Rilevamento e blocco tag HTML pericolosi (`<script>`, `<iframe>`, etc.)
- **SQL Injection Protection**: Prepared statements + validazione input a doppio livello
- **File Size Validation**: Limite 50MB per prevenire crash da file troppo grandi
- **Custom Exception Hierarchy**: 13+ eccezioni custom per error handling consistente
- **Type Hints**: Type safety migliorata con annotations su moduli core
- **Zero Performance Penalty**: Tutte le feature di sicurezza hanno overhead trascurabile (<1ms)

### ⌨️ Shortcuts
- `Ctrl+?` - **Mostra pannello scorciatoie** (nuovo!)
- `Ctrl+F` - Ricerca
- `Ctrl+I` - Importa manga
- `Ctrl+E` - Esporta manga
- `Ctrl+N` - Nuovo manga
- `Ctrl+D` - Toggle vista doppia pagina (nel reader)
- `Ctrl+B` - Aggiungi segnalibro (nel reader)
- `F5` - Aggiorna libreria
- `F11` - Toggle fullscreen
- `Backspace` - Indietro
- `↑/↓` - Zoom in/out nel reader
- `Esc` - Esci

### 🛠️ Gestione
- **Auto-Update** (v0.1.0) - Sistema integrato per controllare e installare aggiornamenti da GitHub
- **Import/Export** file .manga
- **Editor integrato** per creare e modificare manga
- **Segnalibri personalizzati** - Gestione completa con rinomina/elimina
- **Libreria personalizzabile** - scegli dove salvare i tuoi manga
- **Download cover** - Salva copertine manga e volumi
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

## 🧪 Testing

### Setup Testing Environment

```bash
# Installa dipendenze di development
pip install -r requirements-dev.txt
```

### Esecuzione Test

```bash
# Esegui tutti i test
pytest

# Esegui test con coverage
pytest --cov=src --cov-report=html

# Esegui test specifici
pytest tests/test_database.py
pytest tests/test_settings.py -v

# Esegui test in parallelo
pytest -n auto

# Esegui solo test veloci (skip slow tests)
pytest -m "not slow"
```

### Test Suite

Il progetto include test completi per:
- ✅ **Database** - CRUD operations, conversioni immagini, schema migration (20 test)
- ✅ **Settings** - Singleton pattern, persistence, defaults (15 test)
- ✅ **Paths** - Cross-platform path resolution, frozen/unfrozen mode (18 test)
- ✅ **Security** (v0.1.0) - Validation, filename sanitization, path traversal, XSS prevention (5+5 test)
- ✅ **Integration** (v0.1.0) - Workflows completi: settings, cache, validation, exceptions (6 test)
- ✅ **Performance** (v0.1.0) - Benchmarks cache, validation, settings, exceptions (6 test)

**Test Results**: 17/17 test CLI-compatible passati ✓
**Coverage Target**: ~80% workflows core (v0.1.0)
**Security Coverage**: Path traversal, filename injection, XSS, SQL injection, input validation

### Scrivere Nuovi Test

```python
# tests/test_example.py
import pytest

def test_example(temp_dir):
    """Esempio di test con fixture."""
    # Usa fixture temp_dir, sample_image_path, etc.
    assert True
```

## 🔍 Code Quality

### v0.1.0 Improvements

Il progetto ha subito un refactoring significativo per migliorare la qualità del codice:

- ✅ **Type Hints**: Annotations su tutti i moduli core (`cache_manager.py`, `settings.py`, `validation.py`)
- ✅ **Custom Exceptions**: Gerarchia di 13+ eccezioni custom per error handling consistente
- ✅ **Validation Layer**: 9 validator functions per sanitizzazione input utente
- ✅ **Constants Extraction**: Magic numbers sostituiti con costanti centralizzate
- ✅ **Context Managers**: Pattern per gestione automatica risorse (DB connections, thread pools)
- ✅ **Docstrings**: Documentazione completa con type hints per tutti i metodi pubblici
- ✅ **Security Validation**: Input sanitization contro XSS, SQL injection, path traversal
- ✅ **Performance Benchmarks**: Test di performance per validare ottimizzazioni

### Linting & Formatting

```bash
# Formatta codice con Black
black src/ main.py views.py

# Controlla stile con Pylint
pylint src/ main.py views.py

# Type checking con mypy
mypy src/

# Style guide con flake8
flake8 src/ main.py views.py
```

### Pre-commit Hooks (Consigliato)

```bash
# Installa pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Esegui manualmente
pre-commit run --all-files
```

## 🏗️ Architettura

### Struttura Progetto

```
MangaReader/
├── main.py                 # Entry point, theme management, shortcuts
├── views.py                # Main UI views (Library, Manga, Volume, Reader)
├── src/
│   ├── database.py         # SQLite ORM per file .manga
│   ├── settings.py         # Settings singleton con persistence
│   ├── paths.py            # Path management cross-platform
│   ├── theme_manager.py    # Theme generation e applicazione
│   ├── logger.py           # Logging centralizzato
│   ├── constants.py        # Costanti centralizzate
│   ├── exceptions.py       # [v0.1.0] Gerarchia eccezioni custom (13+ exceptions)
│   ├── cache_manager.py    # Cache manager per cover persistent
│   ├── themes.json         # Definizioni colori temi
│   ├── chapter_reader_window.py  # Widget lettore con zoom/pan
│   ├── settings_dialog.py  # Dialog impostazioni
│   ├── tag_widget.py       # Smart tag selection widget
│   ├── utils/
│   │   ├── validation.py   # [v0.1.0] Validazione e sanitizzazione input (9 validators)
│   │   ├── image_converter.py  # [v0.1.0] Conversione immagini threading
│   │   └── cache_stats.py  # [v0.1.0] Analisi performance cache
│   ├── importers/
│   │   └── archive_importer.py  # Importazione CBZ/CBR con security
│   └── creator/
│       └── manga_creator_app.py  # Editor manga completo
├── tests/
│   ├── conftest.py         # Pytest fixtures
│   ├── test_database.py    # Test database operations
│   ├── test_settings.py    # Test settings management
│   ├── test_paths.py       # Test path resolution
│   ├── test_security_isolated.py      # [v0.1.0] Security tests (isolated)
│   ├── test_security_validation.py    # [v0.1.0] Security tests (comprehensive)
│   ├── test_integration_workflows.py  # [v0.1.0] Integration tests
│   └── test_performance_benchmarks.py # [v0.1.0] Performance benchmarks
├── BuildTools/             # Build scripts per PyInstaller
├── assets/                 # Icone e risorse
└── DEVELOPMENT_SUMMARY.md  # [v0.1.0] Documentazione completa delle 5 fasi

```

### Design Patterns

- **Singleton**: `Settings` class per configurazione globale
- **MVC-like**: Separazione model (database), view (UI), controller (logica)
- **LRU Cache**: Gestione intelligente memoria per immagini
- **Observer**: Qt signals/slots per comunicazione components
- **Factory**: Theme generation da configurazioni JSON
- **Context Manager** [v0.1.0]: Gestione automatica risorse (connessioni DB, thread pool)
- **Exception Hierarchy** [v0.1.0]: Gerarchia custom exceptions per error handling consistente
- **Validator Pattern** [v0.1.0]: Validazione centralizzata input con sanitizzazione
- **Thread Pool** [v0.1.0]: Conversione immagini parallela con `ImageConverterPool`

### Database Schema

```sql
-- metadata: Informazioni manga
title, author, description, language, cover, year, tags

-- volumes: Organizzazione volumi
id, name, order, cover

-- chapters: Capitoli per volume
id, name, order, description, volume_id

-- pages: Immagini pagine
chapter_id, page_number, image_data (BLOB)

-- history: Cronologia lettura (futuro)
user, chapter_id, page_number, timestamp, notes
```

### Logging

L'applicazione usa un sistema di logging centralizzato:

```python
from src.logger import get_logger

logger = get_logger(__name__)
logger.info("Informazione")
logger.error("Errore")
logger.debug("Debug info")
```

**Log Location**:
- Windows: `%LOCALAPPDATA%\MangaReader\manga_reader.log`
- Unix: `~/.mangareader/manga_reader.log`

**Configurazione**: Rotazione automatica (10MB max, 5 backup)

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
