"""
Runtime hook per PyInstaller: Delay iniziale per antivirus.

Problema: Windows Defender scansiona i file appena estratti da onefile,
bloccando python311.dll durante il primo avvio.

Soluzione: Aspetta 2-3 secondi all'avvio per dare tempo all'antivirus
di finire la scansione prima di caricare le DLL critiche.

Questo hook viene eseguito PRIMA di qualsiasi import Python.
"""

import time
import sys
import os

# Solo su Windows e solo se stiamo eseguendo da _MEIPASS (onefile mode)
if sys.platform == 'win32' and hasattr(sys, '_MEIPASS'):
    # Delay di 2.5 secondi per dare tempo all'antivirus
    # Abbastanza breve da non infastidire l'utente,
    # abbastanza lungo per completare scansione DLL principali
    time.sleep(2.5)

    # Debug: verifica che le DLL siano accessibili
    dll_path = os.path.join(sys._MEIPASS, 'python311.dll')
    if os.path.exists(dll_path):
        # DLL trovata, possiamo procedere
        pass
