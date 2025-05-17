# ui/components/pagination.py
import streamlit as st
import pandas as pd
import math


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

    # Nombre total d'éléments et de pages
    total_items = len(df)
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    # Récupérer ou initialiser la page actuelle
    page_key = f"{key_prefix}_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    current_page = st.session_state[page_key]

    # Calculer les indices de début et de fin
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)

    # Extraire la page courante
    df_page = df.iloc[start_idx:end_idx] if not df.empty else df

    # Afficher le message de pagination
    st.write(f"Affichage de {start_idx + 1 if total_items > 0 else 0}-{end_idx} sur {total_items} éléments")

    # Afficher le tableau
    st.dataframe(df_page, use_container_width=True)

    # Afficher les contrôles de pagination
    if total_pages > 1:
        cols = st.columns([1, 3, 1])

        with cols[0]:
            if st.button("⏮️", disabled=current_page <= 1, key=f"{key_prefix}_prev"):
                st.session_state[page_key] = max(1, current_page - 1)
                st.rerun()

        with cols[1]:
            st.write(f"Page {current_page} sur {total_pages}")

        with cols[2]:
            if st.button("⏭️", disabled=current_page >= total_pages, key=f"{key_prefix}_next"):
                st.session_state[page_key] = min(total_pages, current_page + 1)
                st.rerun()

    return df_page