#!/usr/bin/env python
"""
Script per eseguire tutti i test e mostrare un report completo degli errori.

Usage:
    python run_all_tests.py
    python run_all_tests.py -v  # Verbose mode
    python run_all_tests.py --quick  # Solo test rapidi, salta test lenti
"""
import sys
import subprocess
import os


def run_tests(verbose=False, quick=False):
    """
    Esegue tutti i test e mostra report completo.

    Args:
        verbose: Se True, mostra output dettagliato
        quick: Se True, salta test lenti (marcati con @pytest.mark.slow)

    Returns:
        int: Exit code (0 = success, >0 = failures)
    """
    print("=" * 80)
    print("  ESECUZIONE TEST SUITE COMPLETA - MangaReader v0.3.0")
    print("=" * 80)
    print()

    # Costruisci comando pytest
    cmd = ["python", "-m", "pytest", "tests/"]

    # Opzioni pytest
    pytest_args = [
        "-v",  # Verbose
        "--tb=short",  # Traceback breve
        "--color=yes",  # Output colorato
        "-ra",  # Mostra summary di tutti i test (passed, failed, skipped, etc)
        "--strict-markers",  # Errore se marker non definito
    ]

    if verbose:
        pytest_args.extend([
            "-vv",  # Extra verbose
            "--tb=long",  # Traceback completo
        ])

    if quick:
        pytest_args.append("-m")
        pytest_args.append("not slow")
        print("Modalità QUICK: saltando test lenti...")
        print()

    cmd.extend(pytest_args)

    # Esegui pytest
    try:
        result = subprocess.run(cmd, cwd=os.path.dirname(__file__) or ".")

        print()
        print("=" * 80)

        if result.returncode == 0:
            print("  ✓ TUTTI I TEST SONO PASSATI!")
        elif result.returncode == 1:
            print("  ✗ ALCUNI TEST SONO FALLITI")
        elif result.returncode == 2:
            print("  ✗ ERRORE DI ESECUZIONE TEST (es. syntax error)")
        elif result.returncode == 3:
            print("  ⚠ TEST INTERROTTI DALL'UTENTE")
        elif result.returncode == 4:
            print("  ✗ ERRORE INTERNO DI PYTEST")
        elif result.returncode == 5:
            print("  ⚠ NESSUN TEST TROVATO")

        print("=" * 80)
        print()

        return result.returncode

    except FileNotFoundError:
        print("ERRORE: pytest non trovato!")
        print("Installalo con: pip install pytest")
        return 1
    except KeyboardInterrupt:
        print("\n\nTest interrotti dall'utente.")
        return 3


def main():
    """Entry point dello script."""
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    quick = "--quick" in sys.argv

    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        return 0

    exit_code = run_tests(verbose=verbose, quick=quick)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
