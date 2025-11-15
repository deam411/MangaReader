# Ladro di Copertine Mangaworld

Questo è un'applicazione desktop Python che ti permette di cercare e scaricare le copertine dei volumi dei manga da Mangaworld.

## Funzionalità

*   **Ricerca Manga:** Inserisci l'URL di un manga di Mangaworld e premi Invio per visualizzare le copertine disponibili.
*   **Anteprima Copertine:** Visualizza le anteprime delle copertine dei volumi.
*   **Selezione Intuitiva:** Clicca su qualsiasi punto della riga di una copertina (immagine, testo, spazio) per selezionarla/deselezionarla.
*   **Download Immediato:** Premi Invio (dopo aver selezionato le copertine) per scaricare tutte le copertine selezionate in una cartella a tua scelta.
*   **Modalità a Schermo Intero:** L'applicazione si avvia in modalità a schermo intero per un'esperienza immersiva.
*   **Chiusura Rapida:** Premi il tasto `Esc` per chiudere l'applicazione in qualsiasi momento.

## Installazione

1.  **Clona o scarica** questo repository sul tuo computer.
2.  **Naviga nella cartella del progetto** tramite il terminale:
    ```bash
    cd "C:\Users\Alessandro\Documents\Ladro di copertine mangaworld\mangaworld-cover-downloader"
    ```
3.  **Crea un ambiente virtuale** (consigliato):
    ```bash
    python -m venv .venv
    ```
4.  **Attiva l'ambiente virtuale**:
    *   Su Windows:
        ```bash
        .venv\Scripts\activate
        ```
    *   Su macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
5.  **Installa le dipendenze necessarie**:
    ```bash
    pip install customtkinter Pillow requests beautifulsoup4
    ```

## Utilizzo

1.  **Avvia l'applicazione** dal terminale (assicurati che l'ambiente virtuale sia attivo):
    ```bash
    python main.py
    ```
2.  **Inserisci l'URL del manga** di Mangaworld nel campo di testo in alto e premi `Invio`.
3.  L'applicazione caricherà e visualizzerà le anteprime delle copertine.
4.  **Seleziona le copertine** che desideri scaricare cliccando su di esse.
5.  **Premi `Invio`** per avviare il download delle copertine selezionate. Ti verrà chiesto di scegliere una cartella di destinazione.
6.  Per uscire dall'applicazione, premi il tasto `Esc`.
