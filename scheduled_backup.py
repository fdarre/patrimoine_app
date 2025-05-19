"""
Script de sauvegarde automatique avec rotation
"""
import os
import time
from datetime import datetime

from config.app_config import DATA_DIR
from services.backup_service import BackupService
from utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)


def run_scheduled_backup():
    """Exécute une sauvegarde programmée et maintient une rotation"""
    try:
        logger.info("Démarrage de la sauvegarde programmée...")
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

            # Créer également une copie de sauvegarde des fichiers .salt et .key
            salt_file = DATA_DIR / ".salt"
            key_file = DATA_DIR / ".key"
            backup_dir = DATA_DIR / "key_backups"
            backup_dir.mkdir(exist_ok=True)

            # Limiter ces sauvegardes à une par jour
            day_timestamp = datetime.now().strftime("%Y%m%d")
            salt_backup = backup_dir / f"salt_backup_{day_timestamp}"
            key_backup = backup_dir / f"key_backup_{day_timestamp}"

            # Créer les copies uniquement si elles n'existent pas déjà pour aujourd'hui
            if not salt_backup.exists() and salt_file.exists():
                try:
                    import shutil
                    shutil.copy2(salt_file, salt_backup)
                    logger.info(f"Copie de sauvegarde du sel créée: {salt_backup}")
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde du sel: {str(e)}")

            if not key_backup.exists() and key_file.exists():
                try:
                    import shutil
                    shutil.copy2(key_file, key_backup)
                    logger.info(f"Copie de sauvegarde de la clé créée: {key_backup}")
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde de la clé: {str(e)}")

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
