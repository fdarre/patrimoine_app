"""
Utilitaire pour charger les styles CSS et améliorer l'expérience utilisateur
"""
import os
import streamlit as st
import time

def load_css():
    """
    Charge les styles CSS depuis le fichier principal
    et les injecte dans Streamlit avec des améliorations
    """
    # Chemin absolu du projet
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Chemin vers le fichier CSS
    css_file = os.path.join(project_root, "static", "styles", "main.css")

    try:
        if os.path.exists(css_file):
            with open(css_file, "r") as f:
                css = f.read()

            # Injecter le CSS et le splash screen
            st.markdown(f"""
            <style>
            {css}
            </style>
            
            <div id="splash-screen" class="splash-screen">
                <div class="splash-content">
                    <div class="splash-title">Gestion Patrimoniale</div>
                    <div class="splash-subtitle">Chargement...</div>
                </div>
            </div>
            
            <script>
            // Fonction pour masquer l'écran de démarrage après le chargement
            document.addEventListener('DOMContentLoaded', function() {{
                setTimeout(function() {{
                    const splash = document.getElementById('splash-screen');
                    if (splash) {{
                        splash.style.opacity = '0';
                        splash.style.transition = 'opacity 0.5s ease-in-out';
                        setTimeout(function() {{
                            splash.style.display = 'none';
                        }}, 500);
                    }}
                }}, 1000);
            }});
            </script>
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
    """
    Charge les scripts JS supplémentaires pour améliorer l'interface
    """
    st.markdown("""
    <script>
    // Améliorer l'apparence du chargement des pages
    document.addEventListener('DOMContentLoaded', function() {
        // Appliquer des transitions douces aux éléments
        const allElements = document.querySelectorAll('*');
        allElements.forEach(function(el) {
            if (!el.style.transition) {
                el.style.transition = 'all 0.3s ease-in-out';
            }
        });
    });
    
    // Améliorer l'expérience des menus de navigation
    const enhanceNavigation = () => {
        const navItems = document.querySelectorAll('[data-testid="stSidebar"] [role="radiogroup"] label');
        navItems.forEach(item => {
            item.addEventListener('mouseenter', function() {
                this.style.transform = 'translateX(5px)';
            });
            
            item.addEventListener('mouseleave', function() {
                this.style.transform = 'translateX(0)';
            });
        });
    };
    
    // Exécuter après un délai pour s'assurer que les éléments sont chargés
    setTimeout(enhanceNavigation, 1000);
    </script>
    """, unsafe_allow_html=True)