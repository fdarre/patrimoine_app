#!/usr/bin/env python
"""
Script d'initialisation des clés de chiffrement
À utiliser uniquement pour une nouvelle installation ou en cas de perte des clés
"""
import argparse
import sys
from pathlib import Path

# Ajouter le répertoire parent au chemin pour pouvoir importer les modules
sys.path.append(str(Path(__file__).parent))

from config.app_config import DATA_DIR, KEY_BACKUPS_DIR
from utils.key_manager import KeyManager
from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Initialise les clés de chiffrement pour l'application"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force l'écrasement des clés existantes (DANGER: rendra les données existantes irrécupérables)"
    )
    args = parser.parse_args()

    # Vérifier si les clés existent déjà
    key_manager = KeyManager(DATA_DIR, KEY_BACKUPS_DIR)
    if key_manager.check_keys_exist() and not args.force:
        print("Des fichiers de clés existent déjà.")
        confirm = input("Êtes-vous ABSOLUMENT CERTAIN de vouloir générer de nouvelles clés? (oui/NON): ")
        if confirm.lower() != "oui":
            print("Opération annulée.")
            return

        print("\n" + "*" * 80)
        print("AVERTISSEMENT: Vous êtes sur le point de créer de nouvelles clés.")
        print("TOUTES LES DONNÉES EXISTANTES SERONT IRRÉCUPÉRABLES!")
        print("*" * 80 + "\n")

        confirm_again = input("Tapez 'JE COMPRENDS LES RISQUES' pour continuer: ")
        if confirm_again != "JE COMPRENDS LES RISQUES":
            print("Opération annulée.")
            return

    # Initialiser les nouvelles clés
    new_key_manager = KeyManager.init_new_keys(DATA_DIR, force=args.force or False)

    if new_key_manager:
        print("Clés générées avec succès.")
        print(f"Les backups ont été créés dans: {KEY_BACKUPS_DIR}")
        print("\nIMPORTANT: Sauvegardez ces fichiers dans un endroit sûr:")
        print(f"  - {DATA_DIR / '.key'}")
        print(f"  - {DATA_DIR / '.salt'}")
        print(f"  - {DATA_DIR / '.key_metadata.json'}")
    else:
        print("Échec de l'initialisation des clés.")


if __name__ == "__main__":
    main()
