"""
Utilitaire de pagination pour les tableaux de données
"""
from typing import List, Optional, Dict, Any, Tuple
import streamlit as st
import pandas as pd
import math

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
    
    # Créer la pagination HTML
    pagination_html = '<div class="pagination">'
    
    # Bouton "Précédent"
    prev_disabled = current_page <= 1
    prev_class = "page-item disabled" if prev_disabled else "page-item"
    prev_onclick = "" if prev_disabled else f"Streamlit.setComponentValue('{page_key}', {current_page - 1});"
    pagination_html += f'<div class="{prev_class}"><a class="page-link" href="#" onclick="{prev_onclick}">«</a></div>'
    
    # Calculer les pages à afficher
    if total_pages <= max_visible_pages:
        # Afficher toutes les pages
        pages_to_show = range(1, total_pages + 1)
    else:
        # Afficher une sélection de pages
        start_page = max(1, current_page - (max_visible_pages // 2))
        end_page = min(total_pages, start_page + max_visible_pages - 1)
        
        if end_page - start_page < max_visible_pages - 1:
            start_page = max(1, end_page - (max_visible_pages - 1))
            
        pages_to_show = range(start_page, end_page + 1)
    
    # Bouton pour la première page si nécessaire
    if pages_to_show[0] > 1:
        pagination_html += f'<div class="page-item"><a class="page-link" href="#" onclick="Streamlit.setComponentValue(\'{page_key}\', 1);">1</a></div>'
        if pages_to_show[0] > 2:
            pagination_html += '<div class="page-item disabled"><a class="page-link">...</a></div>'
    
    # Boutons pour les pages à afficher
    for page in pages_to_show:
        page_class = "page-item active" if page == current_page else "page-item"
        page_onclick = "" if page == current_page else f"Streamlit.setComponentValue('{page_key}', {page});"
        pagination_html += f'<div class="{page_class}"><a class="page-link" href="#" onclick="{page_onclick}">{page}</a></div>'
    
    # Bouton pour la dernière page si nécessaire
    if pages_to_show[-1] < total_pages:
        if pages_to_show[-1] < total_pages - 1:
            pagination_html += '<div class="page-item disabled"><a class="page-link">...</a></div>'
        pagination_html += f'<div class="page-item"><a class="page-link" href="#" onclick="Streamlit.setComponentValue(\'{page_key}\', {total_pages});">{total_pages}</a></div>'
    
    # Bouton "Suivant"
    next_disabled = current_page >= total_pages
    next_class = "page-item disabled" if next_disabled else "page-item"
    next_onclick = "" if next_disabled else f"Streamlit.setComponentValue('{page_key}', {current_page + 1});"
    pagination_html += f'<div class="{next_class}"><a class="page-link" href="#" onclick="{next_onclick}">»</a></div>'
    
    pagination_html += '</div>'
    
    # Option alternative plus simple avec des boutons Streamlit
    col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])
    
    with col1:
        if st.button("«", key=f"prev_{page_key}", disabled=prev_disabled):
            change_page(current_page - 1)
    
    with col3:
        st.write(f"Page {current_page} / {total_pages}")
    
    with col5:
        if st.button("»", key=f"next_{page_key}", disabled=next_disabled):
            change_page(current_page + 1)
