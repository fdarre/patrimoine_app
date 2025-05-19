#!/usr/bin/env python
"""
Script d'initialisation des clés de chiffrement
À utiliser uniquement pour une nouvelle installation ou en cas de perte des clés
"""
import argparse
import json
import os
import secrets
from datetime import datetime
from pathlib import Path

# Définir les chemins directement sans importer app_config
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
KEY_BACKUPS_DIR = DATA_DIR / "key_backups"

# Assurer que les répertoires existent
DATA_DIR.mkdir(exist_ok=True)
KEY_BACKUPS_DIR.mkdir(exist_ok=True)

# Fichiers de clés
SALT_FILE = DATA_DIR / ".salt"
KEY_FILE = DATA_DIR / ".key"
METADATA_FILE = DATA_DIR / ".key_metadata.json"


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
    if (SALT_FILE.exists() or KEY_FILE.exists()) and not args.force:
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

    try:
        # Générer de nouvelles clés
        secret_key = secrets.token_bytes(32)
        encryption_salt = secrets.token_bytes(16)

        # Écrire les fichiers
        with open(KEY_FILE, "wb") as f:
            f.write(secret_key)
        with open(SALT_FILE, "wb") as f:
            f.write(encryption_salt)

        # Protéger les fichiers (Unix seulement)
        try:
            os.chmod(KEY_FILE, 0o600)
            os.chmod(SALT_FILE, 0o600)
        except Exception:
            pass

        # Créer les métadonnées
        metadata = {
            "version": 1,
            "creation_date": datetime.now().isoformat(),
            "last_verified": datetime.now().isoformat()
        }

        # Écrire les métadonnées
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2)

        try:
            os.chmod(METADATA_FILE, 0o600)
        except Exception:
            pass

        # Créer un backup initial
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_salt = KEY_BACKUPS_DIR / f"salt_backup_v1_initial_{backup_timestamp}"
        backup_key = KEY_BACKUPS_DIR / f"key_backup_v1_initial_{backup_timestamp}"
        backup_metadata = KEY_BACKUPS_DIR / f"metadata_backup_v1_initial_{backup_timestamp}"

        # Copier les fichiers pour le backup
        import shutil
        shutil.copy2(SALT_FILE, backup_salt)
        shutil.copy2(KEY_FILE, backup_key)
        shutil.copy2(METADATA_FILE, backup_metadata)

        print("Clés générées avec succès.")
        print(f"Les backups ont été créés dans: {KEY_BACKUPS_DIR}")
        print("\nIMPORTANT: Sauvegardez ces fichiers dans un endroit sûr:")
        print(f"  - {SALT_FILE}")
        print(f"  - {KEY_FILE}")
        print(f"  - {METADATA_FILE}")
    except Exception as e:
        print(f"Erreur lors de la génération des clés: {str(e)}")


if __name__ == "__main__":
    main()