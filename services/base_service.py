"""
Service de base générique pour les opérations CRUD avec une approche cohérente
"""
from typing import List, Optional, TypeVar, Generic, Type, Dict, Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database.models import Base
from utils.error_manager import catch_exceptions  # Changé de handle_exceptions
from utils.exceptions import DatabaseError, ValidationError
from utils.logger import get_logger

# Type générique pour les modèles SQLAlchemy
T = TypeVar('T', bound=Base)
logger = get_logger(__name__)


class BaseService(Generic[T]):
    """
    Service de base générique pour les opérations CRUD
    """

    def __init__(self, model_class: Type[T]):
        """
        Initialise le service avec la classe de modèle

        Args:
            model_class: Classe de modèle SQLAlchemy
        """
        self.model_class = model_class

    @catch_exceptions  # Changé de handle_exceptions
    def get_all(self, db: Session, owner_id: Optional[str] = None, **filters) -> List[T]:
        """
        Récupère tous les objets qui correspondent aux filtres

        Args:
            db: Session de base de données
            owner_id: ID de l'utilisateur propriétaire (si applicable)
            **filters: Filtres supplémentaires

        Returns:
            Liste d'objets correspondant aux filtres
        """
        query = db.query(self.model_class)

        if owner_id is not None and hasattr(self.model_class, 'owner_id'):
            query = query.filter(self.model_class.owner_id == owner_id)

        for attr, value in filters.items():
            if hasattr(self.model_class, attr):
                query = query.filter(getattr(self.model_class, attr) == value)

        return query.all()

    @catch_exceptions  # Changé de handle_exceptions
    def get_by_id(self, db: Session, item_id: str) -> Optional[T]:
        """
        Récupère un objet par son ID

        Args:
            db: Session de base de données
            item_id: ID de l'objet

        Returns:
            Objet trouvé ou None
        """
        return db.query(self.model_class).filter(self.model_class.id == item_id).first()

    @catch_exceptions  # Changé de handle_exceptions
    def create(self, db: Session, data: Dict[str, Any]) -> T:
        """
        Crée un nouvel objet

        Args:
            db: Session de base de données
            data: Données pour la création

        Returns:
            Nouvel objet créé

        Raises:
            ValidationError: Si les données sont invalides
            DatabaseError: En cas d'erreur lors de la création
        """
        # Validation des données requises si le modèle a un attribut required_fields
        if hasattr(self.model_class, 'required_fields'):
            missing_fields = [field for field in self.model_class.required_fields
                             if field not in data or data[field] is None]
            if missing_fields:
                raise ValidationError(f"Champs obligatoires manquants: {', '.join(missing_fields)}")

        try:
            item = self.model_class(**data)
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erreur lors de la création de {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Erreur lors de la création: {str(e)}")

    @catch_exceptions  # Changé de handle_exceptions
    def update(self, db: Session, item_id: str, data: Dict[str, Any]) -> Optional[T]:
        """
        Met à jour un objet existant

        Args:
            db: Session de base de données
            item_id: ID de l'objet
            data: Données pour la mise à jour

        Returns:
            Objet mis à jour ou None

        Raises:
            DatabaseError: En cas d'erreur lors de la mise à jour
        """
        try:
            item = self.get_by_id(db, item_id)
            if not item:
                return None

            for key, value in data.items():
                if hasattr(item, key):
                    setattr(item, key, value)

            db.commit()
            db.refresh(item)
            return item
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erreur lors de la mise à jour de {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Erreur lors de la mise à jour: {str(e)}")

    @catch_exceptions  # Changé de handle_exceptions
    def delete(self, db: Session, item_id: str) -> bool:
        """
        Supprime un objet

        Args:
            db: Session de base de données
            item_id: ID de l'objet

        Returns:
            True si la suppression a réussi, False sinon

        Raises:
            DatabaseError: En cas d'erreur lors de la suppression
        """
        try:
            item = self.get_by_id(db, item_id)
            if not item:
                return False

            db.delete(item)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erreur lors de la suppression de {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Erreur lors de la suppression: {str(e)}")

    @catch_exceptions  # Changé de handle_exceptions
    def count(self, db: Session, owner_id: Optional[str] = None, **filters) -> int:
        """
        Compte le nombre d'objets qui correspondent aux filtres

        Args:
            db: Session de base de données
            owner_id: ID de l'utilisateur propriétaire (si applicable)
            **filters: Filtres supplémentaires

        Returns:
            Nombre d'objets
        """
        query = db.query(self.model_class)

        if owner_id is not None and hasattr(self.model_class, 'owner_id'):
            query = query.filter(self.model_class.owner_id == owner_id)

        for attr, value in filters.items():
            if hasattr(self.model_class, attr):
                query = query.filter(getattr(self.model_class, attr) == value)

        return query.count()

    @catch_exceptions  # Changé de handle_exceptions
    def exists(self, db: Session, item_id: str) -> bool:
        """
        Vérifie si un objet existe

        Args:
            db: Session de base de données
            item_id: ID de l'objet

        Returns:
            True si l'objet existe, False sinon
        """
        return db.query(self.model_class).filter(self.model_class.id == item_id).count() > 0

    @catch_exceptions  # Changé de handle_exceptions
    def bulk_create(self, db: Session, items_data: List[Dict[str, Any]]) -> List[T]:
        """
        Crée plusieurs objets en une seule transaction

        Args:
            db: Session de base de données
            items_data: Liste des données pour la création

        Returns:
            Liste des objets créés

        Raises:
            ValidationError: Si les données sont invalides
            DatabaseError: En cas d'erreur lors de la création
        """
        # Validation des données requises si le modèle a un attribut required_fields
        if hasattr(self.model_class, 'required_fields'):
            for i, data in enumerate(items_data):
                missing_fields = [field for field in self.model_class.required_fields
                                if field not in data or data[field] is None]
                if missing_fields:
                    raise ValidationError(f"Champs obligatoires manquants dans l'élément {i+1}: {', '.join(missing_fields)}")

        try:
            items = [self.model_class(**data) for data in items_data]
            db.add_all(items)
            db.commit()
            for item in items:
                db.refresh(item)
            return items
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erreur lors de la création en masse de {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Erreur lors de la création en masse: {str(e)}")