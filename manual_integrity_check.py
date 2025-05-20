#!/usr/bin/env python
"""
Script pour exécuter la vérification d'intégrité de la base de données
Ce script peut être programmé comme tâche cron/planifiée pour vérification régulière
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire parent au chemin pour pouvoir importer les modules de l'application
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Imports de l'application
from database.db_config import get_db_session
from utils.logger import get_logger, setup_file_logging
from services.integrity_service import integrity_service
from services.backup_service import BackupService
from config.app_config import DB_PATH, LOGS_DIR

# Configurer le logger
logger = get_logger("integrity_check")


def main():
    """
    Fonction principale pour exécuter la vérification d'intégrité

    Ce script peut être exécuté en ligne de commande ou via une tâche planifiée
    pour vérifier régulièrement l'intégrité de la base de données.
    """
    # Assurer que le répertoire de logs existe
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Configurer le logging pour ce script
    setup_file_logging("integrity_check")

    logger.info("Démarrage de la vérification d'intégrité automatique")

    try:
        # Première étape: créer un backup de sécurité
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BackupService.create_backup(
            str(DB_PATH),
            output_path=str(Path(DB_PATH).parent / f"integrity_check_{backup_timestamp}.zip.enc")
        )

        if backup_path:
            logger.info(f"Backup de sécurité créé: {backup_path}")
        else:
            logger.warning("Impossible de créer un backup de sécurité avant vérification d'intégrité")

        # Seconde étape: exécuter la vérification d'intégrité
        with get_db_session() as db:
            logger.info("Exécution de la vérification d'intégrité de la base de données")
            integrity_check = integrity_service.verify_database_integrity(db)

            if integrity_check:
                logger.info("✅ Vérification d'intégrité réussie!")
                return 0  # Succès
            else:
                logger.error("❌ La vérification d'intégrité a échoué")

                # Exécuter un scan complet pour plus de détails sur les problèmes
                logger.info("Exécution d'un scan complet pour identifier les problèmes")
                scan_results = integrity_service.perform_complete_integrity_scan(db)

                if scan_results["corrupted"] > 0:
                    logger.error(
                        f"Scan complet: {scan_results['corrupted']} éléments corrompus détectés sur {scan_results['total_scanned']} éléments analysés")
                    for item in scan_results["corrupted_items"]:
                        logger.error(
                            f"Élément corrompu - Type: {item['type']}, ID: {item['id']}, Erreur: {item['error']}")
                else:
                    logger.warning(
                        f"Le scan complet n'a pas détecté de corruption, mais la vérification initiale a échoué")

                return 1  # Échec

    except Exception as e:
        logger.exception(f"Erreur inattendue lors de la vérification d'intégrité: {str(e)}")
        return 2  # Erreur


if __name__ == "__main__":
    sys.exit(main())
