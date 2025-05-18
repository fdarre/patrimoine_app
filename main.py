"""
Point d'entrée principal de l'application de gestion patrimoniale
"""

import streamlit as st
import os
from datetime import datetime

from config.app_config import LOGS_DIR
from utils.style_manager import initialize_styles, create_theme_selector
from utils.logger import get_logger, setup_file_logging
from utils.decorators import streamlit_exception_handler
from utils.exceptions import AppError
from database.db_config import get_db, engine, Base
from ui.dashboard import show_dashboard
from ui.banks_accounts import show_banks_accounts
from ui.assets import show_asset_management
from ui.analysis import show_analysis
from ui.todos import show_todos
from ui.settings import show_settings
from ui.auth import show_auth, check_auth, logout, get_current_user_id
from ui.templates.template_management import show_template_management

# Configurer le logger
logger = get_logger(__name__)

@streamlit_exception_handler
def main():
    """Fonction principale de l'application"""
    # Configuration de base de l'application
    st.set_page_config(
        page_title="Gestion Patrimoniale",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialiser les styles - IMPORTANT : doit être appelé avant tout autre rendu
    initialize_styles()  # Utilisation du gestionnaire unifié

    # Ajouter le sélecteur de thème dans la barre latérale
    create_theme_selector()

    # Vérifier l'authentification
    is_authenticated = check_auth()

    if not is_authenticated:
        # Afficher l'interface d'authentification
        show_auth()
        return

    # Récupérer l'ID de l'utilisateur courant
    user_id = get_current_user_id()
    if not user_id:
        show_auth()
        return

    # Configurer le logging pour l'utilisateur
    setup_file_logging(user_id)

    # Titre principal avec style moderne
    st.title("Application de Gestion Patrimoniale")

    # Navigation dans la barre latérale avec icônes
    st.sidebar.title("Navigation")

    # Définition des options de menu avec icônes
    nav_options = {
        "Dashboard": "📊",
        "Gestion des actifs": "💼",
        "Banques & Comptes": "🏦",
        "Modèles d'actifs": "📋",
        "Analyses": "📈",
        "Tâches (Todo)": "✅",
        "Paramètres": "⚙️"
    }

    # Utiliser le sélecteur standard de Streamlit pour la navigation
    page = st.sidebar.radio(
        "Sélectionner une page",
        list(nav_options.keys()),
        format_func=lambda x: f"{nav_options[x]} {x}",
        key="navigation"
    )

    try:
        # Obtenir une session de base de données
        db = next(get_db())

        # Afficher la page sélectionnée
        if page == "Dashboard":
            show_dashboard(db, user_id)
        elif page == "Gestion des actifs":
            show_asset_management(db, user_id)
        elif page == "Banques & Comptes":
            show_banks_accounts(db, user_id)
        elif page == "Modèles d'actifs":
            show_template_management(db, user_id)
        elif page == "Analyses":
            show_analysis(db, user_id)
        elif page == "Tâches (Todo)":
            show_todos(db, user_id)
        elif page == "Paramètres":
            show_settings(db, user_id)
    except AppError as e:
        st.error(f"Erreur: {e.message}")
        logger.error(f"Erreur d'application: {e.message}")
    except Exception as e:
        st.error(f"Une erreur inattendue s'est produite. Veuillez consulter les logs pour plus de détails.")
        logger.exception(f"Exception non gérée: {str(e)}")
    finally:
        # S'assurer que la session de base de données est fermée
        if 'db' in locals():
            db.close()

    # Afficher un message d'aide dans la barre latérale
    st.sidebar.markdown("---")
    with st.sidebar.expander("🔍 Aide"):
        st.markdown("""
        ### Guide rapide

        1. Commencez par ajouter des **banques** dans la section "Banques & Comptes"
        2. Puis créez des **comptes** pour chaque banque
        3. Ajoutez vos **actifs** dans ces comptes via la section "Gestion des actifs"
        4. Pour les fonds mixtes, spécifiez l'allocation par catégorie et la répartition géographique pour chaque catégorie
        5. Consultez votre **dashboard** et les **analyses** détaillées

        Vos données sont sécurisées avec une base de données chiffrée et des sauvegardes automatiques.
        """)

    # Bouton de déconnexion stylisé
    st.sidebar.markdown("---")
    if st.sidebar.button("📤 Déconnexion", key="logout_button"):
        logout()

    # Afficher les informations stylisées en bas de la sidebar
    st.sidebar.markdown("---")

    # Information utilisateur avec style moderne
    if "user" in st.session_state:
        user = st.session_state['user']
        # Format de date moderne
        current_date = datetime.now().strftime("%d %b %Y")

        st.sidebar.markdown(f"""
        <div class="user-profile">
            <div class="user-avatar">👤</div>
            <div class="user-info">
                <div class="user-name">{user}</div>
                <div class="user-date">{current_date}</div>
            </div>
        </div>
        <div class="user-status">
            <span>Version 3.0</span>
            <span>Pro</span>
        </div>
        """, unsafe_allow_html=True)

# Point d'entrée
if __name__ == "__main__":
    # S'assurer que les tables existent
    Base.metadata.create_all(bind=engine)

    # S'assurer que les dossiers de logs existent
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Démarrer l'application
    main()