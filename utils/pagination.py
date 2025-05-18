"""
Utilitaire de pagination pour les tableaux de données
"""
from typing import List, Optional, Dict, Any, Tuple
import streamlit as st
import pandas as pd
import math
from sqlalchemy.orm import Query

def paginate_query(
    query: Query,
    page_size: int = 10,
    page_key: str = "pagination_page"
) -> Tuple[List[Any], int, int]:
    """
    Implémente la pagination côté SQL pour une requête SQLAlchemy

    Args:
        query: Requête SQLAlchemy à paginer
        page_size: Nombre d'éléments par page
        page_key: Clé pour la session_state de Streamlit

    Returns:
        Tuple (résultats paginés, nombre de pages, page courante)
    """
    # Calculer le nombre total d'éléments (requête distincte avec count)
    total_count = query.count()
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    # Initialiser la page courante dans session_state si nécessaire
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    # S'assurer que la page courante est valide
    current_page = st.session_state[page_key]
    if current_page > total_pages:
        current_page = total_pages
        st.session_state[page_key] = current_page

    # Calculer l'offset pour la requête SQL
    offset = (current_page - 1) * page_size

    # Appliquer la pagination à la requête SQLAlchemy
    paginated_results = query.limit(page_size).offset(offset).all()

    return paginated_results, total_pages, current_page

def paginate_dataframe(
    df: pd.DataFrame,
    page_size: int = 10,
    page_key: str = "pagination_page"
) -> Tuple[pd.DataFrame, int, int]:
    """
    Implémente la pagination d'un DataFrame

    Args:
        df: DataFrame à paginer
        page_size: Nombre d'éléments par page
        page_key: Clé pour la session_state de Streamlit

    Returns:
        Tuple (DataFrame paginé, nombre de pages, page courante)
    """
    # Calculer le nombre total de pages
    total_rows = len(df)
    total_pages = math.ceil(total_rows / page_size) if total_rows > 0 else 1

    # Initialiser la page courante dans session_state si nécessaire
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    # S'assurer que la page courante est valide
    current_page = st.session_state[page_key]
    if current_page > total_pages:
        current_page = total_pages
        st.session_state[page_key] = current_page

    # Calculer les indices de début et de fin
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)

    # Extraire la page courante
    df_paginated = df.iloc[start_idx:end_idx].copy() if not df.empty else df.copy()

    return df_paginated, total_pages, current_page

def render_pagination_controls(
    total_pages: int,
    page_key: str = "pagination_page",
    max_visible_pages: int = 5
) -> None:
    """
    Affiche les contrôles de pagination

    Args:
        total_pages: Nombre total de pages
        page_key: Clé pour la session_state de Streamlit
        max_visible_pages: Nombre maximum de boutons de page à afficher
    """
    if total_pages <= 1:
        return

    current_page = st.session_state[page_key]

    # Fonction de callback pour changer de page
    def change_page(page_num):
        st.session_state[page_key] = page_num

    # Interface de pagination améliorée
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button("◀ Précédent", key=f"{page_key}_prev", disabled=current_page <= 1):
            st.session_state[page_key] = current_page - 1
            st.rerun()

    with col2:
        st.write(f"Page {current_page} sur {total_pages}")

    with col3:
        if st.button("Suivant ▶", key=f"{page_key}_next", disabled=current_page >= total_pages):
            st.session_state[page_key] = current_page + 1
            st.rerun()

def paginated_table(df: pd.DataFrame, page_size: int = 10, key_prefix: str = "table",
                    with_search: bool = False, with_filters: Dict[str, List[str]] = None):
    """
    Composant de tableau avec pagination, recherche et filtres

    Args:
        df: DataFrame à afficher
        page_size: Nombre d'éléments par page
        key_prefix: Préfixe pour les clés de session
        with_search: Activer la recherche globale
        with_filters: Dictionnaire {colonne: liste de valeurs possibles} pour les filtres

    Returns:
        DataFrame filtré et paginé
    """
    # Ajout du champ de recherche
    if with_search:
        search_term = st.text_input("🔍 Rechercher", key=f"{key_prefix}_search")
        if search_term:
            mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            df = df[mask]

    # Ajout des filtres par colonne
    if with_filters:
        for col, values in with_filters.items():
            if col in df.columns and values:
                # Ajouter l'option "Tous"
                filter_options = ["Tous"] + values
                selected = st.selectbox(f"Filtrer par {col}", filter_options, key=f"{key_prefix}_filter_{col}")

                if selected != "Tous":
                    df = df[df[col] == selected]

    # Paginer le DataFrame filtré
    df_paginated, total_pages, current_page = paginate_dataframe(df, page_size, f"{key_prefix}_page")

    # Afficher le message de pagination
    start_idx = (current_page - 1) * page_size + 1 if len(df) > 0 else 0
    end_idx = min(current_page * page_size, len(df))
    st.write(f"Affichage de {start_idx}-{end_idx} sur {len(df)} éléments")

    # Afficher le tableau
    st.dataframe(df_paginated, use_container_width=True)

    # Afficher les contrôles de pagination
    render_pagination_controls(total_pages, f"{key_prefix}_page")

    return df_paginated