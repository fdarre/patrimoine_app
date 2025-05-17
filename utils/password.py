"""
Utilitaires pour le hachage et la vérification des mots de passe
"""
from passlib.context import CryptContext
import logging
import os
from utils.constants import DATA_DIR

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(DATA_DIR, 'auth.log')
)
logger = logging.getLogger('password')

# Contexte de hachage des mots de passe - augmenté à 12 rounds
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def hash_password(password: str) -> str:
    """
    Hache un mot de passe avec bcrypt

    Args:
        password: Mot de passe en clair

    Returns:
        Hash du mot de passe
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie si un mot de passe correspond à un hash

    Args:
        plain_password: Mot de passe en clair
        hashed_password: Hash du mot de passe

    Returns:
        True si le mot de passe correspond au hash, False sinon
    """
    return pwd_context.verify(plain_password, hashed_password)