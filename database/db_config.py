"""
Database configuration with field-level encryption
"""
import base64
import json
import os
import sqlite3
import sys
from contextlib import contextmanager
from typing import Generator, Dict, Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config.app_config import SQLALCHEMY_DATABASE_URL, SECRET_KEY, ENCRYPTION_SALT, DB_PATH
from utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)


# Define a custom exception for data corruption
class DataCorruptionError(Exception):
    """Exception raised when encrypted data is corrupted or can't be decrypted properly"""
    pass

# Create SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
)


# Activer les contraintes de clé étrangère dans SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Function to generate encryption key from secret key
def get_encryption_key():
    """Generate an encryption key derived from the main secret and salt"""
    try:
        # Les deux valeurs devraient déjà être des bytes
        salt = ENCRYPTION_SALT
        key = SECRET_KEY

        # Create key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        # Derive and encode key
        derived_key = kdf.derive(key)
        result_key = base64.urlsafe_b64encode(derived_key)

        return result_key
    except Exception as e:
        logger.error(f"Error generating encryption key: {str(e)}")
        raise


# Initialiser le chiffrement
try:
    # Initialisation normale
    ENCRYPTION_KEY = get_encryption_key()
    cipher = Fernet(ENCRYPTION_KEY)
    logger.info("Encryption successfully initialized")
except Exception as e:
    error_msg = f"ERREUR FATALE: Impossible d'initialiser le chiffrement: {str(e)}"
    logger.critical(error_msg)
    print(error_msg)
    sys.exit(1)


# Functions for encrypting/decrypting sensitive data
def encrypt_data(data):
    """Encrypt textual data"""
    if data is None:
        return None
    try:
        if not isinstance(data, str):
            data = str(data)
        return cipher.encrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption error: {str(e)}")
        return None


def decrypt_data(data):
    """Decrypt textual data"""
    if data is None:
        return None
    try:
        return cipher.decrypt(data.encode()).decode()
    except InvalidToken:
        logger.error(f"Invalid token during decryption - data might be corrupted")
        return "[Decryption Error]"
    except Exception as e:
        logger.error(f"Decryption error: {str(e)}")
        return "[Decryption Error]"


# Functions for encrypting/decrypting JSON dictionaries
def encrypt_json(data_dict):
    """Encrypt a JSON dictionary"""
    if data_dict is None:
        return None
    try:
        json_str = json.dumps(data_dict)
        return encrypt_data(json_str)
    except Exception as e:
        logger.error(f"JSON encryption error: {str(e)}")
        return None


def decrypt_json(encrypted_str, silent_errors=False) -> Dict[str, Any]:
    """
    Decrypt a JSON dictionary with error handling

    Args:
        encrypted_str: Encrypted JSON string
        silent_errors: If True, return empty dict instead of raising exception (for backward compatibility)

    Returns:
        Decrypted dictionary

    Raises:
        DataCorruptionError: If decryption fails and silent_errors is False
    """
    if encrypted_str is None:
        return {}

    try:
        # Attempt to decrypt
        json_str = decrypt_data(encrypted_str)

        # Handle decryption failure
        if json_str == "[Decryption Error]":
            error_msg = "JSON decryption failed - possible data corruption or key mismatch"
            logger.error(error_msg)
            if not silent_errors:
                raise DataCorruptionError(error_msg)
            return {}

        # Try to parse JSON
        if json_str:
            try:
                result = json.loads(json_str)
                # Ensure we got a dictionary
                if isinstance(result, dict):
                    return result
                else:
                    error_msg = f"Decrypted JSON is not a dictionary, got {type(result)}"
                    logger.error(error_msg)
                    if not silent_errors:
                        raise DataCorruptionError(error_msg)
                    return {}
            except json.JSONDecodeError as e:
                error_msg = f"JSON decode error: {str(e)}"
                logger.error(error_msg)
                if not silent_errors:
                    raise DataCorruptionError(error_msg)
                return {}
        return {}
    except DataCorruptionError:
        # Re-raise DataCorruptionError exceptions
        raise
    except Exception as e:
        error_msg = f"JSON decryption error: {str(e)}"
        logger.error(error_msg)
        if not silent_errors:
            raise DataCorruptionError(error_msg)
        return {}


# Fonction pour vérifier que les clés peuvent déchiffrer des données existantes
def verify_keys_with_existing_data(db_path: str) -> bool:
    """
    Vérifie que les clés actuelles peuvent déchiffrer des données existantes

    Args:
        db_path: Chemin vers la base de données

    Returns:
        True si les clés permettent de déchiffrer des données, False sinon
    """
    if not os.path.exists(db_path):
        logger.warning(f"Base de données {db_path} inexistante, impossible de vérifier les clés")
        return True  # Pas de données à vérifier

    try:
        # Connexion à la BDD SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Chercher une donnée chiffrée, essayer plusieurs tables
        encrypted_data = None
        tables_to_check = ['users', 'banks', 'assets']

        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                row = cursor.fetchone()
                if row:
                    # Trouver une colonne qui pourrait contenir des données chiffrées
                    for i, value in enumerate(row):
                        if isinstance(value, str) and len(value) > 64:  # Probablement chiffré
                            encrypted_data = value
                            break

                    if encrypted_data:
                        break
            except sqlite3.Error:
                continue  # Table n'existe peut-être pas

        conn.close()

        # Si aucune donnée chiffrée trouvée, on ne peut pas vérifier
        if not encrypted_data:
            logger.info("Aucune donnée chiffrée trouvée dans la base de données pour vérification")
            return True

        # Essayer de déchiffrer
        try:
            decrypt_data(encrypted_data)
            logger.info("Vérification des clés réussie: déchiffrement des données existantes OK")

            # Mettre à jour le timestamp de dernière vérification
            from utils.key_manager import KeyManager
            from config.app_config import DATA_DIR, KEY_BACKUPS_DIR
            key_manager = KeyManager(DATA_DIR, KEY_BACKUPS_DIR)
            key_manager.update_verification_timestamp()

            return True
        except Exception as e:
            logger.critical(f"ERREUR: Les clés actuelles ne peuvent pas déchiffrer les données existantes: {str(e)}")
            return False

    except Exception as e:
        logger.error(f"Erreur lors de la vérification des clés: {str(e)}")
        return False


# Vérifier la compatibilité avec les données existantes si la base existe
if os.path.exists(DB_PATH):
    if not verify_keys_with_existing_data(str(DB_PATH)):
        error_msg = "ERREUR CRITIQUE: Les clés ne peuvent pas déchiffrer les données existantes!"
        logger.critical(error_msg)
        print(error_msg)
        print("Restaurez les fichiers de clés corrects ou utilisez une sauvegarde de la base de données.")
        sys.exit(1)


# Create a SQLAlchemy session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()

# Metadata for tables
metadata = MetaData()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions to ensure proper resource management

    Usage:
        with get_db_session() as session:
            # Use session here

    Yields:
        SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        db.close()


def get_db():
    """
    Utility function to get a database session for dependency injection

    Yields:
        SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()