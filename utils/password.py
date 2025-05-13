"""
Utilitaires pour le hachage et la vérification des mots de passe
"""
from passlib.context import CryptContext

# Contexte de hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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