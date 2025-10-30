# 🚀 Guida Setup GitHub e Build Automatici

Questa guida ti aiuterà a pubblicare il progetto su GitHub e configurare i build automatici multi-piattaforma.

## 📋 Prerequisiti

- Account GitHub (crea uno gratuito su [github.com](https://github.com))
- Git installato sul tuo computer
  - **Windows**: Scarica da [git-scm.com](https://git-scm.com/download/win)
  - **macOS**: Già incluso o installa con `brew install git`
  - **Linux**: `sudo apt-get install git` (Ubuntu/Debian)

## 📝 Parte 1: Creare il Repository GitHub

### 1.1 Crea il Repository

1. Vai su [github.com](https://github.com) ed effettua il login
2. Clicca sul pulsante **"+"** in alto a destra → **"New repository"**
3. Compila i campi:
   - **Repository name**: `MangaReader` (o il nome che preferisci)
   - **Description**: "Un lettore e gestore di manga moderno con supporto multi-piattaforma"
   - **Public** o **Private**: Scegli in base alle tue preferenze
   - **NON** selezionare "Initialize with README" (lo abbiamo già)
4. Clicca **"Create repository"**

### 1.2 Copia l'URL del Repository

Dopo aver creato il repository, vedrai una pagina con le istruzioni. Copia l'URL HTTPS che appare, sarà qualcosa come:
```
https://github.com/TUO-USERNAME/MangaReader.git
```

## 🔧 Parte 2: Configurare Git Locale

### 2.1 Apri il Terminale/Prompt dei Comandi

**Windows**:
- Premi `Win+R`, digita `cmd`, premi Invio
- Oppure cerca "Prompt dei comandi" nel menu Start

**macOS/Linux**:
- Apri Terminal

### 2.2 Naviga alla Cartella del Progetto

```bash
cd "C:\Users\aless\Downloads\Lettore .manga"
```

### 2.3 Configura Git (Se è la Prima Volta)

```bash
git config --global user.name "Il Tuo Nome"
git config --global user.email "tua.email@example.com"
```

Usa la stessa email del tuo account GitHub.

### 2.4 Inizializza il Repository Git

```bash
git init
```

### 2.5 Aggiungi Tutti i File

```bash
git add .
```

Questo comando aggiunge tutti i file del progetto (il `.gitignore` escluderà automaticamente i file non necessari).

### 2.6 Crea il Primo Commit

```bash
git commit -m "Initial commit - Manga Reader v0.0.3"
```

### 2.7 Collega al Repository Remoto

Sostituisci `TUO-USERNAME` con il tuo username GitHub:

```bash
git remote add origin https://github.com/TUO-USERNAME/MangaReader.git
```

### 2.8 Rinomina il Branch Principale (Se Necessario)

GitHub usa `main` come nome predefinito, assicuriamoci di essere allineati:

```bash
git branch -M main
```

### 2.9 Carica il Codice su GitHub

```bash
git push -u origin main
```

Ti verrà chiesto di autenticarti:
- **Username**: Il tuo username GitHub
- **Password**: Usa un **Personal Access Token** invece della password
  - Vai su GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  - Genera un nuovo token con scope `repo`
  - Copia e incolla il token come password

## 🎬 Parte 3: Verificare GitHub Actions

### 3.1 Controlla l'Esecuzione Automatica

1. Vai su GitHub, apri il tuo repository
2. Clicca sulla tab **"Actions"**
3. Dovresti vedere un workflow **"Build Multi-Platform"** in esecuzione
4. Clicca sul workflow per vedere i dettagli

Il workflow eseguirà 3 build in parallelo:
- 🪟 **Windows** (~5-8 minuti)
- 🍎 **macOS** (~8-12 minuti)
- 🐧 **Linux** (~5-8 minuti)

### 3.2 Verifica i Build Completati

Una volta completati (tutti i segni di spunta verdi ✓):

1. Clicca sul workflow completato
2. Scorri in basso fino a **"Artifacts"**
3. Vedrai 4 file scaricabili:
   - `MangaReader-Windows` (contiene MangaReader.exe)
   - `MangaReader-macOS-app` (contiene MangaReader.app)
   - `MangaReader-macOS-dmg` (contiene MangaReader.dmg)
   - `MangaReader-Linux` (contiene MangaReader)

### 3.3 Scarica e Testa

Scarica l'artifact per la tua piattaforma e testalo per assicurarti che funzioni correttamente.

## 🏷️ Parte 4: Creare una Release Ufficiale

I build automatici sono ottimi per il testing, ma per distribuire pubblicamente l'applicazione, è meglio creare una **Release**.

### 4.1 Crea un Tag di Versione

Nel terminale, nella cartella del progetto:

```bash
git tag v0.0.3
git push origin v0.0.3
```

### 4.2 GitHub Actions Crea Automaticamente la Release

Quando fai il push di un tag che inizia con `v`, il workflow:
1. Esegue tutti i build
2. Crea automaticamente una Release su GitHub
3. Allega tutti gli eseguibili alla release

### 4.3 Verifica la Release

1. Vai su GitHub, apri il tuo repository
2. Clicca sulla tab **"Releases"** (a destra, sotto "About")
3. Vedrai la release **v0.0.3** con i file allegati:
   - `MangaReader.exe` (Windows)
   - `MangaReader.dmg` (macOS)
   - `MangaReader` (Linux)

### 4.4 Modifica la Release (Opzionale)

Puoi cliccare **"Edit"** sulla release per:
- Aggiungere note di rilascio (changelog)
- Modificare il titolo
- Aggiungere screenshot

## 🔄 Parte 5: Workflow di Sviluppo Continuo

### 5.1 Modifiche Successive

Ogni volta che fai modifiche:

```bash
# Modifica i file del progetto
# Poi:

git add .
git commit -m "Descrizione delle modifiche"
git push
```

GitHub Actions eseguirà automaticamente i build dopo ogni push.

### 5.2 Creare Nuove Release

Quando sei pronto per una nuova versione:

1. Aggiorna il numero di versione nel codice:
   - `views.py`: `APP_VERSION = "0.0.4"`
   - `README.md`: Badge versione
   - `BuildTools/build_*.sh`: Echo messaggi

2. Commit le modifiche:
```bash
git add .
git commit -m "Bump version to 0.0.4"
git push
```

3. Crea e pusha il tag:
```bash
git tag v0.0.4
git push origin v0.0.4
```

## 📊 Parte 6: Aggiornare i Badge nel README

### 6.1 Sostituisci i Placeholder

Nel file `README.md`, sostituisci `TUOUSERNAME` con il tuo vero username GitHub in:

- Link ai badge
- Link ai download
- Link alle issues
- Link al profilo

Esempio:
```markdown
# Prima
![Build](https://github.com/TUOUSERNAME/MangaReader/workflows/Build%20Multi-Platform/badge.svg)

# Dopo (se il tuo username è "mario")
![Build](https://github.com/mario/MangaReader/workflows/Build%20Multi-Platform/badge.svg)
```

### 6.2 Commit le Modifiche

```bash
git add README.md
git commit -m "Update GitHub username in README"
git push
```

## 🐛 Troubleshooting

### Problema: Build Fallisce su macOS

**Errore**: "iconutil: command not found"

**Soluzione**: Il build su macOS richiede che l'iconset venga convertito in .icns. Questo avviene automaticamente nel workflow GitHub Actions su runner macOS. Se vuoi buildare localmente su macOS:

```bash
cd BuildTools
chmod +x build_mac.sh
./build_mac.sh
```

### Problema: Build Fallisce su Linux

**Errore**: Mancano dipendenze Qt

**Soluzione**: Le dipendenze sono installate automaticamente nel workflow. Per build locali:

```bash
sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtsvg libxcb-xinerama0
```

### Problema: Push Rifiutato (Authentication Failed)

**Soluzione**: Usa un Personal Access Token invece della password:
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → Seleziona `repo` scope
3. Copia il token e usalo come password

### Problema: File Troppo Grandi

**Errore**: "remote: error: File xyz is 100.00 MB; this exceeds GitHub's file size limit"

**Soluzione**: GitHub ha un limite di 100 MB per file. Non committare file .manga o build artefatti:
- Verifica che `.gitignore` escluda `*.manga`, `dist/`, `build/`
- Rimuovi file già committati: `git rm --cached file-grande.manga`

## 📚 Risorse Utili

- **Git Documentation**: [git-scm.com/doc](https://git-scm.com/doc)
- **GitHub Actions Docs**: [docs.github.com/actions](https://docs.github.com/en/actions)
- **PyInstaller Manual**: [pyinstaller.org](https://pyinstaller.org/en/stable/)
- **Markdown Guide**: [markdownguide.org](https://www.markdownguide.org/)

## ✅ Checklist Finale

Prima di considerare il setup completo:

- [ ] Repository GitHub creato
- [ ] Codice pushato su GitHub
- [ ] GitHub Actions eseguito con successo (tutti e 3 i build verdi)
- [ ] Artifacts scaricati e testati
- [ ] Tag v0.0.3 creato
- [ ] Release creata automaticamente su GitHub
- [ ] README.md aggiornato con username corretto
- [ ] Badge funzionanti nel README

## 🎉 Complimenti!

Hai configurato con successo un sistema di build e distribuzione professionale per il tuo Manga Reader! Ogni commit attiverà build automatici, e ogni tag di versione creerà una release pubblica.

Il tuo progetto è ora pronto per essere condiviso con il mondo! 🚀📚

---

**Note**: Se hai bisogno di aiuto o incontri problemi, puoi:
- Controllare i log dettagliati in GitHub Actions
- Cercare errori specifici nella documentazione di PyInstaller
- Aprire una issue nel repository per ricevere assistenza
