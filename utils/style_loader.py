"""
Utilitaire pour charger les styles CSS et améliorer l'expérience utilisateur
"""
import os
import streamlit as st
from typing import Dict, Optional

# Thèmes de couleurs disponibles
THEMES = {
    "dark": {
        "bg_color": "#0f172a",
        "card_bg": "#1e293b",
        "primary": "#6366f1",
        "secondary": "#ec4899",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#0ea5e9",
        "text_light": "#f8fafc",
        "text_muted": "#94a3b8"
    },
    "light": {
        "bg_color": "#f8fafc",
        "card_bg": "#ffffff",
        "primary": "#4f46e5",
        "secondary": "#db2777",
        "success": "#059669",
        "warning": "#d97706",
        "danger": "#dc2626",
        "info": "#0284c7",
        "text_light": "#0f172a",
        "text_muted": "#64748b"
    }
}

# Dictionnaire des classes CSS pour les composants de l'application
CSS_CLASSES = {
    # Cartes et conteneurs
    "card": "card-container",
    "card_title": "card-title",
    "card_body": "card-body",
    "card_footer": "card-footer",

    # Métriques et indicateurs
    "metric": "metric-card",
    "positive": "positive",
    "negative": "negative",

    # Tâches et notifications
    "todo": "todo-card",
    "info": "info-message",
    "warning": "warning-message",
    "success": "success-message",
    "error": "error-message",

    # Tableaux et listes
    "table": "data-table",
    "table_header": "table-header",
    "table_row": "table-row",

    # Badges et étiquettes
    "badge": "badge",
    "badge_primary": "badge-primary",
    "badge_success": "badge-success",
    "badge_warning": "badge-warning",
    "badge_danger": "badge-danger",

    # Boutons
    "btn_primary": "btn-primary",
    "btn_secondary": "btn-secondary",
    "btn_success": "btn-success",
    "btn_danger": "btn-danger",
    "btn_warning": "btn-warning",

    # Navigation
    "nav_item": "nav-item",
    "nav_active": "nav-active",

    # Formulaires
    "form_group": "form-group",
    "form_control": "form-control",
    "form_label": "form-label",
    "form_help": "form-help-text",

    # Autres éléments
    "breadcrumb": "breadcrumb",
    "progress": "progress-bar",
    "infobox": "info-box"
}

# Variable globale pour le thème actuel
CURRENT_THEME = "dark"

def get_theme_color(color_name: str) -> str:
    """
    Récupère une couleur du thème actuel

    Args:
        color_name: Nom de la couleur (primary, secondary, etc.)

    Returns:
        Code hexadécimal de la couleur
    """
    return THEMES[CURRENT_THEME].get(color_name, "#000000")

def set_theme(theme_name: str) -> None:
    """
    Définit le thème courant

    Args:
        theme_name: Nom du thème (dark, light)
    """
    global CURRENT_THEME
    if theme_name in THEMES:
        CURRENT_THEME = theme_name
        # Stocke le thème dans session_state pour persistance
        st.session_state["app_theme"] = theme_name

def get_class(component_type: str) -> str:
    """
    Récupère la classe CSS pour un type de composant donné

    Args:
        component_type: Type de composant (card, metric, etc.)

    Returns:
        Nom de classe CSS ou chaîne vide si non trouvé
    """
    return CSS_CLASSES.get(component_type, "")

def load_css() -> None:
    """
    Charge les styles CSS depuis le fichier principal
    et les injecte dans Streamlit
    """
    # Charger le thème depuis session_state si défini
    if "app_theme" in st.session_state:
        set_theme(st.session_state["app_theme"])

    # Chemin absolu du projet
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Chemin vers le fichier CSS
    css_file = os.path.join(project_root, "static", "styles", "main.css")
    css_variables = os.path.join(project_root, "static", "styles", "variables.css")

    try:
        css = ""

        # Charger les variables CSS
        if os.path.exists(css_variables):
            with open(css_variables, "r") as f:
                css += f.read()

        # Charger le CSS principal
        if os.path.exists(css_file):
            with open(css_file, "r") as f:
                css += f.read()

            # Injecter le CSS
            st.markdown(f"""
            <style>
            {css}
            </style>
            """, unsafe_allow_html=True)
        else:
            # Utiliser le CSS de secours
            from config.app_config import CUSTOM_CSS
            st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    except Exception as e:
        # En cas d'erreur, utiliser le CSS de secours
        from config.app_config import CUSTOM_CSS
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

        # Afficher un message d'erreur en console pour le débogage
        print(f"Erreur lors du chargement du CSS: {str(e)}")

