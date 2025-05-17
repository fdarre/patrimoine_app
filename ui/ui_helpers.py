"""
Helpers pour l'interface utilisateur Streamlit
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional, Callable, Tuple
import math

from utils.logger import get_logger

logger = get_logger(__name__)


def show_message(message: str, type: str = "info", auto_dismiss: bool = False, key: Optional[str] = None):
    """
    Affiche un message temporaire dans l'interface

    Args:
        message: Message à afficher
        type: Type de message ('info', 'success', 'warning', 'error')
        auto_dismiss: Si le message doit disparaître automatiquement
        key: Clé unique pour le composant
    """
    # Générer une clé si non fournie
    if key is None:
        import hashlib
        key = f"msg_{hashlib.md5(message.encode()).hexdigest()[:8]}"

    # Placeholder pour le message
    placeholder = st.empty()

    # Afficher le message selon le type
    if type == "success":
        placeholder.success(message, icon="✅")
    elif type == "warning":
        placeholder.warning(message, icon="⚠️")
    elif type == "error":
        placeholder.error(message, icon="❌")
    else:
        placeholder.info(message, icon="ℹ️")

    # Auto-dismiss après 3 secondes
    if auto_dismiss:
        import time
        import threading

        def dismiss():
            time.sleep(3)
            placeholder.empty()

        threading.Thread(target=dismiss, daemon=True).start()

    return placeholder


def confirmation_dialog(title: str, message: str, confirm_label: str = "Confirmer",
                        cancel_label: str = "Annuler", key: Optional[str] = None) -> bool:
    """
    Affiche une boîte de dialogue de confirmation

    Args:
        title: Titre de la boîte de dialogue
        message: Message à afficher
        confirm_label: Texte du bouton de confirmation
        cancel_label: Texte du bouton d'annulation
        key: Clé unique pour le composant

    Returns:
        True si confirmé, False sinon
    """
    # Générer une clé si non fournie
    if key is None:
        import hashlib
        key = f"dialog_{hashlib.md5(title.encode()).hexdigest()[:8]}"

    # Afficher la boîte de dialogue
    with st.expander(title, expanded=True):
        st.markdown(message)

        col1, col2 = st.columns(2)
        with col1:
            confirm = st.button(confirm_label, key=f"{key}_confirm")
        with col2:
            cancel = st.button(cancel_label, key=f"{key}_cancel")

        if cancel:
            return False
        return confirm


def paginate_dataframe(df: pd.DataFrame, page_size: int = 10, page_key: str = "pagination") -> Tuple[
    pd.DataFrame, int, int]:
    """
    Pagine un DataFrame

    Args:
        df: DataFrame à paginer
        page_size: Nombre d'éléments par page
        page_key: Clé pour la pagination dans st.session_state

    Returns:
        Tuple (DataFrame paginé, nombre de pages, page courante)
    """
    # Calculer le nombre total de pages
    n_items = len(df)
    n_pages = math.ceil(n_items / page_size) if n_items > 0 else 1

    # Initialiser l'index de page dans session_state si nécessaire
    if page_key not in st.session_state:
        st.session_state[page_key] = 0

    # Calculer les indices de début et fin
    start_idx = st.session_state[page_key] * page_size
    end_idx = min(start_idx + page_size, n_items)

    # Créer le DataFrame paginé
    df_page = df.iloc[start_idx:end_idx].copy() if not df.empty else df.copy()

    return df_page, n_pages, st.session_state[page_key] + 1


def render_pagination_controls(n_pages: int, current_page: int, page_key: str = "pagination"):
    """
    Affiche les contrôles de pagination

    Args:
        n_pages: Nombre total de pages
        current_page: Page courante (1-indexed)
        page_key: Clé pour la pagination dans st.session_state
    """
    if n_pages <= 1:
        return

    cols = st.columns([1, 3, 1])

    with cols[0]:
        if st.button("⏮️ Précédent", key=f"{page_key}_prev",
                     disabled=current_page <= 1):
            st.session_state[page_key] = max(0, st.session_state[page_key] - 1)
            st.rerun()

    with cols[1]:
        st.write(f"Page {current_page} sur {n_pages}")

    with cols[2]:
        if st.button("Suivant ⏭️", key=f"{page_key}_next",
                     disabled=current_page >= n_pages):
            st.session_state[page_key] = min(n_pages - 1, st.session_state[page_key] + 1)
            st.rerun()


def dynamic_filter(df: pd.DataFrame, column: str, label: str, default: str = "Tous",
                   key: Optional[str] = None, format_func: Optional[Callable] = None):
    """
    Crée un filtre dynamique pour un DataFrame

    Args:
        df: DataFrame à filtrer
        column: Colonne à filtrer
        label: Label du filtre
        default: Valeur par défaut ("Tous" pour aucun filtre)
        key: Clé unique pour le composant
        format_func: Fonction pour formater les valeurs affichées

    Returns:
        Filtre sélectionné
    """
    # Générer les options à partir du DataFrame
    unique_values = df[column].dropna().unique().tolist()
    options = [default] + sorted(unique_values)

    # Sélecteur pour le filtre
    selected = st.selectbox(
        label,
        options=options,
        format_func=format_func if format_func else lambda x: x,
        key=key
    )

    return selected


def searchable_selectbox(label: str, options: List[Any], default_index: int = 0,
                         key: Optional[str] = None, format_func: Optional[Callable] = None):
    """
    Sélecteur avec recherche

    Args:
        label: Label du sélecteur
        options: Liste d'options
        default_index: Index de l'option par défaut
        key: Clé unique pour le composant
        format_func: Fonction pour formater les valeurs affichées

    Returns:
        Option sélectionnée
    """
    # Générer une clé si non fournie
    if key is None:
        import hashlib
        key = f"select_{hashlib.md5(label.encode()).hexdigest()[:8]}"

    # Texte de recherche
    search_key = f"{key}_search"
    search = st.text_input(f"Rechercher dans {label}", key=search_key)

    # Filtrer les options selon la recherche
    if search:
        # Appliquer la fonction de formatage pour la recherche si fournie
        if format_func:
            filtered_options = [opt for opt in options
                                if search.lower() in format_func(opt).lower()]
        else:
            filtered_options = [opt for opt in options
                                if search.lower() in str(opt).lower()]
    else:
        filtered_options = options

    # Afficher le sélecteur filtré
    if filtered_options:
        index = min(default_index, len(filtered_options) - 1) if filtered_options else 0
        return st.selectbox(
            label,
            options=filtered_options,
            index=index,
            format_func=format_func if format_func else lambda x: x,
            key=key
        )
    else:
        st.info(f"Aucun résultat pour '{search}'")
        return None


def custom_metric(label: str, value: Any, delta: Optional[Any] = None,
                  help: Optional[str] = None, color: Optional[str] = None):
    """
    Affiche une métrique personnalisée

    Args:
        label: Label de la métrique
        value: Valeur principale
        delta: Variation (optionnel)
        help: Texte d'aide (optionnel)
        color: Couleur de la valeur (optionnel)
    """
    # Style pour la valeur
    value_style = f'color: {color};' if color else ''

    # Calculer la classe pour le delta
    if delta is not None:
        try:
            delta_float = float(delta)
            delta_class = "positive" if delta_float >= 0 else "negative"
            delta_sign = "+" if delta_float > 0 else ""
            delta_display = f'<div class="{delta_class}">{delta_sign}{delta}</div>'
        except (ValueError, TypeError):
            delta_display = f'<div>{delta}</div>'
    else:
        delta_display = ''

    # Afficher la métrique
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 0.8rem; color: #adb5bd;">{label}</div>
        <div style="font-size: 1.5rem; font-weight: bold; {value_style}">{value}</div>
        {delta_display}
    </div>
    """, unsafe_allow_html=True)

    # Afficher l'aide si fournie
    if help:
        st.markdown(f'<div style="font-size: 0.8rem; color: #adb5bd;">{help}</div>',
                    unsafe_allow_html=True)