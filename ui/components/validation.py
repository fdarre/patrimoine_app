"""
Utilitaires pour la validation des formulaires
"""
import streamlit as st
from typing import Dict, Any, List


def validate_asset_form(asset_info: Dict[str, Any], allocation: Dict[str, float],
                        geo_allocation: Dict[str, Dict[str, float]] = None) -> bool:
    """
    Valide les données du formulaire d'actif

    Args:
        asset_info: Informations de base de l'actif
        allocation: Dictionnaire d'allocation par catégorie
        geo_allocation: Dictionnaire de répartition géographique

    Returns:
        True si le formulaire est valide, False sinon
    """
    is_valid = True

    # Validation des champs obligatoires
    if not asset_info["name"]:
        st.warning("Le nom de l'actif est obligatoire.")
        is_valid = False

    if not asset_info["account_id"]:
        st.warning("Veuillez sélectionner un compte.")
        is_valid = False

    if asset_info["value"] <= 0:
        st.warning("La valeur actuelle doit être supérieure à 0.")
        is_valid = False

    # Validation de l'allocation par catégorie
    allocation_total = sum(allocation.values()) if allocation else 0
    if allocation_total != 100:
        st.warning(f"Le total des allocations doit être de 100% (actuellement: {allocation_total}%).")
        is_valid = False

    # Validation de la répartition géographique
    if geo_allocation:
        all_geo_valid = True
        for category, zones in geo_allocation.items():
            if sum(zones.values()) != 100:
                st.warning(f"Le total de la répartition géographique pour '{category}' doit être de 100%.")
                all_geo_valid = False

        if not all_geo_valid:
            is_valid = False

    return is_valid


def display_form_errors(asset_info: Dict[str, Any], allocation: Dict[str, float]):
    """
    Affiche les erreurs de validation du formulaire

    Args:
        asset_info: Informations de base de l'actif
        allocation: Dictionnaire d'allocation par catégorie
    """
    if not asset_info["name"]:
        st.warning("Le nom de l'actif est obligatoire.")
    if not asset_info["account_id"]:
        st.warning("Veuillez sélectionner un compte.")
    if asset_info["value"] <= 0:
        st.warning("La valeur actuelle doit être supérieure à 0.")

    allocation_total = sum(allocation.values()) if allocation else 0
    if allocation_total != 100:
        st.warning(f"Le total des allocations doit être de 100% (actuellement: {allocation_total}%).")