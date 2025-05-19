"""
Gestionnaire de clés de chiffrement avec versionnage
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional, Any

from utils.logger import get_logger

logger = get_logger(__name__)


class KeyManager:
    """Gestionnaire centralisé des clés de chiffrement avec versionnage"""

    def __init__(self, data_dir: Path, key_backups_dir: Path):
        """
        Initialise le gestionnaire de clés

        Args:
            data_dir: Répertoire des données
            key_backups_dir: Répertoire des backups de clés
        """
        self.data_dir = data_dir
        self.key_backups_dir = key_backups_dir
        self.key_backups_dir.mkdir(exist_ok=True)

        # Fichiers de clés
        self.salt_file = data_dir / ".salt"
        self.key_file = data_dir / ".key"
        self.metadata_file = data_dir / ".key_metadata.json"

        # Version par défaut
        self.current_version = 1
        self.creation_date = None
        self.last_verified = None

        # Charger ou créer les métadonnées
        self._load_or_create_metadata()

    def _load_or_create_metadata(self) -> Dict[str, Any]:
        """
        Charge ou crée les métadonnées des clés

        Returns:
            Dictionnaire des métadonnées
        """
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    metadata = json.load(f)

                self.current_version = metadata.get("version", 1)
                self.creation_date = metadata.get("creation_date")
                self.last_verified = metadata.get("last_verified")

                logger.info(f"Métadonnées des clés chargées: version {self.current_version}")
                return metadata
            except Exception as e:
                logger.error(f"Erreur lors du chargement des métadonnées de clés: {str(e)}")
                # Continuer et créer de nouvelles métadonnées

        # Créer de nouvelles métadonnées si le fichier n'existe pas ou est corrompu
        now = datetime.now().isoformat()
        metadata = {
            "version": self.current_version,
            "creation_date": now,
            "last_verified": now
        }

        # Sauvegarder les métadonnées
        self._save_metadata(metadata)
        return metadata

    def _save_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Sauvegarde les métadonnées des clés

        Args:
            metadata: Dictionnaire des métadonnées
        """
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            # Protéger le fichier (Unix seulement)
            try:
                os.chmod(self.metadata_file, 0o600)
            except Exception:
                pass

            logger.info(f"Métadonnées des clés sauvegardées: version {metadata.get('version', 1)}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des métadonnées de clés: {str(e)}")

    def check_keys_exist(self) -> bool:
        """
        Vérifie si les fichiers de clés existent

        Returns:
            True si les deux fichiers existent, False sinon
        """
        return self.salt_file.exists() and self.key_file.exists()

    def increment_version(self) -> int:
        """
        Incrémente la version des clés

        Returns:
            Nouvelle version
        """
        # Charger les métadonnées actuelles
        metadata = self._load_or_create_metadata()

        # Incrémenter la version
        self.current_version = metadata.get("version", 1) + 1
        metadata["version"] = self.current_version
        metadata["last_updated"] = datetime.now().isoformat()

        # Sauvegarder les métadonnées
        self._save_metadata(metadata)
        logger.info(f"Version des clés incrémentée à {self.current_version}")

        return self.current_version

    def backup_keys(self, prefix: str = "") -> Tuple[Path, Path, Path]:
        """
        Crée une sauvegarde des clés avec la version actuelle

        Args:
            prefix: Préfixe optionnel pour les noms de fichiers

        Returns:
            Tuple des chemins des backups (sel, clé, métadonnées)
        """
        if not self.check_keys_exist():
            logger.error("Impossible de sauvegarder les clés: fichiers manquants")
            raise FileNotFoundError("Les fichiers de clés n'existent pas")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_str = f"v{self.current_version}"

        # Créer les noms de fichiers
        if prefix:
            backup_prefix = f"{prefix}_{version_str}_{timestamp}"
        else:
            backup_prefix = f"{version_str}_{timestamp}"

        salt_backup = self.key_backups_dir / f"salt_backup_{backup_prefix}"
        key_backup = self.key_backups_dir / f"key_backup_{backup_prefix}"
        metadata_backup = self.key_backups_dir / f"metadata_backup_{backup_prefix}"

        # Copier les fichiers
        shutil.copy2(self.salt_file, salt_backup)
        shutil.copy2(self.key_file, key_backup)
        shutil.copy2(self.metadata_file, metadata_backup)

        # Protéger les fichiers
        for file_path in [salt_backup, key_backup, metadata_backup]:
            try:
                os.chmod(file_path, 0o600)
            except Exception:
                pass

        logger.info(f"Backup des clés créé: version {self.current_version}, préfixe '{prefix}'")
        return salt_backup, key_backup, metadata_backup

    def update_verification_timestamp(self) -> None:
        """Met à jour le timestamp de dernière vérification"""
        metadata = self._load_or_create_metadata()
        metadata["last_verified"] = datetime.now().isoformat()
        self._save_metadata(metadata)
        logger.info("Timestamp de vérification des clés mis à jour")

    def create_initial_keys_backup(self) -> None:
        """Crée un backup initial des clés qui ne sera jamais supprimé"""
        if not self.check_keys_exist():
            logger.error("Impossible de créer un backup initial: fichiers manquants")
            return

        # Créer les noms de fichiers
        version_str = f"v{self.current_version}"
        salt_backup = self.key_backups_dir / f"salt_backup_{version_str}_initial"
        key_backup = self.key_backups_dir / f"key_backup_{version_str}_initial"
        metadata_backup = self.key_backups_dir / f"metadata_backup_{version_str}_initial"

        # Copier les fichiers
        shutil.copy2(self.salt_file, salt_backup)
        shutil.copy2(self.key_file, key_backup)
        shutil.copy2(self.metadata_file, metadata_backup)

        # Protéger les fichiers
        for file_path in [salt_backup, key_backup, metadata_backup]:
            try:
                os.chmod(file_path, 0o600)
            except Exception:
                pass

        logger.info(f"Backup initial des clés créé: version {self.current_version}")

    @staticmethod
    def init_new_keys(data_dir: Path, force: bool = False) -> Optional['KeyManager']:
        """
        Initialise de nouvelles clés (à utiliser uniquement en ligne de commande)

        Args:
            data_dir: Répertoire des données
            force: Forcer l'écrasement des clés existantes

        Returns:
            Instance du KeyManager ou None si échec
        """
        import secrets

        salt_file = data_dir / ".salt"
        key_file = data_dir / ".key"
        metadata_file = data_dir / ".key_metadata.json"
        key_backups_dir = data_dir / "key_backups"
        key_backups_dir.mkdir(exist_ok=True)

        # Vérifier si les fichiers existent déjà
        if not force and (salt_file.exists() or key_file.exists()):
            logger.error("Des fichiers de clés existent déjà. Utilisez --force pour les écraser.")
            return None

        # Générer les nouvelles clés
        secret_key = secrets.token_bytes(32)
        encryption_salt = secrets.token_bytes(16)

        # Sauvegarder les nouvelles clés
        with open(key_file, "wb") as f:
            f.write(secret_key)
        with open(salt_file, "wb") as f:
            f.write(encryption_salt)

        # Protéger les fichiers
        try:
            os.chmod(key_file, 0o600)
            os.chmod(salt_file, 0o600)
        except Exception:
            pass

        # Créer le gestionnaire de clés
        key_manager = KeyManager(data_dir, key_backups_dir)

        # Créer le backup initial
        key_manager.create_initial_keys_backup()

        logger.info("Nouvelles clés générées et sauvegardées avec succès")
        return key_manager
