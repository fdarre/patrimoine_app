# ui/assets/geo_allocation_form.py
"""
Module pour la gestion des formulaires de répartition géographique
"""
import streamlit as st
from typing import Dict, Tuple
from utils.calculations import get_default_geo_zones


def create_geo_allocation_form(allocation: Dict[str, float], prefix: str) -> Tuple[Dict[str, Dict[str, float]], bool]:
    """
    Crée un formulaire pour la répartition géographique par catégorie

    Args:
        allocation: Dictionnaire d'allocation par catégorie
        prefix: Préfixe pour les clés de session state

    Returns:
        Tuple (dict des répartitions géographiques, validité de toutes les répartitions)
    """
    st.subheader("Répartition géographique par catégorie")

    # Objet pour stocker les répartitions géographiques
    geo_allocation = {}
    all_geo_valid = True

    # Créer des onglets pour chaque catégorie avec allocation > 0
    geo_tabs = st.tabs([cat.capitalize() for cat in allocation.keys()])

    # Pour chaque catégorie, demander la répartition géographique
    for i, (category, alloc_pct) in enumerate(allocation.items()):
        with geo_tabs[i]:
            st.info(
                f"Configuration de la répartition géographique pour la partie '{category.capitalize()}' ({alloc_pct}% de l'actif)")

            # Obtenir une répartition par défaut selon la catégorie
            default_geo = get_default_geo_zones(category)

            # Variables pour stocker la répartition géographique
            geo_zones = {}
            geo_total = 0

            # Interface améliorée avec régions groupées
            geo_categories = {
                "Marchés développés": ["amerique_nord", "europe_zone_euro", "europe_hors_zone_euro", "japon"],
                "Marchés émergents": ["chine", "inde", "asie_developpee", "autres_emergents"],
                "Global": ["global_non_classe"]
            }

            # Noms d'affichage pour les zones géographiques
            geo_display_names = {
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

            for region_group, zones in geo_categories.items():
                st.subheader(region_group)
                # Utiliser des colonnes pour une meilleure disposition
                if len(zones) > 1:
                    cols = st.columns(2)
                    for j, zone in enumerate(zones):
                        with cols[j % 2]:
                            pct = st.slider(
                                f"{geo_display_names.get(zone, zone)}",
                                min_value=0.0,
                                max_value=100.0,
                                value=get_existing_geo_allocation(prefix, category, zone, default_geo),
                                step=1.0,
                                key=f"{prefix}_geo_{category}_{zone}"
                            )
                            if pct > 0:
                                geo_zones[zone] = pct
                                geo_total += pct
                else:
                    zone = zones[0]
                    pct = st.slider(
                        f"{geo_display_names.get(zone, zone)}",
                        min_value=0.0,
                        max_value=100.0,
                        value=get_existing_geo_allocation(prefix, category, zone, default_geo),
                        step=1.0,
                        key=f"{prefix}_geo_{category}_{zone}"
                    )
                    if pct > 0:
                        geo_zones[zone] = pct
                        geo_total += pct

            # Visualisation du total avec classes CSS
            progress_class = "allocation-total-valid"
            if geo_total < 100:
                progress_class = "allocation-total-warning"
            elif geo_total > 100:
                progress_class = "allocation-total-error"

            st.markdown(f"""
            <div class="allocation-total">
                <h4 class="allocation-total-label">Total: {geo_total}%</h4>
                <div class="allocation-total-bar-bg">
                    <div class="allocation-total-bar {progress_class}" style="width:{min(geo_total, 100)}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Message de validation
            geo_valid = geo_total == 100
            if not geo_valid:
                all_geo_valid = False
                if geo_total < 100:
                    st.warning(
                        f"Le total de la répartition géographique pour '{category}' doit être de 100%. Actuellement: {geo_total}%")
                else:
                    st.error(
                        f"Le total de la répartition géographique pour '{category}' ne doit pas dépasser 100%. Actuellement: {geo_total}%")
            else:
                st.success(f"Répartition géographique pour '{category}' valide (100%)")

            # Enregistrer la répartition géographique pour cette catégorie
            geo_allocation[category] = geo_zones

    return geo_allocation, all_geo_valid


def edit_geo_allocation_form(asset, asset_id: str, new_allocation: Dict[str, float]) -> Tuple[
    Dict[str, Dict[str, float]], bool]:
    """
    Crée un formulaire pour l'édition de la répartition géographique d'un actif existant

    Args:
        asset: Actif à éditer
        asset_id: ID de l'actif
        new_allocation: Nouvelle allocation par catégorie

    Returns:
        Tuple (dict des répartitions géographiques, validité de toutes les répartitions)
    """
    st.subheader("Répartition géographique par catégorie")

    # Créer un objet pour stocker les nouvelles répartitions géographiques
    new_geo_allocation = {}
    all_geo_valid = True

    # Utiliser des onglets pour chaque catégorie ayant une allocation > 0
    geo_tabs = st.tabs([cat.capitalize() for cat in new_allocation.keys()])

    for i, (category, allocation_pct) in enumerate(new_allocation.items()):
        with geo_tabs[i]:
            st.info(
                f"Configuration de la répartition géographique pour la partie '{category}' ({allocation_pct}% de l'actif)")

            # Obtenir la répartition actuelle ou une répartition par défaut
            current_geo = asset.geo_allocation.get(category, get_default_geo_zones(category))

            # Interface pour éditer les pourcentages
            geo_zones = {}
            geo_total = 0

            # Créer des onglets pour faciliter la saisie
            geo_zone_tabs = st.tabs(["Principales", "Secondaires", "Autres"])

            with geo_zone_tabs[0]:
                # Zones principales
                main_zones = ["amerique_nord", "europe_zone_euro", "europe_hors_zone_euro", "japon"]
                cols = st.columns(2)
                for j, zone in enumerate(main_zones):
                    with cols[j % 2]:
                        pct = st.slider(
                            f"{zone.capitalize()} (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(current_geo.get(zone, 0.0)),
                            step=1.0,
                            key=f"edit_asset_geo_{asset_id}_{category}_{zone}"
                        )
                        if pct > 0:
                            geo_zones[zone] = pct
                            geo_total += pct

            with geo_zone_tabs[1]:
                # Zones secondaires
                secondary_zones = ["chine", "inde", "asie_developpee", "autres_emergents"]
                cols = st.columns(2)
                for j, zone in enumerate(secondary_zones):
                    with cols[j % 2]:
                        pct = st.slider(
                            f"{zone.capitalize()} (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(current_geo.get(zone, 0.0)),
                            step=1.0,
                            key=f"edit_asset_geo_{asset_id}_{category}_{zone}"
                        )
                        if pct > 0:
                            geo_zones[zone] = pct
                            geo_total += pct

            with geo_zone_tabs[2]:
                # Autres zones
                other_zones = ["global_non_classe"]
                cols = st.columns(2)
                for j, zone in enumerate(other_zones):
                    with cols[j % 2]:
                        pct = st.slider(
                            f"{zone.capitalize()} (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(current_geo.get(zone, 0.0)),
                            step=1.0,
                            key=f"edit_asset_geo_{asset_id}_{category}_{zone}"
                        )
                        if pct > 0:
                            geo_zones[zone] = pct
                            geo_total += pct

            # Visualisation du total avec classes CSS
            progress_class = "allocation-total-valid"
            if geo_total < 100:
                progress_class = "allocation-total-warning"
            elif geo_total > 100:
                progress_class = "allocation-total-error"

            st.markdown(f"""
            <div class="allocation-total">
                <h4 class="allocation-total-label">Total: {geo_total}%</h4>
                <div class="allocation-total-bar-bg">
                    <div class="allocation-total-bar {progress_class}" style="width:{min(geo_total, 100)}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            geo_valid = geo_total == 100
            if not geo_valid:
                all_geo_valid = False
                if geo_total < 100:
                    st.warning(
                        f"Le total de la répartition géographique pour '{category}' doit être de 100%. Actuellement: {geo_total}%")
                else:
                    st.error(
                        f"Le total de la répartition géographique pour '{category}' ne doit pas dépasser 100%. Actuellement: {geo_total}%")
            else:
                st.success(f"Répartition géographique pour '{category}' valide (100%)")

            # Enregistrer la répartition géographique pour cette catégorie
            new_geo_allocation[category] = geo_zones

    return new_geo_allocation, all_geo_valid


def get_existing_geo_allocation(prefix: str, category: str, zone: str, default_geo: Dict[str, float]) -> float:
    """
    Récupère la valeur de répartition géographique existante si disponible dans la session

    Args:
        prefix: Préfixe pour les clés de session state
        category: Catégorie d'actif
        zone: Zone géographique
        default_geo: Répartition géographique par défaut

    Returns:
        Valeur existante ou valeur par défaut
    """
    key = f"{prefix}_geo_{category}_{zone}"
    if key in st.session_state:
        return st.session_state[key]
    return float(default_geo.get(zone, 0.0))