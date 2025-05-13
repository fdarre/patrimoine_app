"""
Modèle pour les utilisateurs
"""
import uuid
from datetime import datetime
from passlib.context import CryptContext
from typing import Dict, Any, Optional

# Pour le hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User:
    """Classe représentant un utilisateur"""

    def __init__(
            self,
            username: str,
            email: str,
            password_hash: str,
            id: Optional[str] = None,
            is_active: bool = True,
            created_at: Optional[str] = None
    ):
        """
        Initialise un nouvel utilisateur

        Args:
            username: Nom d'utilisateur (unique)
            email: Adresse email
            password_hash: Hash du mot de passe
            id: Identifiant unique (UUID)
            is_active: Statut de l'utilisateur
            created_at: Date de création
        """
        self.id = id if id else str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_active = is_active
        self.created_at = created_at if created_at else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        Crée un utilisateur à partir d'un dictionnaire

        Args:
            data: Dictionnaire contenant les données utilisateur

        Returns:
            Une instance de User
        """
        return cls(
            id=data.get("id"),
            username=data.get("username"),
            email=data.get("email"),
            password_hash=data.get("password_hash"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at")
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'utilisateur en dictionnaire (sans le mot de passe)

        Returns:
            Un dictionnaire représentant l'utilisateur
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "is_active": self.is_active,
            "created_at": self.created_at
        }

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hache un mot de passe

        Args:
            password: Mot de passe en clair

        Returns:
            Hash du mot de passe
        """
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Vérifie un mot de passe

        Args:
            password: Mot de passe à vérifier

        Returns:
            True si le mot de passe est correct, False sinon
        """
        return pwd_context.verify(password, self.password_hash)