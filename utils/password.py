"""
Utilitaires de gestion des mots de passe sécurisés avec bcrypt
"""
import secrets
from typing import Tuple

import bcrypt

from utils.logger import get_logger

logger = get_logger(__name__)


def hash_password(password: str) -> str:
    """
    Hash un mot de passe en utilisant bcrypt

    Args:
        password: Mot de passe en clair

    Returns:
        Hash du mot de passe
    """
    try:
        # Encoder le mot de passe en UTF-8 puis le hacher
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Retourner le hash sous forme de chaîne
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Erreur lors du hachage du mot de passe: {str(e)}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie qu'un mot de passe en clair correspond à un hash

    Args:
        plain_password: Mot de passe en clair
        hashed_password: Hash du mot de passe

    Returns:
        True si le mot de passe correspond au hash, False sinon
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du mot de passe: {str(e)}")
        return False


def generate_reset_token() -> Tuple[str, str]:
    """
    Génère un token de réinitialisation et son hash

    Returns:
        Tuple (token, hash_token)
    """
    # Générer un token aléatoire de 32 octets (256 bits) encodé en base64
    token = secrets.token_urlsafe(32)
    # Hacher le token
    hash_token = hash_password(token)

    return token, hash_token
