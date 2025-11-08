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

**3. Mantenuto Onefile Mode con Fix**

**Configurazione**:
```python
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    [],
    upx=False,  # CRITICAL: UPX disabled to prevent DLL corruption
    # Singolo exe - preferenza utente
)
```

---

### 🎯 Fix Applicati

✅ **UPX Disabilitato** → previene corruzione DLL (fix principale)
✅ **Hidden imports completi** → tutte le dipendenze PyQt5/PIL
✅ **Onefile mantenuto** → semplicità distribuzione (singolo exe)

**Trade-off**:
⚠️ Exe più grande (~100-120 MB invece di ~70-80 MB)
✅ Ma nessuna cartella extra - singolo file come prima

---

### 📦 Build Output

**Prima** (con UPX):
```
dist/
└── MangaReader.exe  (~70-80 MB, con rischio corruzione DLL)
```

**Dopo** (senza UPX):
```
dist/
└── MangaReader.exe  (~100-120 MB, stabile e affidabile)
```

**Singolo file exe** - Nessuna cartella extra, distribuzione semplice.

---

### 🧪 Testing

**Build**:
```bash
pyinstaller BuildTools/manga_reader.spec --clean
```

**Run**:
```bash
dist/MangaReader.exe
```

**Verifica**:
- [ ] App si avvia senza errore DLL
- [ ] Tutte le funzionalità funzionano
- [ ] Auto-update funziona correttamente

---

### 📝 Files Changed

- `BuildTools/manga_reader.spec`:
  - Disabilitato UPX (upx=False) - **fix critico**
  - Aggiunti hidden imports PyQt5.QtPrintSupport, QtSvg
  - Aggiunti hidden imports PIL.Image, ImageQt
  - Mantenuto onefile mode (singolo exe)

**Commits**:
1. `1c532c5` - Fix: Risolto errore "Failed to load python DLL" in PyInstaller (UPX + hidden imports)
2. `7342ed2` - Revert: Torna a onefile mode mantenendo fix UPX

---

### 🚀 Deployment

**Distribuzione**:
Singolo file exe, come prima:

```
MangaReader-v0.1.5.1-Windows.exe
```

**Installazione utente**:
1. Download exe
2. Lancia direttamente

**Workflow GitHub Actions**:
Nessuna modifica necessaria - workflow esistente funziona come prima.

---

### 📚 Note Tecniche

**Perché disabilitare UPX**:
- UPX comprime gli eseguibili per ridurre dimensione
- Su Windows, può corrompere DLL PyQt5 e Python durante compressione
- L'errore `python311.dll` è causato principalmente da UPX
- Disabilitarlo aumenta dimensione (~40%) ma garantisce stabilità

**Onefile vs Onedir**:
- **Scelta**: Onefile mantenuto per semplicità distribuzione
- **Trade-off**: Exe più grande ma singolo file
- **Rischio residuo**: Estrazione in Temp potrebbe ancora dare problemi con alcuni antivirus
- **Se problemi persistono**: Considerare passaggio futuro a onedir

**Compatibilità**:
- Windows 10/11: ✅
- Auto-update esistente: ✅
- Portable: ✅ (singolo exe)

---

## Summary

Questo hotfix risolve l'errore `python311.dll` **disabilitando UPX compression** e aggiungendo hidden imports completi.

Mantenuta modalità onefile (singolo exe) per semplicità distribuzione.

**Ready for testing!** 🚀
