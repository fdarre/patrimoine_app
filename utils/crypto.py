"""
Utilitaires pour le chiffrement et déchiffrement
"""
from sqlalchemy import TypeDecorator, String
from sqlalchemy.ext.mutable import MutableDict, MutableList

from database.db_config import encrypt_data, decrypt_data, encrypt_json, decrypt_json, DataCorruptionError
from utils.logger import get_logger

logger = get_logger(__name__)

class EncryptedString(TypeDecorator):
    """
    Type SQLAlchemy pour stocker des chaînes chiffrées
    """
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return encrypt_data(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return decrypt_data(value)
        return value

class EncryptedJSON(TypeDecorator):
    """
    Type SQLAlchemy pour stocker des JSON chiffrés
    """
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return encrypt_json(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return decrypt_json(value, silent_errors=True)
            except DataCorruptionError as e:
                logger.critical(f"CORRUPTION DÉTECTÉE: {str(e)}")
                # En production, on retourne un dict vide mais on a loggé l'erreur
                return {}
        return value

# Types de données mutables chiffrés
class EncryptedDict(MutableDict):
    """Dictionnaire chiffré"""
    @classmethod
    def coerce(cls, key, value):
        if isinstance(value, dict) and not isinstance(value, EncryptedDict):
            return EncryptedDict(value)
        return value

class EncryptedList(MutableList):
    """Liste chiffrée"""
    @classmethod
    def coerce(cls, key, value):
        if isinstance(value, list) and not isinstance(value, EncryptedList):
            return EncryptedList(value)
        return value