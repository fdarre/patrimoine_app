"""
Point d'entrée principal de l'application de gestion patrimoniale
"""
import os
import sys
from datetime import datetime

import streamlit as st

from config.app_config import LOGS_DIR, DB_PATH
from ui.analysis import show_analysis
from ui.assets import show_asset_management
from ui.auth import show_auth, check_auth, logout, get_current_user_id
from ui.banks_accounts import show_banks_accounts
from ui.dashboard import show_dashboard
from ui.settings import show_settings
from ui.templates.template_management import show_template_management
from ui.todos import show_todos
from utils.error_manager import catch_exceptions  # Utiliser le nouveau gestionnaire d'erreurs
from utils.logger import get_logger, setup_file_logging
from utils.session_manager import session_manager  # Utiliser le gestionnaire de session
from utils.style_manager import initialize_styles

# Configurer le logger
logger = get_logger(__name__)


@catch_exceptions  # Remplacé streamlit_exception_handler par catch_exceptions
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
    initialize_styles()

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
        # Afficher la page sélectionnée - plus besoin de passer db et user_id en arguments
        # Les pages récupèrent ces informations via get_db_session et session_manager
        if page == "Dashboard":
            show_dashboard()
        elif page == "Gestion des actifs":
            show_asset_management()
        elif page == "Banques & Comptes":
            show_banks_accounts()
        elif page == "Modèles d'actifs":
            show_template_management()
        elif page == "Analyses":
            show_analysis()
        elif page == "Tâches (Todo)":
            show_todos()
        elif page == "Paramètres":
            show_settings()
    except Exception as e:
        logger.exception(f"Exception non gérée: {str(e)}")
        st.error("Une erreur inattendue s'est produite. Veuillez consulter les logs pour plus de détails.")

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

    # Information utilisateur avec style moderne - utiliser le gestionnaire de session
    username = session_manager.get("user")
    if username:
        # Format de date moderne
        current_date = datetime.now().strftime("%d %b %Y")

        st.sidebar.markdown(f"""
        <div class="user-profile">
            <div class="user-avatar">👤</div>
            <div class="user-info">
                <div class="user-name">{username}</div>
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
    # S'assurer que les dossiers de logs existent
    LOGS_DIR.mkdir(exist_ok=True)  # Utiliser la méthode mkdir() de Path

    # Initialiser la base de données avec les migrations Alembic
    from utils.migration_manager import migration_manager

    # Vérifier si la base existe déjà et est initialisée
    if not os.path.exists(DB_PATH) or migration_manager.get_current_version() is None:
        logger.info("Initialisation de la base de données...")
        if not migration_manager.initialize_database():
            logger.critical("Échec de l'initialisation de la base de données avec les migrations.")
            sys.exit(1)
        logger.info("Base de données initialisée avec succès.")
    else:
        logger.info(f"Base de données déjà initialisée, version: {migration_manager.get_current_version()}")

    # Démarrer l'application
    main()