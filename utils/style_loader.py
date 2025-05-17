"""
Utilitaire pour charger les styles CSS de l'application
"""
import os
import streamlit as st

def load_css():
    """
    Charge les styles CSS depuis le fichier principal
    et les injecte dans Streamlit
    """
    # Chemin absolu du projet
    project_root = "/home/fred/patrimoine_app"
    
    # Si le chemin absolu n'existe pas, essayer de détecter le répertoire du projet
    if not os.path.exists(project_root):
        # Essayer d'abord avec le chemin relatif (par rapport à ce fichier)
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if os.path.basename(current_dir) == "patrimoine_app":
            project_root = current_dir
        else:
            # Sinon, utiliser le répertoire courant
            project_root = os.getcwd()
    
    # Chemin vers le fichier CSS
    css_file = os.path.join(project_root, "static", "styles", "main.css")
    
    try:
        if os.path.exists(css_file):
            with open(css_file, "r") as f:
                css = f.read()
            
            # Injecter le CSS
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        else:
            # Afficher un message d'erreur en mode développement
            if os.environ.get("STREAMLIT_ENV") == "development":
                st.warning(f"Le fichier CSS {css_file} n'existe pas. Exécutez d'abord scripts/create_directories.py")
            
            # Utiliser le CSS de secours des constantes si le fichier n'existe pas
            from utils.constants import CUSTOM_CSS
            st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    except Exception as e:
        # En cas d'erreur, utiliser le CSS de secours
        from utils.constants import CUSTOM_CSS
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
        
        # Afficher un message d'erreur en mode développement
        if os.environ.get("STREAMLIT_ENV") == "development":
            st.warning(f"Erreur lors du chargement du CSS: {str(e)}")

def load_js():
    """
    Charge le JavaScript pour les fonctionnalités avancées de l'interface
    """
    # Chemin absolu du projet
    project_root = "/home/fred/patrimoine_app"
    
    # Si le chemin absolu n'existe pas, essayer de détecter le répertoire du projet
    if not os.path.exists(project_root):
        # Essayer d'abord avec le chemin relatif (par rapport à ce fichier)
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if os.path.basename(current_dir) == "patrimoine_app":
            project_root = current_dir
        else:
            # Sinon, utiliser le répertoire courant
            project_root = os.getcwd()
    
    # Chemin vers le fichier JS
    js_file = os.path.join(project_root, "static", "js", "main.js")
    
    try:
        if os.path.exists(js_file):
            with open(js_file, "r") as f:
                js = f.read()
            
            # Injecter le JavaScript
            st.markdown(f"<script>{js}</script>", unsafe_allow_html=True)
        else:
            # Afficher un message d'erreur en mode développement
            if os.environ.get("STREAMLIT_ENV") == "development":
                st.warning(f"Le fichier JS {js_file} n'existe pas. Exécutez d'abord scripts/create_directories.py")
    except Exception as e:
        # Afficher un message d'erreur en mode développement
        if os.environ.get("STREAMLIT_ENV") == "development":
            st.warning(f"Erreur lors du chargement du JavaScript: {str(e)}")
