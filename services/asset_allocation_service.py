"""
Service spécialisé pour les calculs d'allocation des actifs
"""
# Imports de la bibliothèque standard
from typing import List, Dict, Optional

# Imports de bibliothèques tierces
from sqlalchemy.orm import Session, joinedload

# Imports de l'application
from database.models import Asset
from utils.common import safe_json_loads
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
        Calcule l'allocation effective pour un actif composite

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

        # Si l'actif n'a pas de composants, retourner son allocation
        composants = safe_json_loads(getattr(asset, 'composants', '[]'), [])
        if not composants:
            return asset.allocation.copy() if asset.allocation else {}

        # Initialiser l'allocation effective à 0 pour toutes les catégories
        effective_allocation = {category: 0.0 for category in asset.allocation} if asset.allocation else {}

        # Calculer la somme des pourcentages des composants
        total_component_percentage = sum(comp.get('percentage', 0) for comp in composants)

        # Si la somme est supérieure à 100%, normaliser
        normalization_factor = 100.0 / total_component_percentage if total_component_percentage > 100 else 1.0

        # Pourcentage restant pour l'allocation directe
        direct_percentage = max(0, 100 - total_component_percentage * normalization_factor)

        # Ajouter l'allocation directe
        if direct_percentage > 0 and asset.allocation:
            for category, percentage in asset.allocation.items():
                effective_allocation[category] = percentage * direct_percentage / 100.0

        # OPTIMISATION: Récupérer tous les composants en une seule requête
        component_ids = [comp.get('asset_id') for comp in composants if comp.get('asset_id')]
        if component_ids:
            components_query = db.query(Asset).filter(Asset.id.in_(component_ids))
            component_assets = {a.id: a for a in components_query.all()}

            # Ajouter l'allocation des composants
            for comp in composants:
                comp_id = comp.get('asset_id')
                comp_percentage = comp.get('percentage', 0) * normalization_factor / 100.0

                if comp_id and comp_id in component_assets:
                    comp_asset = component_assets[comp_id]
                    if comp_asset.allocation:
                        for category, percentage in comp_asset.allocation.items():
                            if category not in effective_allocation:
                                effective_allocation[category] = 0.0
                            effective_allocation[category] += percentage * comp_percentage

        return effective_allocation

    @catch_exceptions
    def calculate_effective_geo_allocation(
            self,
            db: Session,
            asset_id: str,
            category: Optional[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcule la répartition géographique effective pour un actif composite

        Args:
            db: Session de base de données
            asset_id: ID de l'actif
            category: Catégorie spécifique (optionnel)

        Returns:
            Dictionnaire des répartitions géographiques par catégorie
        """
        # Récupérer l'actif avec les relations
        asset = db.query(Asset).filter(Asset.id == asset_id).first()

        if not asset:
            return {}

        # Si l'actif n'a pas de composants ou d'allocation, retourner sa répartition
        composants = safe_json_loads(getattr(asset, 'composants', '[]'), [])
        if not composants or not asset.allocation:
            return asset.geo_allocation.copy() if asset.geo_allocation else {}

        # Si une catégorie spécifique est demandée, filtrer
        categories = [category] if category else asset.allocation.keys()

        # Calculer l'allocation effective
        effective_allocation = self.calculate_effective_allocation(db, asset_id)

        # Initialiser la répartition géographique effective
        effective_geo = {}

        # OPTIMISATION: Récupérer tous les composants en une seule requête
        component_ids = [comp.get('asset_id') for comp in composants if comp.get('asset_id')]
        component_assets = {}

        if component_ids:
            component_assets = {a.id: a for a in db.query(Asset).filter(Asset.id.in_(component_ids)).all()}

        # Calculer la somme des pourcentages des composants
        total_component_percentage = sum(comp.get('percentage', 0) for comp in composants)

        # Si la somme est supérieure à 100%, normaliser
        normalization_factor = 100.0 / total_component_percentage if total_component_percentage > 100 else 1.0

        # Pourcentage restant pour l'allocation directe
        direct_percentage = max(0, 100 - total_component_percentage * normalization_factor)

        # Pour chaque catégorie demandée
        for cat in categories:
            if cat not in effective_allocation or effective_allocation[cat] <= 0:
                continue

            # Initialiser la répartition pour cette catégorie
            effective_geo[cat] = {}

            # Ajouter la répartition directe si applicable
            if direct_percentage > 0 and asset.geo_allocation and cat in asset.geo_allocation:
                direct_weight = (asset.allocation.get(cat, 0) * direct_percentage / 100.0) / effective_allocation[cat]

                for zone, percentage in asset.geo_allocation[cat].items():
                    effective_geo[cat][zone] = percentage * direct_weight

            # Ajouter la répartition des composants
            for comp in composants:
                comp_id = comp.get('asset_id')
                comp_percentage = comp.get('percentage', 0) * normalization_factor / 100.0

                if comp_id and comp_id in component_assets:
                    comp_asset = component_assets[comp_id]

                    if (comp_asset.allocation and comp_asset.geo_allocation and
                            cat in comp_asset.allocation and cat in comp_asset.geo_allocation):

                        # Poids de ce composant dans l'allocation effective de la catégorie
                        comp_weight = (comp_asset.allocation[cat] * comp_percentage / 100.0) / effective_allocation[cat]

                        # Ajouter la répartition géographique pondérée
                        for zone, percentage in comp_asset.geo_allocation[cat].items():
                            if zone not in effective_geo[cat]:
                                effective_geo[cat][zone] = 0.0
                            effective_geo[cat][zone] += percentage * comp_weight

            # Normaliser à 100%
            zone_sum = sum(effective_geo[cat].values())
            if zone_sum > 0:
                for zone in effective_geo[cat]:
                    effective_geo[cat][zone] = (effective_geo[cat][zone] / zone_sum) * 100.0

        return effective_geo

    @catch_exceptions
    def is_used_as_component(self, db: Session, asset_id: str) -> bool:
        """
        Vérifie si un actif est utilisé comme composant dans d'autres actifs

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à vérifier

        Returns:
            True si l'actif est utilisé comme composant, False sinon
        """
        # Cette vérification est plus complexe car les composants sont stockés dans un champ JSON
        # Nous devons récupérer tous les actifs et vérifier manuellement
        assets = db.query(Asset).all()

        for asset in assets:
            componants = safe_json_loads(getattr(asset, 'composants', '[]'), [])

            for comp in componants:
                if comp.get('asset_id') == asset_id:
                    return True

        return False

    @catch_exceptions
    def add_component(self, db: Session, asset_id: str, component_id: str, percentage: float) -> bool:
        """
        Ajoute un composant à un actif composite

        Args:
            db: Session de base de données
            asset_id: ID de l'actif principal
            component_id: ID de l'actif à ajouter comme composant
            percentage: Pourcentage du composant

        Returns:
            True si le composant a été ajouté avec succès, False sinon
        """
        # Vérifier que l'actif principal existe
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return False

        # Vérifier que le composant existe
        component = db.query(Asset).filter(Asset.id == component_id).first()
        if not component:
            return False

        # Vérifier qu'il n'y a pas de référence circulaire
        if self.is_circular_reference(db, asset_id, component_id):
            logger.warning(f"Détection d'une référence circulaire: {asset_id} -> {component_id}")
            return False

        # Récupérer les composants actuels
        componants = safe_json_loads(getattr(asset, 'composants', '[]'), [])

        # Vérifier si le composant existe déjà
        for comp in componants:
            if comp.get('asset_id') == component_id:
                # Mettre à jour le pourcentage
                comp['percentage'] = percentage
                break
        else:
            # Ajouter le nouveau composant
            componants.append({
                'asset_id': component_id,
                'percentage': percentage
            })

        # Mettre à jour l'actif
        asset.composants = componants
        db.commit()

        return True

    @catch_exceptions
    def remove_component(self, db: Session, asset_id: str, component_id: str) -> bool:
        """
        Supprime un composant d'un actif composite

        Args:
            db: Session de base de données
            asset_id: ID de l'actif principal
            component_id: ID du composant à supprimer

        Returns:
            True si le composant a été supprimé avec succès, False sinon
        """
        # Vérifier que l'actif principal existe
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return False

        # Récupérer les composants actuels
        componants = safe_json_loads(getattr(asset, 'composants', '[]'), [])

        # Filtrer les composants
        new_componants = [comp for comp in componants if comp.get('asset_id') != component_id]

        # Si aucun composant n'a été supprimé
        if len(new_componants) == len(componants):
            return False

        # Mettre à jour l'actif
        asset.composants = new_componants
        db.commit()

        return True

    @catch_exceptions
    def is_circular_reference(self, db: Session, parent_id: str, child_id: str, visited: List[str] = None) -> bool:
        """
        Vérifie s'il existe une référence circulaire entre deux actifs

        Args:
            db: Session de base de données
            parent_id: ID de l'actif parent
            child_id: ID de l'actif enfant
            visited: Liste des IDs déjà visités

        Returns:
            True s'il y a une référence circulaire, False sinon
        """
        # Initialiser la liste des visités
        if visited is None:
            visited = []

        # Si l'enfant est le parent, c'est une référence circulaire directe
        if child_id == parent_id:
            return True

        # Éviter les boucles infinies
        if child_id in visited:
            return True

        # Marquer cet actif comme visité
        visited.append(child_id)

        # Récupérer l'actif enfant
        child_asset = db.query(Asset).filter(Asset.id == child_id).first()
        if not child_asset:
            return False

        # Si l'enfant n'a pas de composants, pas de référence circulaire
        componants = safe_json_loads(getattr(child_asset, 'composants', '[]'), [])
        if not componants:
            return False

        # Vérifier récursivement tous les composants de l'enfant
        for comp in componants:
            component_id = comp.get('asset_id')
            if component_id and self.is_circular_reference(db, parent_id, component_id, visited.copy()):
                return True

        # Pas de référence circulaire trouvée
        return False


# Créer une instance singleton du service
asset_allocation_service = AssetAllocationService()