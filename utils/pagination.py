"""
Utilitaire de pagination centralisé pour les tableaux de données et autres collections
"""
import math
from typing import List, Optional, Dict, Tuple, TypeVar, Generic

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Query

T = TypeVar('T')

class PaginationManager(Generic[T]):
    """
    Gestionnaire de pagination réutilisable pour différents types de données

    Cette classe centralise la logique de pagination pour les DataFrame,
    les requêtes SQLAlchemy et les listes standard.
    """

    def __init__(
        self,
        key_prefix: str,
        page_size: int = 10,
        max_visible_pages: int = 5
    ):
        """
        Initialise un gestionnaire de pagination

        Args:
            key_prefix: Préfixe pour les clés de session state
            page_size: Nombre d'éléments par page par défaut
            max_visible_pages: Nombre maximum de boutons de page à afficher
        """
        self.key_prefix = key_prefix
        self.page_size = page_size
        self.max_visible_pages = max_visible_pages
        self.page_key = f"{key_prefix}_page"

        # Initialiser la page courante dans session_state si nécessaire
        if self.page_key not in st.session_state:
            st.session_state[self.page_key] = 1

    def paginate_query(self, query: Query) -> Tuple[List[T], int, int]:
        """
        Pagine une requête SQLAlchemy

        Args:
            query: Requête SQLAlchemy à paginer

        Returns:
            Tuple (résultats paginés, nombre de pages, page courante)
        """
        # Calculer le nombre total d'éléments
        total_count = query.count()
        total_pages = max(1, math.ceil(total_count / self.page_size))

        # S'assurer que la page courante est valide
        current_page = min(max(1, st.session_state[self.page_key]), total_pages)
        st.session_state[self.page_key] = current_page

        # Calculer l'offset pour la requête SQL
        offset = (current_page - 1) * self.page_size

        # Appliquer la pagination à la requête SQLAlchemy
        paginated_results = query.limit(self.page_size).offset(offset).all()

        return paginated_results, total_pages, current_page

    def paginate_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
        """
        Pagine un DataFrame Pandas

        Args:
            df: DataFrame à paginer

        Returns:
            Tuple (DataFrame paginé, nombre de pages, page courante)
        """
        # Calculer le nombre total de pages
        total_rows = len(df)
        total_pages = max(1, math.ceil(total_rows / self.page_size))

        # S'assurer que la page courante est valide
        current_page = min(max(1, st.session_state[self.page_key]), total_pages)
        st.session_state[self.page_key] = current_page

        # Calculer les indices de début et de fin
        start_idx = (current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_rows)

        # Extraire la page courante
        df_paginated = df.iloc[start_idx:end_idx].copy() if not df.empty else df.copy()

        return df_paginated, total_pages, current_page

    def paginate_list(self, items: List[T]) -> Tuple[List[T], int, int]:
        """
        Pagine une liste standard

        Args:
            items: Liste d'éléments à paginer

        Returns:
            Tuple (liste paginée, nombre de pages, page courante)
        """
        # Calculer le nombre total de pages
        total_items = len(items)
        total_pages = max(1, math.ceil(total_items / self.page_size))

        # S'assurer que la page courante est valide
        current_page = min(max(1, st.session_state[self.page_key]), total_pages)
        st.session_state[self.page_key] = current_page

        # Calculer les indices de début et de fin
        start_idx = (current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_items)

        # Extraire la page courante
        paginated_items = items[start_idx:end_idx]

        return paginated_items, total_pages, current_page

    def render_controls(self, total_pages: int, current_page: int) -> None:
        """
        Affiche les contrôles de pagination standard

        Args:
            total_pages: Nombre total de pages
            current_page: Page courante (1-indexed)
        """
        if total_pages <= 1:
            return

        # Afficher le message de pagination
        start_idx = (current_page - 1) * self.page_size + 1
        end_idx = min(current_page * self.page_size, 0)  # Sera mise à jour par l'appelant

        # UI des contrôles de pagination
        cols = st.columns([1, 3, 1])

        with cols[0]:
            if st.button(
                "◀ Précédent",
                key=f"{self.key_prefix}_prev",
                disabled=current_page <= 1,
                on_click=self._goto_page,
                args=(max(1, current_page - 1),)
            ):
                pass  # L'action est dans le on_click

        with cols[1]:
            st.write(f"Page {current_page} sur {total_pages}")

        with cols[2]:
            if st.button(
                "Suivant ▶",
                key=f"{self.key_prefix}_next",
                disabled=current_page >= total_pages,
                on_click=self._goto_page,
                args=(min(total_pages, current_page + 1),)
            ):
                pass  # L'action est dans le on_click

    def _goto_page(self, page_num: int) -> None:
        """
        Change la page courante et force un rechargement

        Args:
            page_num: Numéro de la page cible
        """
        st.session_state[self.page_key] = page_num
        st.rerun()


def create_paginated_table(
    df: pd.DataFrame,
    page_size: int = 10,
    key_prefix: str = "table",
    with_search: bool = False,
    with_filters: Optional[Dict[str, List[str]]] = None
) -> pd.DataFrame:
    """
    Fonction utilitaire pour créer un tableau paginé avec recherche et filtres

    Args:
        df: DataFrame à afficher
        page_size: Nombre d'éléments par page
        key_prefix: Préfixe pour les clés de session
        with_search: Activer la recherche globale
        with_filters: Dictionnaire {colonne: liste de valeurs possibles} pour les filtres

    Returns:
        DataFrame filtré et paginé
    """
    # Créer un gestionnaire de pagination
    paginator = PaginationManager(key_prefix=key_prefix, page_size=page_size)

    # Ajouter la recherche si demandé
    if with_search:
        search_term = st.text_input("🔍 Rechercher", key=f"{key_prefix}_search")
        if search_term:
            # Appliquer la recherche sur toutes les colonnes
            mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            df = df[mask]

    # Ajouter les filtres par colonne si spécifiés
    if with_filters:
        for col, values in with_filters.items():
            if col in df.columns and values:
                # Ajouter l'option "Tous"
                filter_options = ["Tous"] + values
                selected = st.selectbox(
                    f"Filtrer par {col}",
                    filter_options,
                    key=f"{key_prefix}_filter_{col}"
                )

                if selected != "Tous":
                    df = df[df[col] == selected]

    # Paginer le DataFrame
    df_paginated, total_pages, current_page = paginator.paginate_dataframe(df)

    # Afficher le message de pagination
    start_idx = (current_page - 1) * page_size + 1 if len(df) > 0 else 0
    end_idx = min(current_page * page_size, len(df))
    st.write(f"Affichage de {start_idx}-{end_idx} sur {len(df)} éléments")

    # Afficher le tableau
    st.dataframe(df_paginated, use_container_width=True)

    # Afficher les contrôles de pagination
    paginator.render_controls(total_pages, current_page)

    return df_paginated