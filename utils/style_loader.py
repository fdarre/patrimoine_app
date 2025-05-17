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
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Chemin vers le fichier CSS
    css_file = os.path.join(project_root, "static", "styles", "main.css")

    try:
        if os.path.exists(css_file):
            with open(css_file, "r") as f:
                css = f.read()

            # Injecter le CSS
            st.markdown(f"""
            <style>
            {css}
            
            /* Correctifs supplémentaires pour les problèmes d'interface */
            /* Correction des rectangles gris vides */
            [data-testid="stVerticalBlock"] > div > div:empty {
                display: none !important;
            }
            
            /* Correction des éléments de navigation dupliqués */
            [data-testid="stSidebar"] ul:nth-of-type(2) {
                display: none !important;
            }
            
            /* Améliorer les contrastes */
            .stApp {
                background-color: #121212;
            }
            
            /* Améliorer l'apparence des métriques */
            [data-testid="stMetric"] {
                background-color: #1e1e1e;
                padding: 1rem;
                border-radius: 0.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            </style>
            """, unsafe_allow_html=True)
        else:
            # Utiliser le CSS de secours des constantes si le fichier n'existe pas
            from utils.constants import CUSTOM_CSS
            st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    except Exception as e:
        # En cas d'erreur, utiliser le CSS de secours
        from utils.constants import CUSTOM_CSS
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

        # Afficher un message d'erreur en console pour le débogage
        print(f"Erreur lors du chargement du CSS: {str(e)}")

def load_js():
    """Fonction maintenue pour la compatibilité"""
    pass