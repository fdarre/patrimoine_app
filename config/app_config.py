"""
Centralized application configuration
"""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

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

# Database configuration
DB_PATH = DATA_DIR / "patrimoine.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Fichiers pour stocker les clés de sécurité
salt_file = DATA_DIR / ".salt"
key_file = DATA_DIR / ".key"

# Charger ou générer SECRET_KEY
if key_file.exists():
    with open(key_file, "rb") as f:
        SECRET_KEY = f.read()
else:
    # Générer une nouvelle clé
    SECRET_KEY = secrets.token_bytes(32)
    with open(key_file, "wb") as f:
        f.write(SECRET_KEY)
    # Protéger le fichier (Unix seulement)
    try:
        os.chmod(key_file, 0o600)  # Lecture/écriture uniquement pour le propriétaire
    except Exception:
        pass

# Charger ou générer ENCRYPTION_SALT
if salt_file.exists():
    with open(salt_file, "rb") as f:
        ENCRYPTION_SALT = f.read()
else:
    # Générer un nouveau sel
    ENCRYPTION_SALT = secrets.token_bytes(16)
    with open(salt_file, "wb") as f:
        f.write(ENCRYPTION_SALT)
    # Protéger le fichier (Unix seulement)
    try:
        os.chmod(salt_file, 0o600)
    except Exception:
        pass

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

# Logging configuration
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