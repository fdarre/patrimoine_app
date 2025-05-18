"""
Gestionnaire de thèmes pour l'application
"""
import streamlit as st
import os
from typing import Dict, Any, Optional

# Thèmes disponibles
THEMES = {
    "dark": {
        "bg_color": "#0f172a",
        "card_bg": "#1e293b",
        "sidebar_bg": "#0f172a",
        "text_light": "#f8fafc",
        "text_muted": "#94a3b8",
        "text_dark": "#1e293b",
        "primary_color": "#6366f1",
        "secondary_color": "#ec4899",
        "success_color": "#10b981",
        "warning_color": "#f59e0b",
        "danger_color": "#ef4444",
        "info_color": "#0ea5e9",
    },
    "light": {
        "bg_color": "#f8fafc",
        "card_bg": "#ffffff",
        "sidebar_bg": "#f1f5f9",
        "text_light": "#0f172a",
        "text_muted": "#64748b",
        "text_dark": "#0f172a",
        "primary_color": "#4f46e5",
        "secondary_color": "#db2777",
        "success_color": "#059669",
        "warning_color": "#d97706",
        "danger_color": "#dc2626",
        "info_color": "#0284c7",
    }
}

# Stockage global du thème actif
_ACTIVE_THEME = "dark"


def initialize_theme() -> None:
    """
    Initialise le système de thème
    """
    global _ACTIVE_THEME

    # Initialiser le thème dans session_state si nécessaire
    if "theme" not in st.session_state:
        st.session_state["theme"] = _ACTIVE_THEME
    else:
        _ACTIVE_THEME = st.session_state["theme"]

    # Charger les fichiers CSS de base
    from utils.style_manager import load_css
    load_css("variables.css")
    load_css("main.css")

    # Appliquer le thème actif
    apply_theme(_ACTIVE_THEME)


def apply_theme(theme_name: str) -> None:
    """
    Applique un thème spécifique

    Args:
        theme_name: Nom du thème à appliquer
    """
    global _ACTIVE_THEME

    # Vérifier que le thème existe
    if theme_name not in THEMES:
        theme_name = "dark"  # Thème par défaut

    _ACTIVE_THEME = theme_name
    st.session_state["theme"] = theme_name

    # Construire les variables CSS du thème
    theme = THEMES[theme_name]
    css_vars = ""
    for key, value in theme.items():
        css_vars += f"--{key}: {value};\n"

    # Appliquer les variables CSS
    st.markdown(f"""
    <style>
    :root {{
        {css_vars}
    }}
    </style>
    """, unsafe_allow_html=True)


def create_theme_selector() -> None:
    """
    Crée un sélecteur de thème dans la barre latérale
    """
    theme_options = {
        "dark": "🌙 Sombre",
        "light": "☀️ Clair"
    }

    with st.sidebar:
        selected_theme = st.selectbox(
            "Thème",
            options=list(theme_options.keys()),
            format_func=lambda x: theme_options[x],
            index=0 if _ACTIVE_THEME == "dark" else 1,
            key="theme_selector"
        )

        if selected_theme != _ACTIVE_THEME:
            apply_theme(selected_theme)
            st.rerun()


def get_active_theme() -> str:
    """
    Récupère le nom du thème actif

    Returns:
        Nom du thème actif
    """
    return _ACTIVE_THEME


def get_theme_color(color_name: str) -> str:
    """
    Récupère une couleur du thème actuel

    Args:
        color_name: Nom de la couleur ou raccourci

    Returns:
        Code CSS de la couleur
    """
    # Mappings des raccourcis de couleurs
    color_mappings = {
        "primary": "var(--primary_color)",
        "secondary": "var(--secondary_color)",
        "success": "var(--success_color)",
        "warning": "var(--warning_color)",
        "danger": "var(--danger_color)",
        "info": "var(--info_color)",
        "text_light": "var(--text_light)",
        "text_muted": "var(--text_muted)",
        "text_dark": "var(--text_dark)",
        "bg": "var(--bg_color)",
        "card": "var(--card_bg)"
    }

    # Si le nom est un raccourci, retourner la valeur mappée
    if color_name in color_mappings:
        return color_mappings[color_name]

    # Sinon tenter d'interpréter comme une variable CSS
    if color_name.startswith("--"):
        return f"var({color_name})"
    else:
        return f"var(--{color_name})"