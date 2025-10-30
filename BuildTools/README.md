# 🎯 Build System - Manga Reader v0.0.1

Quick reference per compilare e distribuire Manga Reader.

## 📋 Quick Start

### Creare l'exe:
```bash
cd BuildTools
build.bat
```
**Output**: `dist/MangaReader.exe` (56 MB) con icona inclusa!

## 📁 File Importanti

| File | Descrizione |
|------|-------------|
| `build.bat` | Compila l'exe con icona |
| `manga_reader.spec` | Configurazione PyInstaller |
| `convert_to_ico.py` | Converte immagini in .ico |

## 🎨 Hai già l'icona!

L'icona è già configurata: `assets/icon.ico` ✅

## 🚀 Per compilare:

```bash
cd BuildTools
build.bat
```

L'exe sarà in: `dist/MangaReader.exe` con la tua icona!

## 🔄 Per aggiornare la versione:

1. Modifica `APP_VERSION` in `views.py`
2. Esegui `build.bat`
3. Distribuisci il nuovo exe!
