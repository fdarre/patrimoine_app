#!/usr/bin/env python
"""
Script pour exécuter tous les tests unitaires avec rapport de couverture
"""
import subprocess
import sys
from pathlib import Path


def run_tests():
    """
    Exécute tous les tests unitaires et génère un rapport de couverture
    """
    print("=" * 80)
    print("Exécution des tests unitaires avec rapport de couverture")
    print("=" * 80)

    # Vérifier si pytest est installé
    try:
        import pytest
        import pytest_cov
    except ImportError:
        print("Erreur: pytest et/ou pytest-cov non installés.")
        print("Installez-les avec: pip install pytest pytest-cov")
        return 1

    # Répertoire des tests
    test_dir = Path(__file__).parent / "tests"
    if not test_dir.exists():
        print(f"Erreur: Répertoire de tests non trouvé: {test_dir}")
        return 1

    # Commande pytest avec couverture
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_dir),
        "--cov=.",
        "--cov-report=term",
        "--cov-report=html",
        "-v"
    ]

    # Exécuter la commande
    try:
        result = subprocess.run(cmd, check=False)

        # Afficher le chemin du rapport HTML
        if result.returncode == 0:
            html_report_dir = Path.cwd() / "htmlcov"
            print("\nRapport HTML généré dans:", html_report_dir)
            print("Ouvrez index.html dans ce répertoire pour visualiser le rapport complet")

        return result.returncode
    except Exception as e:
        print(f"Erreur lors de l'exécution des tests: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
