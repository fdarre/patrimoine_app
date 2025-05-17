"""
Utilitaire pour charger les styles CSS et améliorer l'expérience utilisateur
"""
import os
import streamlit as st
import time

def load_css():
    """
    Charge les styles CSS depuis le fichier principal
    et les injecte dans Streamlit
    """
    # Chemin absolu du projet
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Chemin vers le fichier CSS
    css_file = os.path.join(project_root, "static", "styles", "main.css")

    try:
        if os.path.exists(css_file):
            with open(css_file, "r") as f:
                css = f.read()

            # Injecter uniquement le CSS sans le splash screen problématique
            st.markdown(f"""
            <style>
            {css}
            </style>
            """, unsafe_allow_html=True)
        else:
            # Utiliser le CSS de secours des constantes si le fichier n'existe pas
            from config.app_config import CUSTOM_CSS
            st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    except Exception as e:
        # En cas d'erreur, utiliser le CSS de secours
        from config.app_config import CUSTOM_CSS
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

        # Afficher un message d'erreur en console pour le débogage
        print(f"Erreur lors du chargement du CSS: {str(e)}")


def load_js():
    """
    Charge les scripts JS supplémentaires pour améliorer l'interface
    Note: Limité aux interactions basiques pour compatibilité Streamlit
    """
    # Nous ne chargeons plus de JavaScript complexe pour éviter les problèmes
    pass