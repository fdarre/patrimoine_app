"""
Database configuration with field-level encryption
"""
import base64
import json
from contextlib import contextmanager
from typing import Generator

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config.app_config import SQLALCHEMY_DATABASE_URL, SECRET_KEY, ENCRYPTION_SALT
from utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
)


# Function to generate encryption key from secret key
def get_encryption_key():
    """Generate an encryption key derived from the main secret and salt"""
    try:
        # Convert salt to bytes
        salt = ENCRYPTION_SALT.encode() if isinstance(ENCRYPTION_SALT, str) else ENCRYPTION_SALT

        # Create key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        # Derive key from secret key
        derived_key = kdf.derive(SECRET_KEY.encode())
        key = base64.urlsafe_b64encode(derived_key)

        return key
    except Exception as e:
        logger.error(f"Error generating encryption key: {str(e)}")
        raise


# Fernet object for encrypting/decrypting sensitive data
ENCRYPTION_KEY = get_encryption_key()
cipher = Fernet(ENCRYPTION_KEY)


# Functions for encrypting/decrypting sensitive data
def encrypt_data(data):
    """Encrypt textual data"""
    if data is None:
        return None
    try:
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
    except Exception as e:
        logger.error(f"Decryption error: {str(e)}")
        return None


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

def decrypt_json(encrypted_str):
    """Decrypt a JSON dictionary"""
    if encrypted_str is None:
        return None
    try:
        json_str = decrypt_data(encrypted_str)
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"JSON decryption error: {str(e)}")
        return {}


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