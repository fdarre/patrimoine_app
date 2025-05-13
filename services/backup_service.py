"""
Service de sauvegarde chiffrée
"""
import os
import zipfile
import shutil
import tempfile
from datetime import datetime
from cryptography.fernet import Fernet

from utils.constants import DATA_DIR, SECRET_KEY

class BackupService:
    """Service pour la gestion des sauvegardes chiffrées"""

    @staticmethod
    def generate_backup_key() -> bytes:
        """
        Génère une clé de chiffrement pour les sauvegardes basée sur la clé secrète

        Returns:
            Clé de chiffrement
        """
        # Utiliser la clé secrète comme base pour le chiffrement des sauvegardes
        import base64
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        # Dériver une clé de 32 octets à partir de la clé secrète
        salt = b'Patrimoine_App_Salt'  # Sel statique pour la dérivation de clé
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
        return key

    @staticmethod
    def create_backup(db_path: str, output_path: str = None) -> str:
        """
        Crée une sauvegarde chiffrée de la base de données

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
            # Copier la base de données dans le répertoire temporaire
            temp_db_path = os.path.join(temp_dir, os.path.basename(db_path))
            shutil.copy2(db_path, temp_db_path)

            # Créer un fichier zip pour la sauvegarde
            zip_path = os.path.join(temp_dir, "backup.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(temp_db_path, os.path.basename(db_path))

            # Chiffrer le fichier zip
            key = BackupService.generate_backup_key()
            f = Fernet(key)

            with open(zip_path, 'rb') as file:
                encrypted_data = f.encrypt(file.read())

            # Écrire les données chiffrées dans le fichier de sortie
            with open(output_path, 'wb') as file:
                file.write(encrypted_data)

        return output_path

    @staticmethod
    def restore_backup(backup_path: str, db_path: str) -> bool:
        """
        Restaure une sauvegarde chiffrée

        Args:
            backup_path: Chemin vers le fichier de sauvegarde
            db_path: Chemin vers la base de données

        Returns:
            True si la restauration a réussi, False sinon
        """
        try:
            # Créer un répertoire temporaire pour la restauration
            with tempfile.TemporaryDirectory() as temp_dir:
                # Déchiffrer le fichier de sauvegarde
                key = BackupService.generate_backup_key()
                f = Fernet(key)

                with open(backup_path, 'rb') as file:
                    encrypted_data = file.read()

                decrypted_data = f.decrypt(encrypted_data)

                # Écrire les données déchiffrées dans un fichier zip temporaire
                zip_path = os.path.join(temp_dir, "backup.zip")
                with open(zip_path, 'wb') as file:
                    file.write(decrypted_data)

                # Extraire le fichier zip
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(temp_dir)

                # Copier la base de données restaurée
                extracted_db_path = os.path.join(temp_dir, os.path.basename(db_path))
                shutil.copy2(extracted_db_path, db_path)

            return True
        except Exception as e:
            print(f"Erreur lors de la restauration: {str(e)}")
            return False