"""
Service de chargement et sauvegarde des données avec SQLAlchemy
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from database.models import Asset, HistoryPoint

class DataService:
    """Service de gestion des données persistantes avec SQLAlchemy"""

    @staticmethod
    def record_history_entry(db: Session, user_id: str, assets: List[Asset] = None) -> HistoryPoint:
        """
        Enregistre un point d'historique pour tous les actifs d'un utilisateur

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            assets: Liste des actifs (si None, récupère tous les actifs de l'utilisateur)

        Returns:
            Le point d'historique créé
        """
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Si la liste d'actifs n'est pas fournie, récupérer tous les actifs de l'utilisateur
        if assets is None:
            assets = db.query(Asset).filter(Asset.owner_id == user_id).all()

        # Vérifier si on a déjà un enregistrement pour aujourd'hui
        existing_entry = db.query(HistoryPoint).filter(HistoryPoint.date == current_date).first()

        if existing_entry:
            # Mettre à jour l'entrée existante
            existing_entry.assets = {asset.id: asset.valeur_actuelle for asset in assets}
            existing_entry.total = sum(asset.valeur_actuelle for asset in assets)
            db.commit()
            db.refresh(existing_entry)
            return existing_entry
        else:
            # Créer une nouvelle entrée
            new_entry = HistoryPoint(
                date=current_date,
                assets={asset.id: asset.valeur_actuelle for asset in assets},
                total=sum(asset.valeur_actuelle for asset in assets)
            )
            db.add(new_entry)
            db.commit()
            db.refresh(new_entry)
            return new_entry

    @staticmethod
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

        return query.all()