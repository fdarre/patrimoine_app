# ui/assets/geo_allocation_form.py
"""
Module pour la gestion des formulaires de répartition géographique
"""
from typing import Dict, Tuple, Optional

import streamlit as st

from utils.calculations import get_default_geo_zones


def create_geo_allocation_form(
        allocation: Dict[str, float],
        prefix: str,
        existing_geo_allocation: Optional[Dict[str, Dict[str, float]]] = None
) -> Tuple[Dict[str, Dict[str, float]], bool]:
    """
    Crée un formulaire pour la répartition géographique par catégorie

    Args:
        allocation: Dictionnaire d'allocation par catégorie
        prefix: Préfixe pour les clés de session state
        existing_geo_allocation: Répartition géographique existante

    Returns:
        Tuple (dict des répartitions géographiques, validité de toutes les répartitions)
    """
    st.subheader("Répartition géographique par catégorie")

    # Objet pour stocker les répartitions géographiques
    geo_allocation = {}
    all_geo_valid = True

    # Créer des onglets pour chaque catégorie avec allocation > 0
    if allocation:
        geo_tabs = st.tabs([cat.capitalize() for cat in allocation.keys()])

        # Pour chaque catégorie, demander la répartition géographique
        for i, (category, alloc_pct) in enumerate(allocation.items()):
            with geo_tabs[i]:
                st.info(
                    f"Configuration de la répartition géographique pour la partie '{category.capitalize()}' ({alloc_pct}% de l'actif)")

                # Obtenir une répartition par défaut selon la catégorie
                default_geo = get_default_geo_zones(category)

                # Utiliser l'existant si disponible
                current_geo = {}
                if existing_geo_allocation and category in existing_geo_allocation:
                    current_geo = existing_geo_allocation[category]

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

                # Créer des onglets pour les groupes de zones
                region_tabs = st.tabs(list(geo_categories.keys()))

                for tab_idx, (region_group, zones) in enumerate(geo_categories.items()):
                    with region_tabs[tab_idx]:
                        # Utiliser des colonnes pour une meilleure disposition
                        cols = st.columns(2)
                        for j, zone in enumerate(zones):
                            with cols[j % 2]:
                                pct = st.slider(
                                    f"{geo_display_names.get(zone, zone)}",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=float(current_geo.get(zone, default_geo.get(zone, 0.0))),
                                    step=1.0,
                                    key=f"{prefix}_geo_{category}_{zone}"
                                )
                                if pct > 0:
                                    geo_zones[zone] = pct
                                    geo_total += pct

                # Visualisation du total avec classes CSS
                progress_color = "#28a745" if geo_total == 100 else "#ffc107" if geo_total < 100 else "#dc3545"

                st.markdown(f"""
                <div style="margin-top:20px;">
                    <h4 style="margin-bottom:5px;">Total: {geo_total}%</h4>
                    <div style="background:#f8f9fa;height:10px;width:100%;border-radius:5px;">
                        <div style="background:{progress_color};height:10px;width:{min(geo_total, 100)}%;border-radius:5px;"></div>
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
    else:
        st.warning("Veuillez d'abord définir l'allocation par catégorie.")

    return geo_allocation, all_geo_valid


def edit_geo_allocation_form(asset, asset_id, new_allocation):
    """
    Crée un formulaire pour l'édition de la répartition géographique d'un actif

    Args:
        asset: Actif à éditer
        asset_id: ID de l'actif
        new_allocation: Allocation mise à jour

    Returns:
        Tuple (dictionnaire de répartition géographique, validité)
    """
    st.subheader("Répartition géographique par catégorie")

    # Initialiser le stockage pour les allocations géographiques et la validité
    geo_allocation = {}
    all_geo_valid = True

    # Utiliser les allocations fournies pour les catégories
    if new_allocation:
        geo_tabs = st.tabs([cat.capitalize() for cat in new_allocation.keys()])

        # Pour chaque catégorie avec allocation > 0, créer une interface de répartition géo
        for i, (category, allocation_pct) in enumerate(new_allocation.items()):
            with geo_tabs[i]:
                # Afficher les infos de la catégorie
                st.info(
                    f"Configuration de la répartition géographique pour la partie '{category}' ({allocation_pct}% de l'actif)")

                # Obtenir la répartition géo actuelle pour cette catégorie ou utiliser la valeur par défaut
                current_geo = {}
                if asset.geo_allocation and category in asset.geo_allocation:
                    current_geo = asset.geo_allocation[category]
                else:
                    # Utiliser les valeurs par défaut si pas d'allocation existante
                    current_geo = get_default_geo_zones(category)

                # Initialiser le stockage pour les zones géo de cette catégorie
                geo_zones = {}
                geo_total = 0

                # Créer des onglets pour différents groupes de régions
                geo_zone_tabs = st.tabs(["Principales", "Secondaires", "Autres"])

                with geo_zone_tabs[0]:
                    # Zones géo principales
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
                    # Zones géo secondaires
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
                    # Autres zones géo
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

                # Valider le total pour cette catégorie
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

                # Afficher le message de validation
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

                # Sauvegarder la répartition géo pour cette catégorie
                geo_allocation[category] = geo_zones
    else:
        st.warning("Veuillez d'abord définir l'allocation par catégorie.")
        all_geo_valid = False

    return geo_allocation, all_geo_valid


def get_existing_geo_value(prefix, category, zone, current_geo, default_geo):
    """
    Récupère la valeur de répartition géographique existante

    Args:
        prefix: Préfixe pour les clés de session state
        category: Catégorie d'actif
        zone: Zone géographique
        current_geo: Répartition géographique actuelle
        default_geo: Répartition géographique par défaut

    Returns:
        Valeur existante ou valeur par défaut
    """
    # D'abord essayer de récupérer depuis session_state
    key = f"{prefix}_geo_{category}_{zone}"
    if key in st.session_state:
        return st.session_state[key]

    # Ensuite essayer depuis la répartition existante
    if current_geo and zone in current_geo:
        return float(current_geo[zone])

    # Enfin utiliser la valeur par défaut
    return float(default_geo.get(zone, 0.0))
