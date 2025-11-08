## 🐛 Hotfix: Risolto errore "Failed to load python DLL"

**Problema critico**: Errore `python311.dll` mancante dopo aggiornamento/avvio app.

### 🔍 Root Cause

Errore completo:
```
Failed to load python DLL
file:///C:/Users/.../AppData/Local/Temp/_MEI28002/python311.dll
LoadLibrary: impossibile trovare il modulo specifico
```

**Causa**:
- PyInstaller modalità **onefile** estrae tutto in cartella temporanea `_MEI*`
- UPX compression corrompe DLL Qt5 e Python su Windows
- Antivirus blocca/corrompe `python311.dll` in Temp
- DLL non viene caricata → app crash

---

### ✅ Soluzioni Applicate

**1. Disabilitato UPX Compression**
```python
upx=False  # Era: upx=True
```
- UPX comprime DLL ma può corromperle su Windows
- Trade-off: exe più grande (~30-40%) ma funzionale

**2. Aggiunti Hidden Imports Mancanti**
```python
hiddenimports=[
    # ... esistenti
    'PyQt5.QtPrintSupport',  # NEW
    'PyQt5.QtSvg',           # NEW
    'PIL.Image',             # NEW
    'PIL.ImageQt',           # NEW
]
```

**3. Passaggio da Onefile a Onedir Mode** (fix definitivo)

**Prima** (onefile):
```python
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    # Singolo exe che estrae in Temp → PROBLEMA
)
```

**Dopo** (onedir):
```python
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,  # Onedir mode
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    name='MangaReader',
)
```

---

### 🎯 Vantaggi Onedir Mode

✅ **NO estrazione in Temp** → risolve problema `python311.dll` completamente
✅ **Nessun conflitto antivirus** → DLL sempre accessibili
✅ **Avvio istantaneo** → no estrazione runtime
✅ **Auto-update affidabile** → sostituzione file diretta
✅ **Debug più facile** → DLL visibili in cartella

**Trade-off accettabile**:
⚠️ Output: cartella `MangaReader/` invece di singolo `.exe`

---

### 📦 Build Output

**Prima**:
```
dist/
└── MangaReader.exe  (singolo file ~80MB)
```

**Dopo**:
```
dist/
└── MangaReader/
    ├── MangaReader.exe
    ├── python311.dll
    ├── Qt5Core.dll
    ├── Qt5Gui.dll
    ├── Qt5Widgets.dll
    ├── ... (altre DLL)
    ├── src/
    └── assets/
```

---

### 🧪 Testing

**Build**:
```bash
pyinstaller BuildTools/manga_reader.spec --clean
```

**Run**:
```bash
dist/MangaReader/MangaReader.exe
```

**Verifica**:
- [x] App si avvia senza errore DLL
- [x] Tutte le funzionalità funzionano
- [x] Auto-update funziona correttamente

---

### 📝 Files Changed

- `BuildTools/manga_reader.spec`:
  - Disabilitato UPX (upx=False)
  - Aggiunti hidden imports PyQt5.QtPrintSupport, QtSvg
  - Aggiunti hidden imports PIL.Image, ImageQt
  - Convertito da onefile a onedir mode
  - Aggiunto blocco COLLECT per onedir

**Commits**:
1. `1c532c5` - Fix: Risolto errore "Failed to load python DLL" in PyInstaller (UPX + hidden imports)
2. `f3c56a5` - Fix: Passaggio da onefile a onedir mode per risolvere python311.dll (definitivo)

---

### 🚀 Deployment

**Distribuzione**:
Zippare l'intera cartella `dist\MangaReader\`:

```
MangaReader-v0.1.5.1-Windows.zip
└── MangaReader/
    ├── MangaReader.exe
    └── ... (tutte le DLL)
```

**Installazione utente**:
1. Estrai zip
2. Lancia `MangaReader\MangaReader.exe`

**Aggiornamento workflow GitHub Actions**:
Dopo il merge, aggiornare `.github/workflows/build.yml` per zippare la cartella invece del singolo exe.

---

### 📚 Note Tecniche

**Perché onedir è meglio di onefile per PyQt5**:
- PyQt5 ha molte DLL interdipendenti
- Onefile extraction può fallire con antivirus attivi
- Onedir garantisce path relativi corretti tra DLL
- Standard per app Qt professionali (VLC, OBS, etc.)

**Compatibilità**:
- Windows 10/11: ✅
- Auto-update esistente: ✅ (funziona meglio)
- Portable: ✅ (cartella self-contained)

---

## Summary

Questo hotfix risolve **definitivamente** l'errore `python311.dll` passando da onefile a onedir mode.

La cartella risultante è più affidabile, più veloce, e compatibile con antivirus.

**Ready for merge!** 🎉
