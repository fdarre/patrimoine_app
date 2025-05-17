"""
Composants visuels réutilisables pour l'interface utilisateur
"""
import streamlit as st
from typing import List, Dict, Any, Optional, Union, Tuple, Callable


def metric_card(title: str, value: Union[str, float, int], 
             delta: Optional[Union[str, float, int]] = None,
             delta_color: str = "normal",
             help_text: str = "",
             icon: str = ""):
    """
    Affiche une carte de métrique améliorée
    
    Args:
        title: Titre de la métrique
        value: Valeur principale
        delta: Variation (optionnel)
        delta_color: Couleur de la variation ('normal', 'inverse', 'off')
        help_text: Texte d'aide en infobulle (optionnel)
        icon: Icône à afficher (emoji ou code HTML)
    """
    # Formatage des valeurs numériques
    if isinstance(value, (int, float)):
        formatted_value = f"{value:,.2f}".replace(",", " ")
    else:
        formatted_value = value
        
    # Formatage de la variation
    delta_html = ""
    if delta is not None:
        if isinstance(delta, (int, float)):
            delta_sign = "+" if delta > 0 else ""
            formatted_delta = f"{delta_sign}{delta:,.2f}".replace(",", " ")
        else:
            formatted_delta = delta
            
        # Déterminer la classe CSS pour la couleur
        if delta_color == "inverse":
            delta_class = "negative" if delta > 0 else "positive"
        elif delta_color == "off":
            delta_class = ""
        else:
            delta_class = "positive" if delta > 0 else "negative"
            
        delta_html = f'<div class="{delta_class}">{formatted_delta}</div>'
    
    # Créer l'HTML de la carte
    metric_html = f"""
    <div class="metric-card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <div style="font-size:14px;color:#adb5bd;">{title}</div>
            {f'<div style="font-size:20px;">{icon}</div>' if icon else ''}
        </div>
        <div style="font-size:24px;font-weight:600;margin-bottom:5px;">{formatted_value}</div>
        {delta_html}
    </div>
    """
    
    # Afficher la carte
    st.markdown(metric_html, unsafe_allow_html=True)
    
    # Ajouter une infobulle si nécessaire
    if help_text:
        st.markdown(f"<div style='font-size:12px;color:#adb5bd;'>{help_text}</div>", unsafe_allow_html=True)


def info_card(title: str, content: str, icon: str = "ℹ️", 
           card_type: str = "info", dismissible: bool = False,
           key: Optional[str] = None):
    """
    Affiche une carte d'information
    
    Args:
        title: Titre de la carte
        content: Contenu HTML ou texte
        icon: Icône à afficher
        card_type: Type de carte ('info', 'success', 'warning', 'error')
        dismissible: Si la carte peut être fermée
        key: Clé unique pour l'état de la carte
    """
    # Définir les couleurs en fonction du type
    colors = {
        "info": "#17a2b8",
        "success": "#28a745",
        "warning": "#ffc107",
        "error": "#dc3545"
    }
    color = colors.get(card_type, colors["info"])
    
    # Générer une clé si nécessaire
    if dismissible and not key:
        import hashlib
        key = f"card_{hashlib.md5((title + content).encode()).hexdigest()}"
    
    # Vérifier si la carte a été fermée
    if dismissible and key in st.session_state and st.session_state[key] == False:
        return
    
    # Créer l'HTML de la carte
    card_html = f"""
    <div style="border-left:4px solid {color};padding:15px;background-color:rgba(0,0,0,0.05);margin-bottom:15px;border-radius:4px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div style="display:flex;align-items:center;">
                <div style="font-size:20px;margin-right:10px;">{icon}</div>
                <div>
                    <div style="font-weight:bold;margin-bottom:5px;">{title}</div>
                    <div>{content}</div>
                </div>
            </div>
            {f'<div style="cursor:pointer;" onclick="this.parentElement.parentElement.style.display=\'none\';">✕</div>' if dismissible else ''}
        </div>
    </div>
    """
    
    # Afficher la carte
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Gérer l'état de la carte si dismissible
    if dismissible and key:
        if key not in st.session_state:
            st.session_state[key] = True


