"""
Fonctions utilitaires communes réutilisables
"""
import json
import uuid
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from utils.exceptions import ValidationError
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_uuid() -> str:
    """
    Génère un UUID unique

    Returns:
        UUID au format string
    """
    return str(uuid.uuid4())


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Vérifie que tous les champs requis sont présents et non vides

    Args:
        data: Dictionnaire de données
        required_fields: Liste des champs obligatoires

    Returns:
        True si tous les champs requis sont présents et non vides

    Raises:
        ValidationError: Si un champ requis est manquant ou vide
    """
    missing_fields = []

    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            missing_fields.append(field)

    if missing_fields:
        raise ValidationError(f"Champs obligatoires manquants ou vides: {', '.join(missing_fields)}")

    return True


def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Convertit une valeur en float de manière sécurisée

    Args:
        value: Valeur à convertir
        default: Valeur par défaut si la conversion échoue

    Returns:
        Valeur convertie en float ou valeur par défaut
    """
    if value is None:
        return default

    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Parse une chaîne JSON de manière sécurisée

    Args:
        json_str: Chaîne JSON à parser
        default: Valeur par défaut si le parsing échoue

    Returns:
        Objet JSON parsé ou valeur par défaut
    """
    if not json_str:
        return default

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return default


def format_currency(value: float, currency: str = "€", decimals: int = 2) -> str:
    """
    Formate un nombre en valeur monétaire avec séparateurs de milliers

    Args:
        value: Valeur à formater
        currency: Symbole de la devise
        decimals: Nombre de décimales

    Returns:
        Chaîne formatée
    """
    return f"{value:,.{decimals}f} {currency}".replace(",", " ")


def format_percentage(value: float, decimals: int = 2, with_sign: bool = False) -> str:
    """
    Formate un nombre en pourcentage

    Args:
        value: Valeur à formater
        decimals: Nombre de décimales
        with_sign: Ajouter un signe + pour les valeurs positives

    Returns:
        Chaîne formatée
    """
    if with_sign and value > 0:
        return f"+{value:.{decimals}f}%"
    return f"{value:.{decimals}f}%"


def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Divise une liste en morceaux de taille n

    Args:
        lst: Liste à diviser
        n: Taille des morceaux

    Returns:
        Liste de listes
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fusionne deux dictionnaires de manière récursive

    Args:
        dict1: Premier dictionnaire
        dict2: Second dictionnaire (prioritaire en cas de conflit)

    Returns:
        Dictionnaire fusionné
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def df_to_dict_list(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convertit un DataFrame en liste de dictionnaires

    Args:
        df: DataFrame à convertir

    Returns:
        Liste de dictionnaires
    """
    return df.to_dict(orient='records')


def dict_list_to_df(dict_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convertit une liste de dictionnaires en DataFrame

    Args:
        dict_list: Liste de dictionnaires à convertir

    Returns:
        DataFrame
    """
    return pd.DataFrame(dict_list)