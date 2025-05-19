#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module pour générer ou restaurer les fichiers de clés nécessaires à l'application.
Ce script doit pouvoir s'exécuter même si les fichiers de clés n'existent pas encore.
"""

import base64
import logging
import secrets
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chemins des fichiers de clés
KEY_FILE = Path("config/security/.key")
SALT_FILE = Path("config/security/.salt")


def create_directories():
    """Crée les répertoires nécessaires s'ils n'existent pas."""
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Répertoire vérifié: {KEY_FILE.parent}")


def generate_salt():
    """Génère un nouveau sel cryptographique aléatoire."""
    return secrets.token_bytes(16)


def generate_key(salt):
    """Génère une nouvelle clé cryptographique basée sur un sel."""
    password = secrets.token_bytes(32)  # Mot de passe aléatoire de 32 octets
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def save_files(key, salt):
    """Sauvegarde la clé et le sel dans les fichiers appropriés."""
    try:
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(key)
        logger.info(f"Fichier de clé créé: {KEY_FILE}")

        with open(SALT_FILE, 'wb') as salt_file:
            salt_file.write(salt)
        logger.info(f"Fichier de sel créé: {SALT_FILE}")

        return True
    except Exception as e:
        logger.critical(f"Erreur lors de la sauvegarde des fichiers: {e}")
        return False


def check_existing_files():
    """Vérifie si les fichiers de clés existent déjà."""
    key_exists = KEY_FILE.exists()
    salt_exists = SALT_FILE.exists()

    if key_exists and salt_exists:
        logger.info("Les fichiers de clés existent déjà.")
        return True
    elif key_exists or salt_exists:
        # Si un seul des fichiers existe, c'est une situation incohérente
        logger.warning("État incohérent: certains fichiers de clés existent mais pas tous.")
        return False
    else:
        logger.info("Aucun fichier de clés n'existe encore.")
        return False


def main():
    """Fonction principale pour générer ou vérifier les fichiers de clés."""
    logger.info("Démarrage de l'initialisation des clés...")

    # Crée les répertoires nécessaires
    create_directories()

    # Vérifie si les fichiers existent déjà
    files_exist = check_existing_files()

    if files_exist:
        logger.info("Les fichiers de clés sont déjà initialisés.")
        print("Les fichiers de clés sont déjà initialisés et valides.")
        return True

    # Génère de nouvelles clés
    logger.info("Génération de nouvelles clés...")
    salt = generate_salt()
    key = generate_key(salt)

    # Sauvegarde les fichiers
    if save_files(key, salt):
        logger.info("Initialisation des clés réussie.")
        print("Les fichiers de clés ont été générés avec succès.")
        return True
    else:
        logger.critical("Échec de l'initialisation des clés.")
        print("ERREUR: Impossible de générer les fichiers de clés. Vérifiez les permissions.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"Exception non gérée: {e}")
        print(f"ERREUR CRITIQUE: {e}")
        sys.exit(1)
