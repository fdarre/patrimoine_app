"""
Configuration centralisée de l'application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Chemins des dossiers
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# S'assurer que les dossiers existent
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Configuration de la base de données
DB_PATH = os.path.join(DATA_DIR, "patrimoine.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Clés de sécurité et cryptographie
SECRET_KEY = os.getenv("SECRET_KEY", "default_key_replace_in_production")
ENCRYPTION_SALT = os.getenv("ENCRYPTION_SALT", "default_salt_replace_in_production")

# Si le sel n'est pas défini dans l'environnement, essayer de le lire depuis le fichier .salt
if ENCRYPTION_SALT == "default_salt_replace_in_production":
    salt_file = os.path.join(DATA_DIR, ".salt")
    if os.path.exists(salt_file):
        with open(salt_file, "r") as f:
            ENCRYPTION_SALT = f.read().strip()

# Configuration JWT
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 heures

# Limites de l'application
MAX_USERS = int(os.getenv("MAX_USERS", "5"))

# Types et catégories (constantes métier)
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
    "amerique_nord": "États-Unis, Canada",
    "europe_zone_euro": "Allemagne, France, Espagne, Italie, Pays-Bas, etc.",
    "europe_hors_zone_euro": "Royaume-Uni, Suisse, Suède, Norvège, Danemark",
    "japon": "Japon",
    "chine": "Chine, Hong Kong",
    "inde": "Inde",
    "asie_developpee": "Corée du Sud, Australie, Singapour, Nouvelle-Zélande",
    "autres_emergents": "Brésil, Mexique, Indonésie, Afrique du Sud, Égypte, Turquie, Pologne, Vietnam, Nigeria, Argentine, Chili, Pérou, Colombie, etc.",
    "global_non_classe": "Pour cas exceptionnels non ventilés"
}

CURRENCIES = ["EUR", "USD", "GBP", "JPY", "CHF"]

# Configuration du logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGS_DIR, "app.log"),
            "formatter": "standard"
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

# CSS personnalisé pour l'application
CUSTOM_CSS = """
<style>
    /* Variables de couleur pour thème sombre */
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

    .component-card {
        background-color: #31383e;
        border-left: 4px solid #4e79a7;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0.25rem;
        color: var(--text-color);
    }

    .positive {
        color: var(--success-color);
    }

    .negative {
        color: var(--danger-color);
    }

    h1, h2, h3 {
        color: var(--text-color);
    }

    .stButton>button {
        width: 100%;
    }

    .allocation-box {
        background-color: var(--light-bg);
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        color: var(--text-color);
    }

    .allocation-title {
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: var(--text-color);
    }

    .composite-header {
        background-color: #2c5840;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin-bottom: 0.5rem;
        color: var(--text-color);
    }

    /* Améliorations pour thème sombre */
    .dataframe td, .dataframe th {
        color: var(--text-color);
    }

    /* Pour les badges et indicateurs */
    span {
        color: inherit;
    }

    /* Pour les éléments de type comptes dans le détail */
    .account-detail {
        color: var(--text-color) !important;
        background-color: var(--light-bg);
    }

    /* Pour les tableaux sur fond sombre */
    table {
        color: var(--text-color);
    }

    /* Pour les sélecteurs et entrées */
    .stSelectbox, .stTextInput, .stTextArea {
        color: var(--text-color);
    }

    /* Renforcer la visibilité des textes */
    p, div, li, span {
        color: var(--text-color);
    }

    /* Exception pour les cartes todo */
    .todo-card p, .todo-card div, .todo-card span {
        color: var(--dark-text-color);
    }
</style>
"""