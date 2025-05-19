"""
Fonctions de calcul pour les analyses patrimoniales
"""
from typing import Dict, Any

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

def calculate_asset_performance(valeur_actuelle: float, prix_de_revient: float) -> Dict[str, Any]:
    """
    Calcule la performance d'un actif de manière standardisée

    Args:
        valeur_actuelle: Valeur actuelle de l'actif
        prix_de_revient: Prix de revient de l'actif

    Returns:
        Dictionnaire contenant la valeur, le pourcentage et le signe de la plus-value
    """
    pv = valeur_actuelle - prix_de_revient
    pv_percent = (pv / prix_de_revient * 100) if prix_de_revient > 0 else 0

    return {
        "value": pv,
        "percent": pv_percent,
        "is_positive": pv_percent >= 0
    }