def create_styled_element(element_type: str, content: str,
                         class_type: Optional[str] = None,
                         extra_classes: str = "",
                         inline_style: str = "") -> str:
    """
    Crée un élément HTML avec le style approprié

    Args:
        element_type: Type d'élément HTML (div, span, etc.)
        content: Contenu HTML de l'élément
        class_type: Type de composant pour la classe CSS (card, metric, etc.)
        extra_classes: Classes CSS supplémentaires
        inline_style: Style CSS inline (à éviter si possible)

    Returns:
        Chaîne HTML de l'élément stylisé
    """
    classes = get_class(class_type) if class_type else ""
    if extra_classes:
        classes += f" {extra_classes}"

    style_attr = f' style="{inline_style}"' if inline_style else ''
    class_attr = f' class="{classes}"' if classes else ''

    return f'<{element_type}{class_attr}{style_attr}>{content}</{element_type}>'

def create_card(title: str, content: str, footer: str = "",
               extra_classes: str = "", card_id: str = "") -> str:
    """
    Crée une carte HTML stylisée

    Args:
        title: Titre de la carte
        content: Contenu HTML de la carte
        footer: Pied de page HTML (optionnel)
        extra_classes: Classes CSS supplémentaires
        card_id: ID HTML pour la carte

    Returns:
        Chaîne HTML de la carte
    """
    id_attr = f' id="{card_id}"' if card_id else ''
    title_html = f'<div class="{get_class("card_title")}">{title}</div>' if title else ''
    footer_html = f'<div class="{get_class("card_footer")}">{footer}</div>' if footer else ''

    return f"""
    <div class="{get_class("card")} {extra_classes}"{id_attr}>
        {title_html}
        <div class="{get_class("card_body")}">{content}</div>
        {footer_html}
    </div>
    """

def create_badge(label: str, badge_type: str = "primary") -> str:
    """
    Crée un badge HTML stylisé

    Args:
        label: Texte du badge
        badge_type: Type de badge (primary, success, warning, danger)

    Returns:
        Chaîne HTML du badge
    """
    class_name = get_class(f"badge_{badge_type}")
    return f'<span class="{get_class("badge")} {class_name}">{label}</span>'

def create_button_style(button_type: str = "primary") -> str:
    """
    Génère le CSS pour styliser un bouton Streamlit

    Args:
        button_type: Type de bouton (primary, secondary, success, danger, warning)

    Returns:
        CSS à injecter avec st.markdown
    """
    color = get_theme_color(button_type)
    hover_color = get_theme_color(f"{button_type}_dark") if f"{button_type}_dark" in THEMES[CURRENT_THEME] else color

    return f"""
    <style>
    div.stButton > button {{
        background-color: {color};
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-weight: 500;
        transition: all 0.2s;
    }}
    div.stButton > button:hover {{
        background-color: {hover_color};
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }}
    div.stButton > button:active {{
        transform: translateY(0);
    }}
    </style>
    """

def apply_container_style() -> None:
    """
    Applique un style à tous les conteneurs Streamlit
    """
    st.markdown(f"""
    <style>
    .stApp {{
        background-color: {get_theme_color("bg_color")};
        color: {get_theme_color("text_light")};
    }}
    .block-container {{
        padding: 2rem;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {get_theme_color("text_light")} !important;
    }}
    p, li, div {{
        color: {get_theme_color("text_light")};
    }}
    </style>
    """, unsafe_allow_html=True)

def inject_custom_css(css_code: str) -> None:
    """
    Injecte du code CSS personnalisé dans la page

    Args:
        css_code: Code CSS à injecter
    """
    st.markdown(f"<style>{css_code}</style>", unsafe_allow_html=True)

def create_theme_selector() -> None:
    """
    Crée un sélecteur de thème dans la barre latérale
    """
    with st.sidebar:
        selected_theme = st.selectbox(
            "Thème",
            options=list(THEMES.keys()),
            index=list(THEMES.keys()).index(CURRENT_THEME),
            key="theme_selector"
        )

        if selected_theme != CURRENT_THEME:
            set_theme(selected_theme)
            st.rerun()

def initialize_styles() -> None:
    """
    Initialise tous les styles de l'application
    """
    load_css()
    apply_container_style()