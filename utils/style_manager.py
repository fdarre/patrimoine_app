"""
Gestionnaire unifié de styles pour l'application
"""
import streamlit as st
import os
from typing import Optional, List, Dict, Any

# Chemins des dossiers de styles
STATIC_DIR = "static"
STYLES_DIR = os.path.join(STATIC_DIR, "styles")
CORE_DIR = os.path.join(STYLES_DIR, "core")
COMPONENTS_DIR = os.path.join(STYLES_DIR, "components")
THEMES_DIR = os.path.join(STYLES_DIR, "themes")

# Thèmes disponibles
THEMES = {
    "dark": {
        "name": "Sombre",
        "icon": "🌙",
        "file": "dark-theme.css",
        "is_default": True,
        "colors": {
            "primary_color": "#6366f1",
            "primary_light": "#818cf8",
            "primary_dark": "#4f46e5",
            "secondary_color": "#ec4899",
            "secondary_light": "#f472b6",
            "secondary_dark": "#db2777",
            "success_color": "#10b981",
            "warning_color": "#f59e0b",
            "danger_color": "#ef4444",
            "info_color": "#0ea5e9",
            "bg_color": "#0f172a",
            "card_bg": "#1e293b",
            "sidebar_bg": "#0f172a",
            "text_light": "#f8fafc",
            "text_muted": "#94a3b8",
            "text_dark": "#1e293b"
        }
    },
    "light": {
        "name": "Clair",
        "icon": "☀️",
        "file": "light-theme.css",
        "is_default": False,
        "colors": {
            "primary_color": "#4f46e5",
            "primary_light": "#5e78ff",
            "primary_dark": "#2b4acb",
            "secondary_color": "#db2777",
            "secondary_light": "#ff5a6a",
            "secondary_dark": "#c62f3a",
            "success_color": "#059669",
            "warning_color": "#d97706",
            "danger_color": "#dc2626",
            "info_color": "#0284c7",
            "bg_color": "#f8fafc",
            "card_bg": "#ffffff",
            "sidebar_bg": "#f1f5f9",
            "text_light": "#0f172a",
            "text_muted": "#64748b",
            "text_dark": "#0f172a"
        }
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

def load_css(css_file_name: str) -> Optional[str]:
    """
    Charge un fichier CSS depuis les répertoires standard

    Args:
        css_file_name: Nom du fichier CSS (sans chemin complet)

    Returns:
        Contenu du CSS ou None si fichier non trouvé
    """
    # Chercher dans différents dossiers en ordre de priorité
    for directory in [CORE_DIR, COMPONENTS_DIR, STYLES_DIR]:
        path = os.path.join(directory, css_file_name)
        if os.path.exists(path):
            return load_css_file(path)

    print(f"Fichier CSS introuvable: {css_file_name}")
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
        "primary": "var(--primary-color)",
        "secondary": "var(--secondary-color)",
        "success": "var(--success-color)",
        "warning": "var(--warning-color)",
        "danger": "var(--danger-color)",
        "info": "var(--info-color)",
        "text-light": "var(--text-light)",
        "text-muted": "var(--text-muted)",
        "text-dark": "var(--text-dark)",
        "bg": "var(--bg-color)",
        "card": "var(--card-bg)"
    }

    # Si le nom est un raccourci, retourner la valeur mappée
    if color_name in color_mappings:
        return color_mappings[color_name]

    # Sinon tenter d'interpréter comme une variable CSS
    if color_name.startswith("--"):
        return f"var({color_name})"
    else:
        return f"var(--{color_name})"

def get_current_theme() -> str:
    """
    Récupère le thème actif

    Returns:
        Clé du thème actif
    """
    return st.session_state.get("theme", next((k for k, v in THEMES.items() if v["is_default"]), "dark"))