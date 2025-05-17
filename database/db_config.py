"""
Configuration de la base de données avec chiffrement au niveau des champs
"""
import os
import base64
import json
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

from utils.constants import DATA_DIR

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(DATA_DIR, 'crypto.log')
)
logger = logging.getLogger('db_crypto')

# Charger les variables d'environnement depuis .env
load_dotenv()

# Créer le répertoire de données s'il n'existe pas
os.makedirs(DATA_DIR, exist_ok=True)

# Récupérer la clé secrète et le sel
SECRET_KEY = os.getenv("SECRET_KEY")
ENCRYPTION_SALT = os.getenv("ENCRYPTION_SALT")

# Si le sel n'est pas défini dans .env, essayer de le lire depuis le fichier .salt
if not ENCRYPTION_SALT:
    salt_file = os.path.join(DATA_DIR, ".salt")
    if os.path.exists(salt_file):
        with open(salt_file, "r") as f:
            ENCRYPTION_SALT = f.read().strip()

# Si toujours pas de sel, utiliser une valeur par défaut (moins sécurisé)
if not ENCRYPTION_SALT:
    logger.warning("Aucun sel personnalisé trouvé, utilisation du sel par défaut")
    ENCRYPTION_SALT = "Patrimoine_App_Salt"  # Valeur par défaut en dernier recours

# Vérifier que la clé secrète est définie
if not SECRET_KEY or SECRET_KEY == "replace_with_a_strong_secret_key":
    logger.error("Clé secrète non définie! Exécutez 'python generate_keys.py' d'abord.")
    raise ValueError("Clé secrète non définie ou valeur par défaut utilisée. Exécutez 'python generate_keys.py'.")

# Chemin vers la base de données
DB_PATH = os.path.join(DATA_DIR, "patrimoine.db")

# URI SQLite standard
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Créer le moteur SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Nécessaire pour SQLite
)

# Fonction pour générer une clé de chiffrement à partir de la clé secrète
def get_encryption_key():
    """Génère une clé de chiffrement dérivée du secret principal et du sel"""
    try:
        # Convertir le sel en bytes
        salt = ENCRYPTION_SALT.encode() if isinstance(ENCRYPTION_SALT, str) else ENCRYPTION_SALT

        # Créer un dérivateur de clé
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        # Dériver la clé à partir de la clé secrète
        derived_key = kdf.derive(SECRET_KEY.encode())
        key = base64.urlsafe_b64encode(derived_key)

        return key
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la clé de chiffrement: {str(e)}")
        raise

# Objet Fernet pour chiffrer/déchiffrer les données sensibles
ENCRYPTION_KEY = get_encryption_key()
cipher = Fernet(ENCRYPTION_KEY)

# Fonctions pour chiffrer/déchiffrer les données sensibles
def encrypt_data(data):
    """Chiffre une donnée textuelle"""
    if data is None:
        return None
    try:
        return cipher.encrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Erreur de chiffrement: {str(e)}")
        return None

def decrypt_data(data):
    """Déchiffre une donnée textuelle"""
    if data is None:
        return None
    try:
        return cipher.decrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Erreur de déchiffrement: {str(e)}")
        return None

# Fonctions pour chiffrer/déchiffrer des dictionnaires JSON
def encrypt_json(data_dict):
    """Chiffre un dictionnaire JSON"""
    if data_dict is None:
        return None
    try:
        json_str = json.dumps(data_dict)
        return encrypt_data(json_str)
    except Exception as e:
        logger.error(f"Erreur de chiffrement JSON: {str(e)}")
        return None

def decrypt_json(encrypted_str):
    """Déchiffre un dictionnaire JSON"""
    if encrypted_str is None:
        return None
    try:
        json_str = decrypt_data(encrypted_str)
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Erreur de déchiffrement JSON: {str(e)}")
        return {}

# Créer une session SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base déclarative pour les modèles
Base = declarative_base()

# Métadonnées pour les tables
metadata = MetaData()

def get_db():
    """
    Fonction utilitaire pour obtenir une session de base de données
    Yields:
        Session SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()