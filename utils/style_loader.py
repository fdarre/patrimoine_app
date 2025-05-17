"""
Utilitaire pour charger les styles CSS de l'application - Version sans JavaScript
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
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        else:
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


# Cette fonction remplace la fonctionnalité JS par des composants Streamlit natifs
def apply_streamlit_config():
    """
    Configure Streamlit pour une meilleure apparence et expérience utilisateur
    """
    # Configuration de la page
    st.set_page_config(
        page_title="Gestion Patrimoniale",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Charger le CSS
    load_css()

    # Définir les propriétés globales de la session si elles n'existent pas déjà
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []

    # Traiter les notifications existantes
    process_notifications()


def add_notification(message, type="info", duration=3):
    """
    Ajoute une notification à afficher

    Args:
        message: Message à afficher
        type: Type de notification ('info', 'success', 'warning', 'error')
        duration: Durée d'affichage en secondes (0 pour permanent)
    """
    import time

    notification = {
        "message": message,
        "type": type,
        "created_at": time.time(),
        "duration": duration
    }

    st.session_state.notifications.append(notification)


def process_notifications():
    """
    Traite et affiche les notifications en attente
    """
    import time

    if not hasattr(st.session_state, "notifications"):
        return

    current_time = time.time()
    remaining_notifications = []

    # Créer un container au sommet de la page pour les notifications
    if st.session_state.notifications:
        notification_container = st.container()

        with notification_container:
            for notif in st.session_state.notifications:
                # Vérifier si la notification doit être affichée
                if notif["duration"] == 0 or current_time - notif["created_at"] < notif["duration"]:
                    # Afficher la notification avec le type approprié
                    if notif["type"] == "success":
                        st.success(notif["message"])
                    elif notif["type"] == "warning":
                        st.warning(notif["message"])
                    elif notif["type"] == "error":
                        st.error(notif["message"])
                    else:
                        st.info(notif["message"])

                    # Garder les notifications permanentes ou celles qui n'ont pas expiré
                    if notif["duration"] == 0 or current_time - notif["created_at"] < notif["duration"]:
                        remaining_notifications.append(notif)

    # Mettre à jour la liste des notifications
    st.session_state.notifications = remaining_notifications


def load_js():
    """
    Fonction maintenue pour la compatibilité, mais ne fait plus rien
    """
    pass