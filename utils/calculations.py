"""
Fonctions de calcul pour les analyses patrimoniales
"""
from typing import Dict, List, Any

def get_default_geo_zones(category: str) -> Dict[str, float]:
    """
    Retourne des valeurs par défaut de zones géographiques selon la catégorie d'actif

    Args:
        category: Catégorie d'actif

    Returns:
        Dictionnaire des répartitions géographiques par défaut
    """
    if category == "actions":
        return {
            "amerique_nord": 45,
            "europe_zone_euro": 15,
            "europe_hors_zone_euro": 10,
            "japon": 5,
            "chine": 10,
            "inde": 5,
            "asie_developpee": 5,
            "autres_emergents": 5
        }
    elif category == "obligations":
        return {
            "amerique_nord": 40,
            "europe_zone_euro": 30,
            "europe_hors_zone_euro": 15,
            "japon": 5,
            "autres_emergents": 10
        }
    elif category == "immobilier":
        return {
            "europe_zone_euro": 60,
            "europe_hors_zone_euro": 20,
            "amerique_nord": 20
        }
    elif category == "crypto":
        return {"global_non_classe": 100}
    elif category == "metaux":
        return {"global_non_classe": 100}
    elif category == "cash":
        return {"europe_zone_euro": 100}
    else:
        return {"global_non_classe": 100}

def is_circular_reference(assets: List[Any], parent_id: str, child_id: str, visited_ids: List[str] = None) -> bool:
    """
    Vérifie s'il existe une référence circulaire entre deux actifs

    Cette fonction détecte si l'ajout d'un actif enfant à un actif parent
    créerait une référence circulaire dans la hiérarchie des actifs composites

    Args:
        assets: Liste de tous les actifs
        parent_id: ID de l'actif parent
        child_id: ID de l'actif enfant à ajouter
        visited_ids: Liste des IDs d'actifs déjà visités (pour la récursion)

    Returns:
        True s'il y a une référence circulaire, False sinon
    """
    # Initialiser la liste des visités au premier appel
    if visited_ids is None:
        visited_ids = []

    # Si l'enfant est le parent, c'est une référence circulaire directe
    if child_id == parent_id:
        return True

    # Éviter les boucles infinies
    if child_id in visited_ids:
        return True

    # Marquer cet actif comme visité
    visited_ids.append(child_id)

    # Récupérer l'actif enfant
    child_asset = next((a for a in assets if a.id == child_id), None)
    if not child_asset:
        return False

    # Si l'enfant n'a pas de composants, pas de référence circulaire
    if not hasattr(child_asset, 'composants') or not child_asset.composants:
        return False

    # Vérifier récursivement tous les composants de l'enfant
    for component in child_asset.composants:
        component_id = component.get('asset_id')
        if component_id and is_circular_reference(assets, parent_id, component_id, visited_ids.copy()):
            return True

    # Pas de référence circulaire trouvée
    return False