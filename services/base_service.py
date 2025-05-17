"""
Service de base générique pour les opérations CRUD
"""
from typing import List, Optional, TypeVar, Generic, Type, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import Base
from utils.exceptions import DatabaseError
from utils.logger import get_logger
from utils.decorators import handle_exceptions

# Type générique pour les modèles SQLAlchemy
T = TypeVar('T', bound=Base)
logger = get_logger(__name__)


class BaseService(Generic[T]):
    """Service de base générique pour les opérations CRUD"""

    def __init__(self, model_class: Type[T]):
        self.model_class = model_class

    @handle_exceptions
    def get_all(self, db: Session, owner_id: str = None, **filters) -> List[T]:
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

    @handle_exceptions
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

    @handle_exceptions
    def create(self, db: Session, data: Dict[str, Any]) -> T:
        """
        Crée un nouvel objet

        Args:
            db: Session de base de données
            data: Données pour la création

        Returns:
            Nouvel objet créé

        Raises:
            DatabaseError: En cas d'erreur lors de la création
        """
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

    @handle_exceptions
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

    @handle_exceptions
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

    @handle_exceptions
    def count(self, db: Session, owner_id: str = None, **filters) -> int:
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