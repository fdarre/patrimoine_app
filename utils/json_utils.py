"""
Utilitaires pour la manipulation et la validation de données JSON
"""
import json
import logging
from typing import Any, Dict, Union

logger = logging.getLogger(__name__)


def is_valid_json(data: Any) -> bool:
    """
    Vérifie si les données sont du JSON valide

    Args:
        data: Données à vérifier

    Returns:
        True si les données sont du JSON valide, False sinon
    """
    if data is None:
        return False
    try:
        if isinstance(data, str):
            json.loads(data)
        else:
            json.dumps(data)
        return True
    except Exception:
        return False


def safe_json_loads(json_str: Union[str, Dict, None], default: Any = None) -> Any:
    """
    Charge un JSON de manière sécurisée

    Args:
        json_str: Chaîne JSON à charger ou dictionnaire déjà chargé
        default: Valeur par défaut si le chargement échoue

    Returns:
        Données JSON chargées ou valeur par défaut
    """
    if json_str is None:
        return default

    # Si c'est déjà un dictionnaire, le retourner directement
    if isinstance(json_str, dict) or isinstance(json_str, list):
        return json_str

    try:
        return json.loads(json_str)
    except Exception as e:
        logger.warning(f"Erreur lors du chargement JSON: {str(e)}")
        return default


def ensure_valid_allocation(allocation: Any, categories: list) -> Dict[str, float]:
    """
    S'assure qu'une allocation est valide et contient les catégories requises

    Args:
        allocation: Allocation à vérifier
        categories: Liste des catégories requises

    Returns:
        Allocation valide
    """
    # Valeur par défaut: 100% cash
    default_allocation = {cat: 0.0 for cat in categories}
    default_allocation["cash"] = 100.0

    # Si l'allocation est None ou pas un dict, retourner la valeur par défaut
    if allocation is None:
        return default_allocation

    try:
        # Convertir en dict si c'est une chaîne
        if isinstance(allocation, str):
            allocation = json.loads(allocation)

        # Vérifier que c'est un dictionnaire
        if not isinstance(allocation, dict):
            return default_allocation

        # Vérifier que toutes les catégories sont présentes
        valid_allocation = {}
        for cat in categories:
            try:
                value = float(allocation.get(cat, 0.0))
                valid_allocation[cat] = value
            except (ValueError, TypeError):
                valid_allocation[cat] = 0.0

        # Vérifier que la somme est égale à 100%
        total = sum(valid_allocation.values())
        if total == 0:
            # Si tout est à zéro, affecter 100% au cash
            valid_allocation["cash"] = 100.0
        elif total != 100:
            # Normaliser à 100%
            factor = 100.0 / total
            for cat in valid_allocation:
                valid_allocation[cat] *= factor

        return valid_allocation

    except Exception as e:
        logger.error(f"Erreur lors de la validation de l'allocation: {str(e)}")
        return default_allocation


def ensure_valid_geo_allocation(geo_allocation: Any, allocation: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """
    S'assure qu'une répartition géographique est valide

    Args:
        geo_allocation: Répartition géographique à vérifier
        allocation: Allocation par catégorie

    Returns:
        Répartition géographique valide
    """
    # Valeur par défaut: 100% global/non classé pour chaque catégorie
    default_geo = {}
    for cat, value in allocation.items():
        if value > 0:
            default_geo[cat] = {"global_non_classe": 100.0}

    # Si la répartition est None ou pas un dict, retourner la valeur par défaut
    if geo_allocation is None:
        return default_geo

    try:
        # Convertir en dict si c'est une chaîne
        if isinstance(geo_allocation, str):
            geo_allocation = json.loads(geo_allocation)

        # Vérifier que c'est un dictionnaire
        if not isinstance(geo_allocation, dict):
            return default_geo

        # Vérifier que chaque catégorie a une répartition valide
        valid_geo = {}
        for cat, value in allocation.items():
            if value <= 0:
                continue

            cat_geo = geo_allocation.get(cat, {"global_non_classe": 100.0})
            if not isinstance(cat_geo, dict):
                cat_geo = {"global_non_classe": 100.0}

            # Vérifier que la somme est égale à 100%
            total = sum(float(pct) for pct in cat_geo.values())
            if total == 0:
                cat_geo = {"global_non_classe": 100.0}
            elif total != 100:
                # Normaliser à 100%
                factor = 100.0 / total
                for zone in cat_geo:
                    cat_geo[zone] = float(cat_geo[zone]) * factor

            valid_geo[cat] = cat_geo

        return valid_geo

    except Exception as e:
        logger.error(f"Erreur lors de la validation de la répartition géographique: {str(e)}")
        return default_geo