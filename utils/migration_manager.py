"""
Gestionnaire de migrations pour l'application
"""
import os
from datetime import datetime  # Ajout de cet import manquant
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from config.app_config import DB_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


class MigrationManager:
    """Gestionnaire centralisé des migrations de base de données"""

    def __init__(self, db_path: Path, alembic_ini_path: str = "alembic.ini"):
        """
        Initialise le gestionnaire de migrations

        Args:
            db_path: Chemin vers la base de données
            alembic_ini_path: Chemin vers le fichier alembic.ini
        """
        self.db_path = db_path
        self.alembic_ini_path = alembic_ini_path

        # Vérifier que le fichier alembic.ini existe
        if not os.path.exists(alembic_ini_path):
            logger.error(f"Fichier de configuration Alembic introuvable: {alembic_ini_path}")
            raise FileNotFoundError(f"Fichier Alembic introuvable: {alembic_ini_path}")

    def get_alembic_config(self) -> Config:
        """
        Récupère la configuration Alembic

        Returns:
            Configuration Alembic
        """
        return Config(self.alembic_ini_path)

    def create_migration(self, message: str, autogenerate: bool = True) -> str:
        """
        Crée une nouvelle migration

        Args:
            message: Message décrivant la migration
            autogenerate: Si True, génère automatiquement la migration en fonction des différences

        Returns:
            ID de la révision créée
        """
        try:
            cfg = self.get_alembic_config()

            if autogenerate:
                # Génération automatique basée sur les modèles SQLAlchemy
                rev = command.revision(cfg, message=message, autogenerate=True)
            else:
                # Création d'une migration vide
                rev = command.revision(cfg, message=message, autogenerate=False)

            logger.info(f"Migration créée: {message}")
            return rev.revision

        except Exception as e:
            logger.error(f"Erreur lors de la création de la migration: {str(e)}")
            raise

    def upgrade_database(self, target: str = "head") -> bool:
        """
        Met à jour la base de données vers une version spécifique

        Args:
            target: Version cible ("head" pour la dernière version)

        Returns:
            True si la mise à jour a réussi, False sinon
        """
        try:
            # Vérifier d'abord s'il y a des migrations à appliquer
            current_version = self.get_current_version()

            # Obtenir la version cible
            cfg = self.get_alembic_config()
            script_directory = ScriptDirectory.from_config(cfg)

            if target == "head":
                target_revision = script_directory.get_current_head()
            else:
                target_revision = target

            # Vérifier si la migration est nécessaire
            if current_version == target_revision:
                logger.info(
                    f"La base de données est déjà à jour (version: {current_version}). Aucune migration nécessaire.")
                return True

            # Créer un backup avant migration seulement si des migrations sont nécessaires
            from services.backup_service import BackupService
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = BackupService.create_backup(
                str(self.db_path),
                output_path=str(self.db_path.parent / f"pre_migration_{backup_timestamp}.zip.enc")
            )
            if not backup_path:
                logger.warning("Impossible de créer un backup avant migration")
            else:
                logger.info(f"Backup avant migration créé: {backup_path}")

            # Procéder à la migration
            command.upgrade(cfg, target)
            logger.info(f"Base de données mise à jour vers la version: {target}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la base de données: {str(e)}")
            return False

    def downgrade_database(self, target: str) -> bool:
        """
        Rétrograde la base de données vers une version spécifique

        Args:
            target: Version cible

        Returns:
            True si la rétrogradation a réussi, False sinon
        """
        try:
            # Créer un backup avant downgrade (encore plus important que pour upgrade)
            from services.backup_service import BackupService
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = BackupService.create_backup(
                str(self.db_path),
                output_path=str(self.db_path.parent / f"pre_downgrade_{backup_timestamp}.zip.enc")
            )
            if not backup_path:
                logger.warning("Impossible de créer un backup avant downgrade")
            else:
                logger.info(f"Backup avant downgrade créé: {backup_path}")

            cfg = self.get_alembic_config()
            command.downgrade(cfg, target)
            logger.info(f"Base de données rétrogradée vers la version: {target}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la rétrogradation de la base de données: {str(e)}")
            return False

    def get_current_version(self) -> str:
        """
        Récupère la version actuelle de la base de données

        Returns:
            Version actuelle ou None si aucune migration n'a été appliquée
        """
        try:
            # Cette opération nécessite une base existante
            if not self.db_path.exists():
                logger.info("La base de données n'existe pas encore")
                return None

            # Utiliser SQLAlchemy pour accéder à la table alembic_version
            from sqlalchemy import create_engine, text, inspect
            from sqlalchemy.exc import SQLAlchemyError

            # Créer un moteur connecté à la base existante
            engine = create_engine(f"sqlite:///{self.db_path}")

            try:
                with engine.connect() as connection:
                    # Vérifier si la table alembic_version existe
                    inspector = inspect(engine)
                    if "alembic_version" not in inspector.get_table_names():
                        logger.info("La table alembic_version n'existe pas")
                        return None

                    # Récupérer la version
                    result = connection.execute(text("SELECT version_num FROM alembic_version"))
                    row = result.fetchone()

                    version = row[0] if row else None

                    if version:
                        logger.info(f"Version actuelle de la migration: {version}")
                    else:
                        logger.info("La table alembic_version existe mais est vide")

                    return version

            except SQLAlchemyError as e:
                logger.error(f"Erreur SQLAlchemy: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la version: {str(e)}")
            return None

    def get_available_migrations(self) -> list:
        """
        Récupère la liste des migrations disponibles

        Returns:
            Liste des révisions disponibles
        """
        try:
            cfg = self.get_alembic_config()
            script_directory = ScriptDirectory.from_config(cfg)
            return script_directory.get_revisions("head")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des migrations disponibles: {str(e)}")
            return []

    def check_migration_compatibility(self) -> bool:
        """
        Vérifie que les migrations sont compatibles avec la base de données actuelle

        Returns:
            True si les migrations sont compatibles, False sinon
        """
        try:
            if not self.db_path.exists():
                return True  # Pas de base de données, compatibilité par défaut

            current_version = self.get_current_version()
            if not current_version:
                return True  # Pas de version, compatibilité par défaut

            # Vérifier si la migration existe
            cfg = self.get_alembic_config()
            script_directory = ScriptDirectory.from_config(cfg)

            try:
                script_directory.get_revision(current_version)
                return True  # La migration existe
            except Exception:
                logger.error(f"La version de migration {current_version} n'existe pas dans les scripts disponibles")
                return False

        except Exception as e:
            logger.error(f"Erreur lors de la vérification de compatibilité des migrations: {str(e)}")
            return False

    def initialize_database(self) -> bool:
        """
        Initialise la base de données avec la dernière version des migrations

        Returns:
            True si l'initialisation a réussi, False sinon
        """
        try:
            # CORRECTION: Ne pas vérifier si la base existe d'abord, upgrade va la créer au besoin
            logger.info("Initialisation de la base de données...")

            # Appliquer les migrations
            cfg = self.get_alembic_config()
            command.upgrade(cfg, "head")

            logger.info("Base de données initialisée avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
            return False


# Créer une instance singleton du gestionnaire
migration_manager = MigrationManager(DB_PATH)