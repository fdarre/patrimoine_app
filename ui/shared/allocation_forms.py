"""
Module partagé pour les formulaires d'allocation et de répartition géographique
"""
import streamlit as st
from typing import Dict, Tuple, List, Any, Optional
from utils.calculations import get_default_geo_zones


def create_allocation_form(prefix: str, existing_allocation: Dict[str, float] = None) -> Dict[str, float]:
    """
    Crée un formulaire pour l'allocation par catégorie

    Args:
        prefix: Préfixe pour les clés de session state
        existing_allocation: Allocation existante (optionnel)

    Returns:
        Dictionnaire des allocations {catégorie: pourcentage}
    """
    st.subheader("Allocation par catégorie")
    st.info("Répartissez la valeur de l'actif entre les différentes catégories (total 100%)")

    # Variables pour stocker les allocations
    allocation = {}
    allocation_total = 0

    # Définition des couleurs par catégorie
    category_colors = {
        "actions": "#4e79a7",
        "obligations": "#f28e2c",
        "immobilier": "#e15759",
        "crypto": "#76b7b2",
        "metaux": "#59a14f",
        "cash": "#edc949",
        "autre": "#af7aa1"
    }

    # Interface améliorée pour l'allocation avec barres de progression
    col1, col2 = st.columns(2)

    # Première colonne: principaux types d'actifs
    with col1:
        for category in ["actions", "obligations", "immobilier", "cash"]:
            percentage = st.slider(
                f"{category.capitalize()} (%)",
                min_value=0.0,
                max_value=100.0,
                value=get_existing_value(prefix, category, existing_allocation),
                step=1.0,
                key=f"{prefix}_alloc_{category}"
            )
            if percentage > 0:
                allocation[category] = percentage
                allocation_total += percentage

                # Afficher une barre de progression colorée pour cette catégorie
                st.markdown(f"""
                <div style="display:flex;align-items:center;margin-bottom:8px;">
                    <div style="width:80px;">{category.capitalize()}</div>
                    <div style="background:#f8f9fa;height:8px;width:70%;margin:0 10px;">
                        <div style="background:{category_colors[category]};height:8px;width:{percentage}%;"></div>
                    </div>
                    <div>{percentage}%</div>
                </div>
                """, unsafe_allow_html=True)

    # Deuxième colonne: autres types d'actifs
    with col2:
        for category in ["crypto", "metaux", "autre"]:
            percentage = st.slider(
                f"{category.capitalize()} (%)",
                min_value=0.0,
                max_value=100.0,
                value=get_existing_value(prefix, category, existing_allocation),
                step=1.0,
                key=f"{prefix}_alloc_{category}"
            )
            if percentage > 0:
                allocation[category] = percentage
                allocation_total += percentage

                # Afficher une barre de progression colorée pour cette catégorie
                st.markdown(f"""
                <div style="display:flex;align-items:center;margin-bottom:8px;">
                    <div style="width:80px;">{category.capitalize()}</div>
                    <div style="background:#f8f9fa;height:8px;width:70%;margin:0 10px;">
                        <div style="background:{category_colors[category]};height:8px;width:{percentage}%;"></div>
                    </div>
                    <div>{percentage}%</div>
                </div>
                """, unsafe_allow_html=True)

    # Barre de progression pour visualiser le total
    st.markdown(f"""
    <div style="margin-top:20px;">
        <h4 style="margin-bottom:5px;">Total: {allocation_total}%</h4>
        <div style="background:#f8f9fa;height:10px;width:100%;border-radius:5px;">
            <div style="background:{('#28a745' if allocation_total == 100 else '#ffc107' if allocation_total < 100 else '#dc3545')};height:10px;width:{min(allocation_total, 100)}%;border-radius:5px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Message de validation
    if allocation_total < 100:
        st.warning(f"Le total des allocations doit être de 100%. Actuellement: {allocation_total}%")
    elif allocation_total > 100:
        st.error(f"Le total des allocations ne doit pas dépasser 100%. Actuellement: {allocation_total}%")
    else:
        st.success("Allocation valide (100%)")

    return allocation


def edit_allocation_form(asset, asset_id: str) -> Tuple[Dict[str, float], bool]:
    """
    Crée un formulaire pour l'édition de l'allocation par catégorie d'un actif existant

    Args:
        asset: Actif à éditer
        asset_id: ID de l'actif

    Returns:
        Tuple (dictionnaire des allocations {catégorie: pourcentage}, validité de l'allocation)
    """
    st.subheader("Allocation par catégorie")
    st.info("Répartissez la valeur de l'actif entre les différentes catégories (total 100%)")

    # Créer un conteneur pour les sliders d'allocation
    allocation_col1, allocation_col2 = st.columns(2)

    # Variables pour stocker les nouvelles allocations
    new_allocation = {}
    allocation_total = 0

    # Définition des couleurs par catégorie
    category_colors = {
        "actions": "#4e79a7",
        "obligations": "#f28e2c",
        "immobilier": "#e15759",
        "crypto": "#76b7b2",
        "metaux": "#59a14f",
        "cash": "#edc949",
        "autre": "#af7aa1"
    }

    # Première colonne: principaux types d'actifs
    with allocation_col1:
        for category in ["actions", "obligations", "immobilier", "cash"]:
            percentage = st.slider(
                f"{category.capitalize()} (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(asset.allocation.get(category, 0.0)),
                step=1.0,
                key=f"edit_asset_alloc_{asset_id}_{category}"
            )
            if percentage > 0:
                new_allocation[category] = percentage
                allocation_total += percentage

                # Afficher une barre de progression colorée
                st.markdown(f"""
                <div style="display:flex;align-items:center;margin-bottom:8px;">
                    <div style="width:80px;">{category.capitalize()}</div>
                    <div style="background:#f8f9fa;height:8px;width:70%;margin:0 10px;">
                        <div style="background:{category_colors[category]};height:8px;width:{percentage}%;"></div>
                    </div>
                    <div>{percentage}%</div>
                </div>
                """, unsafe_allow_html=True)

    # Deuxième colonne: autres types d'actifs
    with allocation_col2:
        for category in ["crypto", "metaux", "autre"]:
            percentage = st.slider(
                f"{category.capitalize()} (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(asset.allocation.get(category, 0.0)),
                step=1.0,
                key=f"edit_asset_alloc_{asset_id}_{category}"
            )
            if percentage > 0:
                new_allocation[category] = percentage
                allocation_total += percentage

                # Afficher une barre de progression colorée
                st.markdown(f"""
                <div style="display:flex;align-items:center;margin-bottom:8px;">
                    <div style="width:80px;">{category.capitalize()}</div>
                    <div style="background:#f8f9fa;height:8px;width:70%;margin:0 10px;">
                        <div style="background:{category_colors[category]};height:8px;width:{percentage}%;"></div>
                    </div>
                    <div>{percentage}%</div>
                </div>
                """, unsafe_allow_html=True)

    # Barre de progression pour le total
    st.markdown(f"""
    <div style="margin-top:20px;">
        <h4 style="margin-bottom:5px;">Total: {allocation_total}%</h4>
        <div style="background:#f8f9fa;height:10px;width:100%;border-radius:5px;">
            <div style="background:{('#28a745' if allocation_total == 100 else '#ffc107' if allocation_total < 100 else '#dc3545')};height:10px;width:{min(allocation_total, 100)}%;border-radius:5px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    allocation_valid = allocation_total == 100

    if not allocation_valid:
        st.warning(f"Le total des allocations doit être de 100%. Actuellement: {allocation_total}%")
    else:
        st.success("Allocation valide (100%)")

    return new_allocation, allocation_valid


def create_geo_allocation_form(
        allocation: Dict[str, float],
        prefix: str,
        existing_geo_allocation: Dict[str, Dict[str, float]] = None
) -> Tuple[Dict[str, Dict[str, float]], bool]:
    """
    Crée un formulaire pour la répartition géographique par catégorie

    Args:
        allocation: Dictionnaire d'allocation par catégorie
        prefix: Préfixe pour les clés de session state
        existing_geo_allocation: Répartition géographique existante (optionnel)

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
                                value=get_existing_geo_value(prefix, category, zone, current_geo, default_geo),
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
                        value=get_existing_geo_value(prefix, category, zone, current_geo, default_geo),
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

            # Visualisation du total
            progress_color = "#28a745" if geo_total == 100 else "#ffc107" if geo_total < 100 else "#dc3545"

            st.markdown(f"""
            <div style="margin-top:20px;">
                <h4 style="margin-bottom:5px;">Total: {geo_total}%</h4>
                <div style="background:#f8f9fa;height:10px;width:100%;border-radius:5px;">
                    <div style="background:{progress_color};height:10px;width:{min(geo_total, 100)}%;border-radius:5px;"></div>
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


def get_existing_value(prefix: str, category: str, existing_allocation: Dict[str, float] = None) -> float:
    """
    Récupère la valeur d'allocation existante si disponible

    Args:
        prefix: Préfixe pour les clés de session state
        category: Catégorie d'actif
        existing_allocation: Allocation existante (optionnel)

    Returns:
        Valeur existante ou 0.0
    """
    # D'abord essayer de récupérer depuis session_state
    key = f"{prefix}_alloc_{category}"
    if key in st.session_state:
        return st.session_state[key]

    # Ensuite essayer depuis l'allocation existante
    if existing_allocation and category in existing_allocation:
        return float(existing_allocation[category])

    return 0.0


def get_existing_geo_value(
        prefix: str,
        category: str,
        zone: str,
        current_geo: Dict[str, float],
        default_geo: Dict[str, float]
) -> float:
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