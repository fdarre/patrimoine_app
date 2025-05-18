"""
Service d'authentification et de gestion des utilisateurs avec protections améliorées
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import jwt
from sqlalchemy.orm import Session

from database.models import User
from config.app_config import SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, MAX_USERS
from utils.password import hash_password, verify_password
from utils.logger import get_logger
from utils.exceptions import AuthenticationError, ValidationError
from utils.decorators import handle_exceptions

# Configurer le logger
logger = get_logger(__name__)

# Dictionnaire pour stocker les tentatives d'authentification échouées
# Clé = nom d'utilisateur, Valeur = (nombre de tentatives, heure de dernière tentative)
failed_attempts = {}

class AuthService:
    """Service pour l'authentification et la gestion des utilisateurs avec sécurité renforcée"""

    @staticmethod
    @handle_exceptions
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
    @handle_exceptions
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
    @handle_exceptions
    def create_user(db: Session, username: str, email: str, password: str) -> Optional[User]:
        """
        Crée un nouvel utilisateur avec vérification de la force du mot de passe

        Args:
            db: Session de base de données
            username: Nom d'utilisateur
            email: Email
            password: Mot de passe en clair

        Returns:
            L'utilisateur créé ou None si le nom d'utilisateur existe déjà

        Raises:
            ValidationError: Si le mot de passe est trop court
        """
        # Vérifier la force du mot de passe (minimal)
        if len(password) < 8:
            logger.warning(f"Tentative de création d'utilisateur avec un mot de passe trop court: {username}")
            raise ValidationError("Le mot de passe doit contenir au moins 8 caractères")

        # Vérifier si le nom d'utilisateur existe déjà
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            logger.warning(f"Tentative de création d'un utilisateur avec un nom existant: {username}")
            return None

        # Vérifier si l'email existe déjà
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            logger.warning(f"Tentative de création d'un utilisateur avec un email existant: {email}")
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
        logger.info(f"Nouvel utilisateur créé: {username}")

        return new_user

    @staticmethod
    @handle_exceptions
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authentifie un utilisateur avec protection contre les attaques par force brute

        Args:
            db: Session de base de données
            username: Nom d'utilisateur
            password: Mot de passe en clair

        Returns:
            L'utilisateur authentifié ou None

        Raises:
            AuthenticationError: Si le compte est temporairement verrouillé
        """
        # Vérifier les tentatives précédentes
        if username in failed_attempts:
            attempts, last_attempt = failed_attempts[username]
            if attempts >= 5 and datetime.now() - last_attempt < timedelta(minutes=15):
                logger.warning(f"Compte temporairement verrouillé après plusieurs échecs: {username}")
                raise AuthenticationError("Compte temporairement verrouillé suite à plusieurs échecs d'authentification. Veuillez réessayer dans 15 minutes.")

        # Trouver l'utilisateur
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.warning(f"Tentative d'authentification avec un nom d'utilisateur inconnu: {username}")
            # Incrémenter le compteur même pour les utilisateurs inexistants
            if username not in failed_attempts:
                failed_attempts[username] = (1, datetime.now())
            else:
                attempts, _ = failed_attempts[username]
                failed_attempts[username] = (attempts + 1, datetime.now())
            return None

        # Vérifier le mot de passe
        if not verify_password(password, user.password_hash):
            logger.warning(f"Échec d'authentification pour l'utilisateur: {username}")
            # Incrémenter le compteur d'échecs
            if username not in failed_attempts:
                failed_attempts[username] = (1, datetime.now())
            else:
                attempts, _ = failed_attempts[username]
                failed_attempts[username] = (attempts + 1, datetime.now())
            return None

        # Vérifier que l'utilisateur est actif
        if not user.is_active:
            logger.warning(f"Tentative d'authentification avec un compte inactif: {username}")
            return None

        # Réinitialiser le compteur d'échecs en cas de succès
        if username in failed_attempts:
            del failed_attempts[username]

        logger.info(f"Authentification réussie pour l'utilisateur: {username}")
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

        # Définir l'expiration du token (4 heures par défaut au lieu de 24)
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
        except jwt.PyJWTError as e:
            logger.warning(f"Vérification de token échouée: {str(e)}")
            return None

    @staticmethod
    @handle_exceptions
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
    @handle_exceptions
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
        logger.info(f"Utilisateur mis à jour: {user.username}")

        return user

    @staticmethod
    @handle_exceptions
    def change_password(db: Session, user_id: str, new_password: str) -> Optional[User]:
        """
        Change le mot de passe d'un utilisateur avec vérification de la force du mot de passe

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            new_password: Nouveau mot de passe en clair

        Returns:
            L'utilisateur mis à jour ou None

        Raises:
            ValidationError: Si le mot de passe est trop court
        """
        # Vérifier la force du mot de passe
        if len(new_password) < 8:
            logger.warning(f"Tentative de changement de mot de passe trop court pour l'utilisateur: {user_id}")
            raise ValidationError("Le mot de passe doit contenir au moins 8 caractères")

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
        logger.info(f"Mot de passe changé pour l'utilisateur: {user.username}")

        return user

    @staticmethod
    @handle_exceptions
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
        logger.info(f"Utilisateur supprimé: {user.username}")

        return True

    @staticmethod
    def reset_failed_attempts(username: str) -> None:
        """
        Réinitialise le compteur de tentatives échouées pour un utilisateur

        Args:
            username: Nom d'utilisateur
        """
        if username in failed_attempts:
            del failed_attempts[username]
            logger.info(f"Compteur de tentatives échouées réinitialisé pour: {username}")