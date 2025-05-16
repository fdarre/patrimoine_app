# ui/assets/allocation_form.py
"""
Module pour la gestion des formulaires d'allocation par catégorie
"""
import streamlit as st
from typing import Dict, Tuple

def create_allocation_form(prefix: str) -> Dict[str, float]:
    """
    Crée un formulaire pour l'allocation par catégorie
    
    Args:
        prefix: Préfixe pour les clés de session state (ex: "new_asset" ou "edit_asset_123")
        
    Returns:
        Dictionnaire des allocations {catégorie: pourcentage}
    """
    st.subheader("Allocation par catégorie")
    st.info("Répartissez la valeur de l'actif entre les différentes catégories (total 100%)")

    # Variables pour stocker les allocations
    allocation = {}
    allocation_total = 0

    # Interface améliorée pour l'allocation avec barres de progression
    col1, col2 = st.columns(2)

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
    with col1:
        for category in ["actions", "obligations", "immobilier", "cash"]:
            percentage = st.slider(
                f"{category.capitalize()} (%)",
                min_value=0.0,
                max_value=100.0,
                value=get_existing_allocation(prefix, category),
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
                value=get_existing_allocation(prefix, category),
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

    # Vérifier que le total est de 100%
    st.progress(allocation_total / 100)
    
    allocation_valid = allocation_total == 100
    
    if not allocation_valid:
        st.warning(f"Le total des allocations doit être de 100%. Actuellement: {allocation_total}%")
    else:
        st.success("Allocation valide (100%)")
        
    return new_allocation, allocation_valid

def get_existing_allocation(prefix: str, category: str) -> float:
    """
    Récupère la valeur d'allocation existante si disponible dans la session
    
    Args:
        prefix: Préfixe pour les clés de session state
        category: Catégorie d'actif
        
    Returns:
        Valeur existante ou 0.0
    """
    key = f"{prefix}_alloc_{category}"
    if key in st.session_state:
        return st.session_state[key]
    return 0.0
