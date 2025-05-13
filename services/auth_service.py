"""
Service d'authentification et de gestion des utilisateurs
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import jwt
from sqlalchemy.orm import Session

from database.models import User
from utils.constants import SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from utils.password import hash_password, verify_password

class AuthService:
    """Service pour l'authentification et la gestion des utilisateurs"""

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        Récupère un utilisateur par son nom d'utilisateur

        Args:
            db: Session de base de données
            username: Nom d'utilisateur

        Returns:
            L'utilisateur ou None
        """
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """
        Récupère un utilisateur par son ID

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur

        Returns:
            L'utilisateur ou None
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str) -> Optional[User]:
        """
        Crée un nouvel utilisateur

        Args:
            db: Session de base de données
            username: Nom d'utilisateur
            email: Email
            password: Mot de passe en clair

        Returns:
            L'utilisateur créé ou None si le nom d'utilisateur existe déjà
        """
        # Vérifier si le nom d'utilisateur existe déjà
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return None

        # Vérifier si l'email existe déjà
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            return None

        # Hacher le mot de passe
        password_hash = hash_password(password)

        # Créer le nouvel utilisateur
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_active=True,
            created_at=datetime.now()
        )

        # Ajouter et valider
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authentifie un utilisateur

        Args:
            db: Session de base de données
            username: Nom d'utilisateur
            password: Mot de passe en clair

        Returns:
            L'utilisateur authentifié ou None
        """
        # Trouver l'utilisateur
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None

        # Vérifier le mot de passe
        if not verify_password(password, user.password_hash):
            return None

        # Vérifier que l'utilisateur est actif
        if not user.is_active:
            return None

        return user

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Crée un token JWT

        Args:
            data: Données à inclure dans le token
            expires_delta: Durée de validité du token

        Returns:
            Token JWT
        """
        to_encode = data.copy()

        # Définir l'expiration du token
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})

        # Encoder le token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)

        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Vérifie un token JWT

        Args:
            token: Token JWT à vérifier

        Returns:
            Données du token ou None si invalide
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

    @staticmethod
    def get_user_count(db: Session) -> int:
        """
        Compte le nombre d'utilisateurs

        Args:
            db: Session de base de données

        Returns:
            Nombre d'utilisateurs
        """
        return db.query(User).count()

    @staticmethod
    def update_user(db: Session, user_id: str, is_active: bool = None, email: str = None) -> Optional[User]:
        """
        Met à jour un utilisateur

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            is_active: Statut d'activité (optionnel)
            email: Nouvel email (optionnel)

        Returns:
            L'utilisateur mis à jour ou None
        """
        # Récupérer l'utilisateur
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Mettre à jour les champs
        if is_active is not None:
            user.is_active = is_active

        if email:
            user.email = email

        # Valider les modifications
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def change_password(db: Session, user_id: str, new_password: str) -> Optional[User]:
        """
        Change le mot de passe d'un utilisateur

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            new_password: Nouveau mot de passe en clair

        Returns:
            L'utilisateur mis à jour ou None
        """
        # Récupérer l'utilisateur
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Hacher le nouveau mot de passe
        password_hash = hash_password(new_password)

        # Mettre à jour le hash du mot de passe
        user.password_hash = password_hash

        # Valider les modifications
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        """
        Supprime un utilisateur

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur à supprimer

        Returns:
            True si la suppression a réussi, False sinon
        """
        # Récupérer l'utilisateur
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Supprimer l'utilisateur
        db.delete(user)
        db.commit()

        return True