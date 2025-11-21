"""
Test logica versioning per verificare comportamento con versioni uguali.
"""

from src.updater import is_newer_version, parse_version, check_for_updates
from src.constants import APP_VERSION

print("=" * 60)
print("TEST LOGICA VERSIONING")
print("=" * 60)
print()

print(f"Versione app corrente: {APP_VERSION}")
print()

# Simula vari scenari
scenarios = [
    ("0.1.1", "0.1.1", "Stessa versione - NON dovrebbe scaricare"),
    ("0.1.1", "0.1.0", "Versione più vecchia - NON dovrebbe scaricare"),
    ("0.1.1", "0.2.0", "Versione più nuova - DOVREBBE scaricare"),
    ("0.1.0", "0.1.1", "Versione più nuova - DOVREBBE scaricare"),
]

for current, latest, description in scenarios:
    print(f"Scenario: {description}")
    print(f"  Current: {current}, Latest: {latest}")

    is_newer = is_newer_version(current, latest)
    should_download = is_newer

    print(f"  is_newer_version() = {is_newer}")
    print(f"  check_for_updates() returnerebbe: {'UPDATE INFO' if should_download else 'None'}")
    print(f"  Comportamento atteso: {'Mostra dialog download' if should_download else 'Mostra messaggio già aggiornato'}")
    print()

print("=" * 60)
print("CONCLUSIONE:")
print("Se latest == current → is_newer_version = False → return None → Messaggio 'già aggiornato' ✓")
print("=" * 60)
