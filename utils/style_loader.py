"""
Utilitaire pour gérer le chargement et l'application des styles CSS
"""
import streamlit as st
import os

def load_css(filename="main.css"):
    """
    Charge un fichier CSS depuis le dossier static/styles

    Args:
        filename: Nom du fichier CSS à charger
    """
    css_path = os.path.join("static", "styles", filename)
    try:
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Fichier CSS {css_path} non trouvé")

def load_js(filename="scripts.js"):
    """
    Charge un fichier JavaScript depuis le dossier static/scripts

    Args:
        filename: Nom du fichier JS à charger
    """
    js_path = os.path.join("static", "scripts", filename)
    try:
        with open(js_path, "r") as f:
            st.markdown(f"<script>{f.read()}</script>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Fichier JavaScript {js_path} non trouvé")

def initialize_styles():
    """
    Initialise les styles globaux de l'application
    """
    # Charger le CSS principal
    load_css("main.css")

    # Appliquer les styles de base supplémentaires pour Streamlit
    st.markdown("""
    <style>
    /* Réinitialisation de base pour Streamlit */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Masquer les éléments de débogage et le menu de hamburger */
    #MainMenu, footer, .stDeployButton {
        display: none !important;
    }
    
    /* Ajustements pour les colonnes */
    [data-testid="column"] {
        padding: 0.5rem !important;
    }
    
    /* Suppression des marges excessives */
    .stMarkdown {
        margin-bottom: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def create_theme_selector():
    """
    Crée un sélecteur de thème (clair/sombre) dans la barre latérale
    """
    # Ajouter le sélecteur de thème dans la sidebar
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"  # Thème par défaut

    theme_options = {
        "dark": "🌙 Sombre",
        "light": "☀️ Clair"
    }

    with st.sidebar:
        selected_theme = st.selectbox(
            "Thème",
            options=list(theme_options.keys()),
            format_func=lambda x: theme_options[x],
            index=0 if st.session_state["theme"] == "dark" else 1,
            key="theme_selector"
        )

        if selected_theme != st.session_state["theme"]:
            st.session_state["theme"] = selected_theme
            st.rerun()

    # Appliquer le thème sélectionné
    if st.session_state["theme"] == "light":
        st.markdown("""
        <style>
        :root {
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --sidebar-bg: #f1f5f9;
            --text-light: #0f172a;
            --text-muted: #64748b;
            --text-dark: #0f172a;
        }
        </style>
        """, unsafe_allow_html=True)

def get_theme_color(color_name):
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
        "text_light": "var(--text-light)",
        "text_muted": "var(--text-muted)",
        "text_dark": "var(--text-dark)",
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

def get_class(class_name):
    """
    Récupère une classe CSS avec un préfixe unique pour éviter les conflits

    Args:
        class_name: Nom de la classe

    Returns:
        Nom de classe préfixé
    """
    return f"pgp-{class_name}"  # pgp pour "Portfolio Gestion Patrimoniale"

def create_styled_element(tag, content, classes=None, styles=None, attributes=None):
    """
    Crée un élément HTML stylisé

    Args:
        tag: Tag HTML à utiliser
        content: Contenu de l'élément
        classes: Liste des classes CSS à appliquer
        styles: Dictionnaire des styles inline à appliquer
        attributes: Dictionnaire des attributs à ajouter

    Returns:
        Chaîne HTML de l'élément
    """
    # Construire la chaîne de classes
    classes_str = ""
    if classes:
        classes_str = ' class="' + ' '.join([get_class(cls) for cls in classes]) + '"'

    # Construire la chaîne de styles
    styles_str = ""
    if styles:
        styles_str = ' style="' + ';'.join([f"{k}:{v}" for k, v in styles.items()]) + '"'

    # Construire la chaîne d'attributs
    attributes_str = ""
    if attributes:
        attributes_str = ' ' + ' '.join([f'{k}="{v}"' for k, v in attributes.items()])

    # Construire l'élément complet
    return f"<{tag}{classes_str}{styles_str}{attributes_str}>{content}</{tag}>"

def create_card(title, content, footer=None, extra_classes=None):
    """
    Crée une carte stylisée

    Args:
        title: Titre de la carte
        content: Contenu HTML de la carte
        footer: Pied de page de la carte (optionnel)
        extra_classes: Classes CSS supplémentaires

    Returns:
        Chaîne HTML de la carte
    """
    classes = ["card"]
    if extra_classes:
        classes.append(extra_classes)

    footer_html = ""
    if footer:
        footer_html = f"""<div class="{get_class('card-footer')}">{footer}</div>"""

    return f"""
    <div class="{' '.join([get_class(cls) for cls in classes])}">
        <div class="{get_class('card-header')}">
            <h3 class="{get_class('card-title')}">{title}</h3>
        </div>
        <div class="{get_class('card-body')}">
            {content}
        </div>
        {footer_html}
    </div>
    """

def create_badge(text, type="primary", size="normal"):
    """
    Crée un badge stylisé

    Args:
        text: Texte du badge
        type: Type de badge ('primary', 'secondary', 'success', 'warning', 'danger')
        size: Taille du badge ('small', 'normal', 'large')

    Returns:
        Chaîne HTML du badge
    """
    size_class = ""
    if size == "small":
        size_class = "badge-sm"
    elif size == "large":
        size_class = "badge-lg"

    return f"""<span class="{get_class('badge')} {get_class(f'badge-{type}')} {get_class(size_class)}">{text}</span>"""

def create_button_style(button_type):
    """
    Crée un style pour un bouton

    Args:
        button_type: Type de bouton ('primary', 'secondary', 'success', 'warning', 'danger')

    Returns:
        Chaîne CSS pour le bouton
    """
    color = get_theme_color(button_type)
    hover_color = get_theme_color(f"{button_type}-dark" if "-dark" not in button_type else button_type)

    return f"""
    <style>
    div.stButton > button {{
        background-color: {color};
        color: white;
        border: none;
        border-radius: var(--radius-md);
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    
    div.stButton > button:hover {{
        background-color: {hover_color};
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transform: translateY(-1px);
    }}
    
    div.stButton > button:active {{
        transform: translateY(0);
    }}
    </style>
    """