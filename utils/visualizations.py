"""
Fonctions utilitaires pour les visualisations
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Any
import streamlit as st


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


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Formate un nombre en pourcentage

    Args:
        value: Valeur à formater
        decimals: Nombre de décimales

    Returns:
        Chaîne formatée
    """
    return f"{value:.{decimals}f}%"


def generate_color_palette(n: int) -> List[str]:
    """
    Génère une palette de couleurs pour les graphiques

    Args:
        n: Nombre de couleurs à générer

    Returns:
        Liste de couleurs au format hexadécimal
    """
    base_colors = [
        "#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f",
        "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"
    ]

    if n <= len(base_colors):
        return base_colors[:n]

    # Si plus de couleurs sont nécessaires, générer des couleurs supplémentaires
    import colorsys

    colors = []
    for i in range(n):
        hue = i / n
        # Garder une saturation et une luminosité constantes
        r, g, b = colorsys.hls_to_rgb(hue, 0.6, 0.7)
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(r * 255), int(g * 255), int(b * 255)
        )
        colors.append(hex_color)

    return colors


def create_pretty_table(data: List[List[Any]], headers: List[str], key: str = None):
    """
    Crée un tableau HTML élégant à afficher dans Streamlit

    Args:
        data: Données du tableau (liste de listes)
        headers: En-têtes des colonnes
        key: Clé unique pour le composant
    """
    # Créer un DataFrame avec Pandas pour faciliter le formatage
    import pandas as pd
    df = pd.DataFrame(data, columns=headers)

    # Afficher le tableau avec Streamlit
    st.dataframe(df, use_container_width=True, key=key)


def get_geo_zone_display_name(zone_code: str) -> str:
    """
    Convertit un code de zone géographique en nom d'affichage plus lisible

    Cette fonction permet d'harmoniser l'affichage des zones géographiques
    dans toute l'application.

    Args:
        zone_code: Code de la zone géographique

    Returns:
        Nom d'affichage de la zone
    """
    display_names = {
        "amerique_nord": "Amérique du Nord",
        "europe_zone_euro": "Europe zone euro",
        "europe_hors_zone_euro": "Europe hors zone euro",
        "japon": "Japon",
        "chine": "Chine",
        "inde": "Inde",
        "asie_developpee": "Asie développée",
        "autres_emergents": "Autres émergents",
        "global_non_classe": "Global/Non classé"
    }
    return display_names.get(zone_code, zone_code.capitalize())