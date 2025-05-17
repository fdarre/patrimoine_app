"""
Utilitaire de journalisation centralisée
"""
import logging
import logging.config
import os
from datetime import datetime
from config.app_config import LOGGING_CONFIG, LOGS_DIR

# Configurer le logging
logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """
    Récupère un logger configuré pour le module spécifié

    Args:
        name: Nom du module (généralement __name__)

    Returns:
        Logger configuré
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, e: Exception, message: str = None):
    """
    Journalise une exception avec un message optionnel

    Args:
        logger: Logger à utiliser
        e: Exception à journaliser
        message: Message optionnel à inclure
    """
    if message:
        logger.exception(f"{message}: {str(e)}")
    else:
        logger.exception(str(e))


def setup_file_logging(user_id: str = None):
    """
    Configure la journalisation dans un fichier spécifique à l'utilisateur

    Args:
        user_id: ID de l'utilisateur (si applicable)
    """
    # Créer le nom du fichier de log
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id:
        log_file = os.path.join(LOGS_DIR, f"user_{user_id}_{today}.log")
    else:
        log_file = os.path.join(LOGS_DIR, f"app_{today}.log")

    # Configurer un gestionnaire de fichier
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    # Ajouter le gestionnaire au logger racine
    logging.getLogger('').addHandler(file_handler)

    return log_file