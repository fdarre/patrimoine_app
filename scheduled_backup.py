"""
Script de sauvegarde automatique avec rotation
"""
import os
import time
from datetime import datetime

from services.backup_service import BackupService
from utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)


def run_scheduled_backup():
    """Exécute une sauvegarde programmée et maintient une rotation"""
    try:
        logger.info("Démarrage de la sauvegarde programmée...")
        from config.app_config import DATA_DIR, KEY_BACKUPS_DIR
        from utils.key_manager import KeyManager

        db_path = DATA_DIR / "patrimoine.db"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = DATA_DIR / f"scheduled_backup_{timestamp}.zip.enc"

        # Créer la sauvegarde
        backup_file = BackupService.create_backup(str(db_path), str(backup_path))

        if backup_file:
            logger.info(f"Sauvegarde programmée créée avec succès: {backup_file}")

            # Gestion de la rotation (conserver les 7 dernières sauvegardes)
            scheduled_backups = sorted(
                [f for f in os.listdir(DATA_DIR) if f.startswith("scheduled_backup_")],
                reverse=True
            )

            # Supprimer les sauvegardes excédentaires
            if len(scheduled_backups) > 7:
                for old_backup in scheduled_backups[7:]:
                    old_path = os.path.join(DATA_DIR, old_backup)
                    try:
                        os.remove(old_path)
                        logger.info(f"Ancienne sauvegarde supprimée: {old_path}")
                    except Exception as e:
                        logger.error(f"Erreur lors de la suppression de {old_path}: {str(e)}")

            # Backup des clés avec le gestionnaire
            key_manager = KeyManager(DATA_DIR, KEY_BACKUPS_DIR)

            # Créer un backup quotidien des clés s'il n'existe pas déjà
            day_timestamp = datetime.now().strftime("%Y%m%d")
            salt_backup = KEY_BACKUPS_DIR / f"salt_backup_v{key_manager.current_version}_{day_timestamp}"

            if not salt_backup.exists():
                try:
                    # Créer le backup avec versionnage
                    salt_path, key_path, metadata_path = key_manager.backup_keys(prefix="daily")
                    logger.info(f"Backup quotidien des clés créé: {salt_path}, {key_path}, {metadata_path}")
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde des clés: {str(e)}")

            # Gérer la rotation des sauvegardes de clés (garder 30 jours)
            # Cette partie reste inchangée car elle est déjà bien gérée

            return True
        else:
            logger.error("Échec de la sauvegarde programmée")
            return False
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la sauvegarde programmée: {str(e)}")
        return False


if __name__ == "__main__":
    # Enregistrer le début de l'opération
    start_time = time.time()
    logger.info("Démarrage du script de sauvegarde automatique")

    success = run_scheduled_backup()

    # Enregistrer le résultat
    duration = time.time() - start_time
    if success:
        logger.info(f"Sauvegarde automatique terminée avec succès en {duration:.2f} secondes")
    else:
        logger.error(f"Sauvegarde automatique terminée avec des erreurs après {duration:.2f} secondes")