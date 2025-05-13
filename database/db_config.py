"""
Configuration de la base de données avec chiffrement au niveau des champs
"""
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet

from utils.constants import DATA_DIR, SECRET_KEY

# Créer le répertoire de données s'il n'existe pas
os.makedirs(DATA_DIR, exist_ok=True)

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
    import base64
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    salt = b'Patrimoine_App_Salt'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
    return key

# Objet Fernet pour chiffrer/déchiffrer les données sensibles
ENCRYPTION_KEY = get_encryption_key()
cipher = Fernet(ENCRYPTION_KEY)

# Fonctions pour chiffrer/déchiffrer les données sensibles
def encrypt_data(data):
    """Chiffre une donnée textuelle"""
    if data is None:
        return None
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(data):
    """Déchiffre une donnée textuelle"""
    if data is None:
        return None
    return cipher.decrypt(data.encode()).decode()

# Fonctions pour chiffrer/déchiffrer des dictionnaires JSON
import json

def encrypt_json(data_dict):
    """Chiffre un dictionnaire JSON"""
    if data_dict is None:
        return None
    json_str = json.dumps(data_dict)
    return encrypt_data(json_str)

def decrypt_json(encrypted_str):
    """Déchiffre un dictionnaire JSON"""
    if encrypted_str is None:
        return None
    json_str = decrypt_data(encrypted_str)
    return json.loads(json_str)

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