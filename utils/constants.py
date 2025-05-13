"""
Constantes utilisées dans l'application de gestion patrimoniale
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Types de comptes (enveloppes fiscales)
ACCOUNT_TYPES = ["courant", "livret", "pea", "titre", "assurance_vie", "autre"]

# Types de produits (forme juridique)
PRODUCT_TYPES = ["etf", "sicav", "action", "obligation", "scpi", "reits",
                 "fonds_euro", "crypto", "metal", "cash", "immo_direct", "autre"]

# Catégories patrimoniales
ASSET_CATEGORIES = ["actions", "obligations", "immobilier", "crypto", "metaux", "cash", "autre"]

# Zones géographiques
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

# Description des zones géographiques
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

# Devises
CURRENCIES = ["EUR", "USD", "GBP", "JPY", "CHF"]

# Chemins des fichiers
DATA_DIR = "data"

# Clé secrète pour JWT et chiffrement
SECRET_KEY = os.getenv("SECRET_KEY", "replace_with_a_strong_secret_key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 heures

# Nombre maximum d'utilisateurs
MAX_USERS = int(os.getenv("MAX_USERS", "5"))

# Styles CSS
CUSTOM_CSS = """
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        margin-bottom: 1rem;
    }

    .todo-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0.25rem;
    }

    .component-card {
        background-color: #e2f0fb;
        border-left: 4px solid #0d6efd;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0.25rem;
    }

    .positive {
        color: #28a745;
    }

    .negative {
        color: #dc3545;
    }

    h1, h2, h3 {
        color: #343a40;
    }

    .stButton>button {
        width: 100%;
    }

    .allocation-box {
        background-color: #e9ecef;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .allocation-title {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }

    .composite-header {
        background-color: #d1e7dd;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin-bottom: 0.5rem;
    }
</style>
"""