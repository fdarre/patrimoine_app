"""
Service de gestion des modèles (templates) d'actifs avec propagation des modifications
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from database.models import Asset
from utils.logger import get_logger

logger = get_logger(__name__)


class TemplateService:
    """Service pour la gestion des modèles d'actifs"""

    @staticmethod
    def create_template(db: Session, asset_id: str, template_name: str) -> bool:
        """
        Désigne un actif existant comme modèle de référence

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à désigner comme modèle
            template_name: Nom du modèle pour faciliter l'identification

        Returns:
            True si l'opération a réussi, False sinon
        """
        try:
            # Récupérer l'actif
            asset = db.query(Asset).filter(Asset.id == asset_id).first()
            if not asset:
                return False

            # Le marquer comme modèle
            asset.is_template = True
            asset.template_name = template_name

            db.commit()
            logger.info(f"Actif {asset_id} désigné comme modèle: {template_name}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur lors de la création du modèle: {str(e)}")
            return False

    @staticmethod
    def link_to_template(db: Session, asset_id: str, template_id: str, sync_allocations: bool = True) -> bool:
        """
        Lie un actif à un modèle existant

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à lier
            template_id: ID du modèle
            sync_allocations: Si True, synchronise les allocations au moment de la liaison

        Returns:
            True si l'opération a réussi, False sinon
        """
        try:
            # Récupérer les actifs
            asset = db.query(Asset).filter(Asset.id == asset_id).first()
            template = db.query(Asset).filter(Asset.id == template_id, Asset.is_template == True).first()

            if not asset or not template:
                return False

            # Établir la liaison
            asset.template_id = template_id
            asset.sync_allocations = sync_allocations

            # Synchroniser les allocations si demandé
            if sync_allocations:
                asset.allocation = template.allocation.copy() if template.allocation else {}
                asset.geo_allocation = template.geo_allocation.copy() if template.geo_allocation else {}
                asset.date_maj = datetime.now().strftime("%Y-%m-%d")

            db.commit()
            logger.info(f"Actif {asset_id} lié au modèle {template_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur lors de la liaison au modèle: {str(e)}")
            return False

    @staticmethod
    def unlink_from_template(db: Session, asset_id: str) -> bool:
        """
        Supprime la liaison d'un actif à son modèle

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à délier

        Returns:
            True si l'opération a réussi, False sinon
        """
        try:
            # Récupérer l'actif
            asset = db.query(Asset).filter(Asset.id == asset_id).first()
            if not asset or not asset.template_id:
                return False

            # Supprimer la liaison
            asset.template_id = None
            asset.sync_allocations = False

            db.commit()
            logger.info(f"Actif {asset_id} délié de son modèle")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur lors de la suppression de liaison: {str(e)}")
            return False

    @staticmethod
    def propagate_template_changes(db: Session, template_id: str) -> int:
        """
        Propage les modifications d'allocation et de répartition géographique d'un modèle
        à tous les actifs qui y sont liés et ont sync_allocations=True

        Args:
            db: Session de base de données
            template_id: ID du modèle

        Returns:
            Nombre d'actifs mis à jour
        """
        try:
            # Récupérer le modèle
            template = db.query(Asset).filter(Asset.id == template_id, Asset.is_template == True).first()
            if not template:
                return 0

            # Récupérer tous les actifs liés à ce modèle avec synchronisation activée
            linked_assets = db.query(Asset).filter(
                Asset.template_id == template_id,
                Asset.sync_allocations == True
            ).all()

            update_count = 0

            # Mettre à jour chaque actif lié
            for asset in linked_assets:
                # Copier les allocations et répartitions géographiques
                asset.allocation = template.allocation.copy() if template.allocation else {}
                asset.geo_allocation = template.geo_allocation.copy() if template.geo_allocation else {}
                asset.date_maj = datetime.now().strftime("%Y-%m-%d")
                update_count += 1

            db.commit()
            logger.info(f"Modèle {template_id} propagé à {update_count} actifs")
            return update_count
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur lors de la propagation du modèle: {str(e)}")
            return 0

    @staticmethod
    def get_templates(db: Session, user_id: str) -> List[Asset]:
        """
        Récupère tous les modèles d'un utilisateur

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur

        Returns:
            Liste des actifs marqués comme modèles
        """
        return db.query(Asset).filter(
            Asset.owner_id == user_id,
            Asset.is_template == True
        ).all()

    @staticmethod
    def get_linked_assets(db: Session, template_id: str) -> List[Asset]:
        """
        Récupère tous les actifs liés à un modèle spécifique

        Args:
            db: Session de base de données
            template_id: ID du modèle

        Returns:
            Liste des actifs liés au modèle
        """
        return db.query(Asset).filter(Asset.template_id == template_id).all()

    @staticmethod
    def get_template_candidates(db: Session, user_id: str) -> List[Asset]:
        """
        Récupère les actifs qui pourraient servir de modèles (non déjà liés à un modèle)

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur

        Returns:
            Liste des actifs candidats pour devenir des modèles
        """
        return db.query(Asset).filter(
            Asset.owner_id == user_id,
            Asset.template_id.is_(None),  # Pas déjà lié à un modèle
            Asset.is_template == False  # Pas déjà un modèle
        ).all()


# Créer une instance singleton du service
template_service = TemplateService()