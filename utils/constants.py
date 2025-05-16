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