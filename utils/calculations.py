"""
Fonctions de calcul pour les analyses patrimoniales
"""

from typing import Dict, List, Optional, Any
from models.asset import Asset


def get_default_geo_zones(category: str) -> Dict[str, float]:
    """
    Retourne des valeurs par défaut de zones géographiques selon la catégorie d'actif

    Args:
        category: Catégorie d'actif

    Returns:
        Dictionnaire des répartitions géographiques par défaut
    """
    if category == "actions":
        return {"us": 60, "europe": 20, "japan": 10, "emerging": 5, "autre": 5}
    elif category == "obligations":
        return {"europe": 80, "us": 20}
    elif category == "immobilier":
        return {"europe": 100}
    elif category == "crypto":
        return {"monde": 100}
    elif category == "metaux":
        return {"monde": 100}
    elif category == "cash":
        return {"europe": 100}
    else:
        return {"europe": 100}


def calculate_category_values(
        assets: List[Asset],
        accounts: Dict[str, Dict[str, Any]],
        filtered_assets: Optional[List[Asset]] = None,
        asset_categories: List[str] = None
) -> Dict[str, float]:
    """
    Calcule la répartition par catégorie en tenant compte des allocations mixtes
    et des actifs composites

    Args:
        assets: Liste complète des actifs (pour résoudre les références des composants)
        accounts: Dictionnaire des comptes
        filtered_assets: Liste filtrée des actifs à analyser (utilise assets si None)
        asset_categories: Liste des catégories à considérer

    Returns:
        Dictionnaire avec les valeurs par catégorie
    """
    if asset_categories is None:
        from utils.constants import ASSET_CATEGORIES
        asset_categories = ASSET_CATEGORIES

    if filtered_assets is None:
        filtered_assets = assets

    category_values = {cat: 0 for cat in asset_categories}

    for asset in filtered_assets:
        # Pour les actifs directs (non composites)
        if not asset.is_composite():
            for category, percentage in asset.allocation.items():
                # Calculer la valeur allouée à cette catégorie
                allocated_value = asset.valeur_actuelle * percentage / 100
                category_values[category] += allocated_value
        else:
            # Pour les actifs composites
            # Calculer l'allocation effective
            from services.asset_service import AssetService
            effective_allocation = AssetService.calculate_effective_allocation(assets, asset)

            for category, percentage in effective_allocation.items():
                allocated_value = asset.valeur_actuelle * percentage / 100
                category_values[category] += allocated_value

    return category_values


def calculate_geo_values(
        assets: List[Asset],
        accounts: Dict[str, Dict[str, Any]],
        filtered_assets: Optional[List[Asset]] = None,
        category: Optional[str] = None,
        geo_zones: List[str] = None
) -> Dict[str, float]:
    """
    Calcule la répartition géographique en tenant compte des allocations mixtes
    et des actifs composites

    Args:
        assets: Liste complète des actifs (pour résoudre les références des composants)
        accounts: Dictionnaire des comptes
        filtered_assets: Liste filtrée des actifs à analyser (utilise assets si None)
        category: Catégorie spécifique à analyser (optionnel)
        geo_zones: Liste des zones géographiques à considérer

    Returns:
        Dictionnaire avec les valeurs par zone géographique
    """
    if geo_zones is None:
        from utils.constants import GEO_ZONES
        geo_zones = GEO_ZONES

    if filtered_assets is None:
        filtered_assets = assets

    geo_values = {zone: 0 for zone in geo_zones}

    from services.asset_service import AssetService

    for asset in filtered_assets:
        # Si une catégorie est spécifiée, ne considérer que cette partie de l'actif
        if category:
            if category not in asset.allocation:
                continue

            # Pour les actifs non composites
            if not asset.is_composite():
                # Valeur allouée à cette catégorie
                category_value = asset.valeur_actuelle * asset.allocation[category] / 100

                # Répartition géographique pour cette catégorie
                geo_zones_dict = asset.geo_allocation.get(category, asset.zone_geographique)

                for zone, percentage in geo_zones_dict.items():
                    geo_values[zone] += category_value * percentage / 100
            else:
                # Pour les actifs composites, calculer la répartition effective
                effective_geo = AssetService.calculate_effective_geo_allocation(assets, asset, category)
                category_value = asset.valeur_actuelle * asset.allocation.get(category, 0) / 100

                for zone, percentage in effective_geo.get(category, {}).items():
                    geo_values[zone] += category_value * percentage / 100
        else:
            # Pour tous les actifs, ventiler selon les allocations et répartitions géographiques
            if not asset.is_composite():
                for cat, allocation_pct in asset.allocation.items():
                    category_value = asset.valeur_actuelle * allocation_pct / 100

                    # Utiliser la répartition géographique spécifique à cette catégorie si disponible
                    geo_zones_dict = asset.geo_allocation.get(cat, asset.zone_geographique)

                    for zone, percentage in geo_zones_dict.items():
                        geo_values[zone] += category_value * percentage / 100
            else:
                # Pour les actifs composites, calculer la répartition effective pour chaque catégorie
                for cat, allocation_pct in asset.allocation.items():
                    effective_geo = AssetService.calculate_effective_geo_allocation(assets, asset, cat)
                    category_value = asset.valeur_actuelle * allocation_pct / 100

                    for zone, percentage in effective_geo.get(cat, {}).items():
                        geo_values[zone] += category_value * percentage / 100

    return geo_values


def calculate_total_patrimony(assets: List[Asset]) -> float:
    """
    Calcule la valeur totale du patrimoine

    Args:
        assets: Liste des actifs

    Returns:
        Valeur totale du patrimoine
    """
    return sum(asset.valeur_actuelle for asset in assets)


def is_circular_reference(
        assets: List[Asset],
        source_id: str,
        target_id: str,
        visited: Optional[List[str]] = None
) -> bool:
    """
    Vérifie s'il y a une référence circulaire lors de l'ajout d'un composant

    Args:
        assets: Liste des actifs
        source_id: ID de l'actif source
        target_id: ID de l'actif cible qu'on veut ajouter comme composant
        visited: Liste des IDs déjà visités (pour la récursivité)

    Returns:
        True s'il y a une référence circulaire, False sinon
    """
    if visited is None:
        visited = []

    if source_id == target_id:
        return True

    if source_id in visited:
        return False

    visited.append(source_id)

    # Chercher l'actif cible
    target_asset = None
    for asset in assets:
        if asset.id == target_id:
            target_asset = asset
            break

    if not target_asset:
        return False

    # Vérifier récursivement pour les composants de la cible
    for component in target_asset.composants:
        if is_circular_reference(assets, source_id, component["asset_id"], visited):
            return True

    return False