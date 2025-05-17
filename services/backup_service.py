"""
Service de sauvegarde chiffrée avec vérification d'intégrité
"""
import os
import zipfile
import shutil
import tempfile
import hashlib
import json
import logging
from datetime import datetime
from cryptography.fernet import Fernet

from utils.constants import DATA_DIR, SECRET_KEY
from database.db_config import get_encryption_key

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(DATA_DIR, 'backup.log')
)
logger = logging.getLogger('backup')

class BackupService:
    """Service pour la gestion des sauvegardes chiffrées avec vérification d'intégrité"""

    @staticmethod
    def generate_backup_key() -> bytes:
        """
        Génère une clé de chiffrement pour les sauvegardes basée sur la clé secrète

        Returns:
            Clé de chiffrement
        """
        # Réutiliser la fonction de la configuration DB pour consistance
        return get_encryption_key()

    @staticmethod
    def create_backup(db_path: str, output_path: str = None) -> str:
        """
        Crée une sauvegarde chiffrée de la base de données avec métadonnées et vérification d'intégrité

        Args:
            db_path: Chemin vers la base de données
            output_path: Chemin de sortie pour la sauvegarde (optionnel)

        Returns:
            Chemin vers le fichier de sauvegarde
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(DATA_DIR, f"backup_{timestamp}.zip.enc")

        # Créer un répertoire temporaire pour la sauvegarde
        with tempfile.TemporaryDirectory() as temp_dir:
            # Vérifier que la base de données existe
            if not os.path.exists(db_path):
                logger.error(f"La base de données {db_path} n'existe pas!")
                return None

            # Calculer le hash SHA-256 de la base de données pour vérification d'intégrité
            with open(db_path, 'rb') as f:
                db_hash = hashlib.sha256(f.read()).hexdigest()
                logger.info(f"Hash de la base de données: {db_hash}")

            # Copier la base de données dans le répertoire temporaire
            temp_db_path = os.path.join(temp_dir, os.path.basename(db_path))
            shutil.copy2(db_path, temp_db_path)

            # Créer un fichier de métadonnées
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "db_hash": db_hash,
                "version": "3.0",
                "description": "Sauvegarde chiffrée pour l'application de gestion patrimoniale"
            }

            metadata_path = os.path.join(temp_dir, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            # Créer un fichier zip pour la sauvegarde
            zip_path = os.path.join(temp_dir, "backup.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(temp_db_path, os.path.basename(db_path))
                zipf.write(metadata_path, "metadata.json")

            # Chiffrer le fichier zip
            key = BackupService.generate_backup_key()
            f = Fernet(key)

            try:
                with open(zip_path, 'rb') as file:
                    encrypted_data = f.encrypt(file.read())

                # Écrire les données chiffrées dans le fichier de sortie
                with open(output_path, 'wb') as file:
                    file.write(encrypted_data)

                logger.info(f"Sauvegarde créée avec succès: {output_path}")
                return output_path
            except Exception as e:
                logger.error(f"Erreur lors du chiffrement de la sauvegarde: {str(e)}")
                return None

    @staticmethod
    def restore_backup(backup_path: str, db_path: str) -> bool:
        """
        Restaure une sauvegarde chiffrée avec vérification d'intégrité

        Args:
            backup_path: Chemin vers le fichier de sauvegarde
            db_path: Chemin vers la base de données

        Returns:
            True si la restauration a réussi, False sinon
        """
        try:
            # Créer une sauvegarde de la base actuelle avant restauration
            if os.path.exists(db_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_before_restore = os.path.join(DATA_DIR, f"pre_restore_backup_{timestamp}.db")
                shutil.copy2(db_path, backup_before_restore)
                logger.info(f"Sauvegarde de sécurité créée: {backup_before_restore}")

            # Créer un répertoire temporaire pour la restauration
            with tempfile.TemporaryDirectory() as temp_dir:
                # Déchiffrer le fichier de sauvegarde
                key = BackupService.generate_backup_key()
                f = Fernet(key)

                try:
                    with open(backup_path, 'rb') as file:
                        encrypted_data = file.read()

                    decrypted_data = f.decrypt(encrypted_data)
                except Exception as e:
                    logger.error(f"Erreur lors du déchiffrement: {str(e)}")
                    return False

                # Écrire les données déchiffrées dans un fichier zip temporaire
                zip_path = os.path.join(temp_dir, "backup.zip")
                with open(zip_path, 'wb') as file:
                    file.write(decrypted_data)

                # Extraire le fichier zip
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(temp_dir)

                # Vérifier l'intégrité avec les métadonnées si disponibles
                metadata_path = os.path.join(temp_dir, "metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)

                    db_file = os.path.join(temp_dir, os.path.basename(db_path))
                    if os.path.exists(db_file):
                        with open(db_file, 'rb') as f:
                            actual_hash = hashlib.sha256(f.read()).hexdigest()

                        if metadata.get("db_hash") != actual_hash:
                            logger.error(f"Erreur d'intégrité: le hash de la base de données ne correspond pas!")
                            return False

                        logger.info("Vérification d'intégrité réussie")

                # Copier la base de données restaurée
                extracted_db_path = os.path.join(temp_dir, os.path.basename(db_path))
                shutil.copy2(extracted_db_path, db_path)
                logger.info("Restauration terminée avec succès")

            return True
        except Exception as e:
            logger.error(f"Erreur lors de la restauration: {str(e)}")
            return False