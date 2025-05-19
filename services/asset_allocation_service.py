"""
Service spécialisé pour les calculs d'allocation des actifs
"""
# Imports de la bibliothèque standard
from typing import Dict, Optional

# Imports de bibliothèques tierces
from sqlalchemy.orm import Session, joinedload

# Imports de l'application
from database.models import Asset
from utils.error_manager import catch_exceptions
from utils.logger import get_logger

logger = get_logger(__name__)

class AssetAllocationService:
    """
    Service spécialisé pour les calculs d'allocation et de répartition des actifs

    Ce service isole les fonctionnalités de calcul d'allocation qui étaient
    auparavant dans AssetService, suivant ainsi le principe de responsabilité unique.
    """

    @catch_exceptions
    def calculate_effective_allocation(self, db: Session, asset_id: str) -> Dict[str, float]:
        """
        Calcule l'allocation effective pour un actif

        Args:
            db: Session de base de données
            asset_id: ID de l'actif

        Returns:
            Dictionnaire avec l'allocation effective
        """
        # OPTIMISATION: Utiliser une seule requête avec eager loading pour récupérer l'actif
        asset = db.query(Asset).options(
            joinedload(Asset.account)
        ).filter(Asset.id == asset_id).first()

        if not asset:
            return {}

        # Retourner directement l'allocation de l'actif
        return asset.allocation.copy() if asset.allocation else {}

    @catch_exceptions
    def calculate_effective_geo_allocation(
            self,
            db: Session,
            asset_id: str,
            category: Optional[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcule la répartition géographique effective pour un actif

        Args:
            db: Session de base de données
            asset_id: ID de l'actif
            category: Catégorie spécifique (optionnel)

        Returns:
            Dictionnaire des répartitions géographiques par catégorie
        """
        # Récupérer l'actif avec les relations
        asset = db.query(Asset).filter(Asset.id == asset_id).first()

        if not asset or not asset.geo_allocation:
            return {}

        # Si une catégorie spécifique est demandée, filtrer
        if category:
            if category in asset.geo_allocation:
                return {category: asset.geo_allocation[category]}
            return {}

        # Sinon retourner toutes les répartitions géographiques
        return asset.geo_allocation.copy()


# Créer une instance singleton du service
asset_allocation_service = AssetAllocationService()