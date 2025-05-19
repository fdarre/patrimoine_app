"""
Centralized application configuration
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

# Import logger functions only, not the full module
from utils.logger import get_logger, configure_logging

# Load environment variables
load_dotenv()

# Directory paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
STATIC_DIR = BASE_DIR / "static"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Dossier dédié pour les backups de clés
KEY_BACKUPS_DIR = DATA_DIR / "key_backups"
KEY_BACKUPS_DIR.mkdir(exist_ok=True)

# Définir la configuration de logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "app.log"),
            "formatter": "standard"
        },
        "detailed_file": {
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "detailed.log"),
            "formatter": "detailed"
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard"
        }
    },
    "loggers": {
        "": {
            "handlers": ["file", "console"],
            "level": "INFO",
        }
    }
}

# Configurer le logging avec notre configuration
configure_logging(LOGGING_CONFIG, LOGS_DIR)

# Configure logger for this module
logger = get_logger(__name__)

# Database configuration
DB_PATH = DATA_DIR / "patrimoine.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Fichiers pour stocker les clés de sécurité
salt_file = DATA_DIR / ".salt"
key_file = DATA_DIR / ".key"

# Initialiser le gestionnaire de clés
from utils.key_manager import KeyManager

key_manager = KeyManager(DATA_DIR, KEY_BACKUPS_DIR)

# Charger les clés existantes ou arrêter l'exécution
if key_manager.check_keys_exist():
    with open(key_file, "rb") as f:
        SECRET_KEY = f.read()
    with open(salt_file, "rb") as f:
        ENCRYPTION_SALT = f.read()
    logger.info("Clés de chiffrement chargées avec succès")
else:
    # Afficher un message d'erreur critique et arrêter l'exécution
    error_msg = (
        "ERREUR CRITIQUE: Fichiers de clés manquants. "
        "Exécutez 'python init_keys.py' pour générer de nouvelles clés "
        "ou restaurez les fichiers .key et .salt à partir d'une sauvegarde."
    )
    logger.critical(error_msg)
    print(error_msg)
    sys.exit(1)  # Arrêt de l'exécution avec code d'erreur 1

# JWT configuration
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Reduced from 1440 (24h) to 60 minutes (1h)

# Application limits
MAX_USERS = 5

# Types and categories (business constants)
ACCOUNT_TYPES = ["courant", "livret", "pea", "titre", "assurance_vie", "autre"]

PRODUCT_TYPES = ["etf", "sicav", "action", "obligation", "scpi", "reits",
                 "fonds_euro", "crypto", "metal", "cash", "immo_direct", "autre"]

ASSET_CATEGORIES = ["actions", "obligations", "immobilier", "crypto", "metaux", "cash", "autre"]

GEO_ZONES = [
    "amerique_nord",
    "europe_zone_euro",
    "europe_hors_zone_euro",
    "japon",
    "chine",
    "inde",
    "asie_developpee",
    "autres_emergents",
    "global_non_classe"
]

GEO_ZONES_DESCRIPTIONS = {
    "amerique_nord": "United States, Canada",
    "europe_zone_euro": "Germany, France, Spain, Italy, Netherlands, etc.",
    "europe_hors_zone_euro": "United Kingdom, Switzerland, Sweden, Norway, Denmark",
    "japon": "Japan",
    "chine": "China, Hong Kong",
    "inde": "India",
    "asie_developpee": "South Korea, Australia, Singapore, New Zealand",
    "autres_emergents": "Brazil, Mexico, Indonesia, South Africa, Egypt, Turkey, Poland, Vietnam, Nigeria, Argentina, Chile, Peru, Colombia, etc.",
    "global_non_classe": "For exceptional non-ventilated cases"
}

CURRENCIES = ["EUR", "USD", "GBP", "JPY", "CHF"]

# Custom CSS for the application
CUSTOM_CSS = """
<style>
    /* Color variables for dark theme */
    :root {
        --text-color: #fff;
        --dark-text-color: #333;
        --background-color: #1e1e1e;
        --primary-color: #4e79a7;
        --secondary-color: #f28e2c;
        --success-color: #40c057;
        --danger-color: #fa5252;
        --light-bg: #343a40;
        --border-color: #495057;
    }

    .metric-card {
        background-color: var(--light-bg);
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
        color: var(--text-color);
    }

    .todo-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0.25rem;
        color: var(--dark-text-color) !important;
    }

    /* Rest of CSS remains the same */
    /* ... */
</style>
"""