def action_button(label: str, icon: str = "", 
               button_type: str = "primary",
               on_click: Optional[Callable] = None,
               args: Tuple = (), 
               disabled: bool = False,
               help_text: str = "",
               key: Optional[str] = None,
               use_container_width: bool = False):
    """
    Crée un bouton d'action stylisé
    
    Args:
        label: Texte du bouton
        icon: Icône (emoji ou code HTML)
        button_type: Type du bouton ('primary', 'success', 'warning', 'danger', 'outline')
        on_click: Fonction à appeler lors du clic
        args: Arguments à passer à la fonction on_click
        disabled: Si le bouton est désactivé
        help_text: Texte d'aide en infobulle
        key: Clé unique pour le bouton
        use_container_width: Utiliser toute la largeur du conteneur
    """
    # Générer une clé si nécessaire
    if not key:
        import hashlib
        key = f"btn_{hashlib.md5(label.encode()).hexdigest()}"
    
    # Préparer le label avec l'icône
    button_label = f"{icon} {label}" if icon else label
    
    # Créer le bouton
    clicked = st.button(
        button_label,
        key=key,
        disabled=disabled,
        help=help_text,
        on_click=on_click,
        args=args,
        use_container_width=use_container_width
    )
    
    # Appliquer le style CSS en fonction du type
    button_classes = {
        "primary": "btn-primary",
        "success": "btn-success",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "outline": "btn-outline"
    }
    button_class = button_classes.get(button_type, "btn-primary")
    
    # Injecter le CSS pour ce bouton spécifique
    st.markdown(f"""
    <style>
    div[data-testid="stButton"] > button[kind="{key}"] {{
        background-color: var(--primary-color);
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    return clicked


def card_container(content_func: Callable, 
                title: str = "", 
                footer: str = "",
                collapsible: bool = False,
                collapsed: bool = False,
                key: Optional[str] = None):
    """
    Crée un conteneur de type carte pour encapsuler du contenu
    
    Args:
        content_func: Fonction qui génère le contenu
        title: Titre de la carte
        footer: Pied de page de la carte
        collapsible: Si la carte peut être réduite/agrandie
        collapsed: État initial si collapsible
        key: Clé unique pour la carte
    """
    # Générer une clé si nécessaire
    if not key:
        import hashlib
        key = f"card_{hashlib.md5(title.encode()).hexdigest()}"
    
    # Gérer l'état replié/déplié
    if collapsible:
        if f"{key}_collapsed" not in st.session_state:
            st.session_state[f"{key}_collapsed"] = collapsed
            
        # Créer l'en-tête avec le toggle
        col1, col2 = st.columns([10, 1])
        with col1:
            st.markdown(f"### {title}" if title else "")
        with col2:
            if st.button("▼" if st.session_state[f"{key}_collapsed"] else "▲", key=f"{key}_toggle"):
                st.session_state[f"{key}_collapsed"] = not st.session_state[f"{key}_collapsed"]
        
        # Afficher le contenu si non replié
        if not st.session_state[f"{key}_collapsed"]:
            with st.container():
                content_func()
                
            # Afficher le footer si présent
            if footer:
                st.markdown(f"""
                <div style="border-top: 1px solid #ddd; padding-top: 10px; font-size: 12px; color: #adb5bd;">
                    {footer}
                </div>
                """, unsafe_allow_html=True)
    else:
        # Version non-collapsible
        if title:
            st.markdown(f"### {title}")
            
        content_func()
            
        if footer:
            st.markdown(f"""
            <div style="border-top: 1px solid #ddd; padding-top: 10px; font-size: 12px; color: #adb5bd;">
                {footer}
            </div>
            """, unsafe_allow_html=True)


def data_table(data: Union[List[Dict], Dict[str, List], List[List]], 
            columns: Optional[List[str]] = None,
            key: Optional[str] = None,
            pagination: bool = False,
            page_size: int = 10,
            searchable: bool = False,
            sortable: bool = False,
            with_index: bool = False):
    """
    Affiche un tableau de données amélioré
    
    Args:
        data: Données à afficher (liste de dict, dict de listes, liste de listes)
        columns: Noms des colonnes (optionnel)
        key: Clé unique pour le tableau
        pagination: Activer la pagination
        page_size: Nombre d'éléments par page
        searchable: Activer la recherche
        sortable: Activer le tri
        with_index: Afficher l'index
    """
    import pandas as pd
    from utils.pagination import paginate_dataframe, render_pagination_controls
    
    # Convertir les données en DataFrame
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        # Liste de dictionnaires
        df = pd.DataFrame(data)
    elif isinstance(data, dict):
        # Dictionnaire de listes
        df = pd.DataFrame(data)
    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
        # Liste de listes
        df = pd.DataFrame(data, columns=columns)
    else:
        # Cas par défaut, essayer de convertir directement
        df = pd.DataFrame(data)
    
    # Générer une clé si nécessaire
    if not key:
        import hashlib
        key = f"table_{hashlib.md5(str(df.shape).encode()).hexdigest()}"
    
    # Ajouter une barre de recherche si nécessaire
    if searchable:
        search_term = st.text_input("🔍 Rechercher", key=f"{key}_search")
        if search_term:
            # Recherche dans toutes les colonnes
            filtered_df = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            df = df[filtered_df]
    
    # Ajouter des options de tri si nécessaire
    if sortable and not df.empty:
        sort_cols = st.columns([3, 2, 1])
        with sort_cols[0]:
            sort_column = st.selectbox(
                "Trier par",
                options=df.columns.tolist(),
                key=f"{key}_sort_col"
            )
        with sort_cols[1]:
            sort_order = st.radio(
                "Ordre",
                options=["Ascendant", "Descendant"],
                horizontal=True,
                key=f"{key}_sort_order"
            )
        
        # Appliquer le tri
        ascending = sort_order == "Ascendant"
        df = df.sort_values(by=sort_column, ascending=ascending)
    
    # Appliquer la pagination si nécessaire
    if pagination:
        df_paginated, total_pages, current_page = paginate_dataframe(
            df, page_size=page_size, page_key=f"{key}_page"
        )
        
        # Afficher le tableau
        st.dataframe(df_paginated, use_container_width=True, hide_index=not with_index)
        
        # Afficher les contrôles de pagination
        render_pagination_controls(total_pages, f"{key}_page")
    else:
        # Afficher le tableau sans pagination
        st.dataframe(df, use_container_width=True, hide_index=not with_index)