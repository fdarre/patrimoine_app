"""
Utilitaire amélioré pour gérer les styles CSS et les thèmes
"""
import streamlit as st
import os
import json
from typing import Optional, List, Dict

# Chemins des dossiers de styles
STYLES_DIR = os.path.join("static", "styles")
CORE_DIR = os.path.join(STYLES_DIR, "core")
COMPONENTS_DIR = os.path.join(STYLES_DIR, "components")
THEMES_DIR = os.path.join(STYLES_DIR, "themes")

# Thèmes disponibles
THEMES = {
    "dark": {
        "name": "Sombre",
        "icon": "🌙",
        "file": "dark-theme.css",
        "is_default": True
    },
    "light": {
        "name": "Clair",
        "icon": "☀️",
        "file": "light-theme.css",
        "is_default": False
    }
}


def load_css_file(file_path: str) -> Optional[str]:
    """
    Charge un fichier CSS depuis un chemin spécifié

    Args:
        file_path: Chemin complet du fichier CSS

    Returns:
        Contenu du fichier CSS ou None si le fichier n'existe pas
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Fichier CSS introuvable: {file_path}")
        return None
    except Exception as e:
        print(f"Erreur lors du chargement du CSS: {str(e)}")
        return None


def apply_css(css_content: str) -> None:
    """
    Applique un contenu CSS à l'application Streamlit

    Args:
        css_content: Contenu CSS à appliquer
    """
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def load_theme_css(theme_key: str) -> Optional[str]:
    """
    Charge le CSS d'un thème spécifique

    Args:
        theme_key: Clé du thème à charger

    Returns:
        Contenu CSS du thème ou None si le thème n'existe pas
    """
    if theme_key not in THEMES:
        theme_key = next((k for k, v in THEMES.items() if v["is_default"]), "dark")

    theme_file = THEMES[theme_key]["file"]
    theme_path = os.path.join(THEMES_DIR, theme_file)
    return load_css_file(theme_path)


def initialize_styles() -> None:
    """
    Initialise tous les styles de l'application
    """
    # Charger main.css qui importe les autres styles de base
    main_css_path = os.path.join(STYLES_DIR, "main.css")
    main_css = load_css_file(main_css_path)
    if main_css:
        apply_css(main_css)

    # Charger le thème actif
    if "theme" not in st.session_state:
        st.session_state["theme"] = next((k for k, v in THEMES.items() if v["is_default"]), "dark")

    theme_css = load_theme_css(st.session_state["theme"])
    if theme_css:
        apply_css(theme_css)

    # Ajouter une classe au corps pour le thème actif
    apply_css(f"""
    body {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* Appliquer la classe de thème sur le corps */
    body {{
        background-color: var(--bg-color);
        color: var(--text-light);
    }}

    /* Masquer les éléments de débogage et le menu hamburger */
    #MainMenu, footer, .stDeployButton {{
        display: none !important;
    }}
    """)

    # Ajouter un attribut de classe au corps pour le thème actif
    st.markdown(f"""
    <script>
        document.documentElement.className = '{st.session_state["theme"]}-theme';
    </script>
    """, unsafe_allow_html=True)


def create_theme_selector() -> None:
    """
    Crée un sélecteur de thème dans la barre latérale
    """
    with st.sidebar:
        # Créer les options de thème avec icônes
        theme_options = {
            k: f"{v['icon']} {v['name']}" for k, v in THEMES.items()
        }

        selected_theme = st.selectbox(
            "Thème",
            options=list(theme_options.keys()),
            format_func=lambda x: theme_options[x],
            index=list(theme_options.keys()).index(st.session_state["theme"]),
            key="theme_selector"
        )

        if selected_theme != st.session_state["theme"]:
            st.session_state["theme"] = selected_theme
            st.rerun()