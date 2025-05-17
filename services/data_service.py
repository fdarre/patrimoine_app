"""
Service de chargement et sauvegarde des données avec SQLAlchemy
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from database.models import Asset, HistoryPoint
from utils.decorators import handle_exceptions
from utils.logger import get_logger
from utils.common import safe_float_conversion

logger = get_logger(__name__)

class DataService:
    """Service de gestion des données persistantes avec SQLAlchemy"""

    @staticmethod
    @handle_exceptions
    def record_history_entry(db: Session, user_id: str) -> HistoryPoint:
        """
        Enregistre un point d'historique pour tous les actifs d'un utilisateur

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur

        Returns:
            Le point d'historique créé
        """
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Récupérer tous les actifs de l'utilisateur
        assets = db.query(Asset).filter(Asset.owner_id == user_id).all()

        # Vérifier si on a déjà un enregistrement pour aujourd'hui
        existing_entry = db.query(HistoryPoint).filter(HistoryPoint.date == current_date).first()

        # Utiliser value_eur pour l'historique
        assets_dict = {}
        total_value = 0.0

        for asset in assets:
            # Utiliser value_eur s'il existe, sinon valeur_actuelle
            value = safe_float_conversion(asset.value_eur) or safe_float_conversion(asset.valeur_actuelle)
            assets_dict[asset.id] = value
            total_value += value

        if existing_entry:
            # Mettre à jour l'entrée existante
            existing_entry.assets = assets_dict
            existing_entry.total = total_value
            db.commit()
            db.refresh(existing_entry)
            logger.info(f"Point d'historique mis à jour pour {current_date}")
            return existing_entry
        else:
            # Créer une nouvelle entrée
            new_entry = HistoryPoint(
                date=current_date,
                assets=assets_dict,
                total=total_value
            )
            db.add(new_entry)
            db.commit()
            db.refresh(new_entry)
            logger.info(f"Nouveau point d'historique créé pour {current_date}")
            return new_entry

    @staticmethod
    @handle_exceptions
    def get_history(db: Session, days: Optional[int] = None) -> List[HistoryPoint]:
        """
        Récupère l'historique des valeurs

        Args:
            db: Session de base de données
            days: Nombre de jours à récupérer (None pour tout l'historique)

        Returns:
            Liste des points d'historique
        """
        query = db.query(HistoryPoint).order_by(HistoryPoint.date)

        if days:
            # Récupérer uniquement les N derniers jours
            query = query.order_by(HistoryPoint.date.desc()).limit(days)
            result = query.all()
            # Réordonner par date croissante
            result.reverse()
            return result

        return query.all()