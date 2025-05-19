"""
Point d'entrée principal de l'application de gestion patrimoniale
"""
import os
import sys
import uuid
from datetime import datetime

import streamlit as st

from config.app_config import LOGS_DIR, DB_PATH
from database.db_config import engine, get_db_session
from database.models import Base, User
from ui.analysis import show_analysis
from ui.assets import show_asset_management
from ui.auth import show_auth, check_auth, logout, get_current_user_id
from ui.banks_accounts import show_banks_accounts
from ui.dashboard import show_dashboard
from ui.settings import show_settings
from ui.templates.template_management import show_template_management
from ui.todos import show_todos
from utils.error_manager import catch_exceptions
from utils.logger import get_logger, setup_file_logging
from utils.migration_manager import migration_manager
from utils.password import hash_password
from utils.session_manager import session_manager
from utils.style_manager import initialize_styles

# Configurer le logger
logger = get_logger(__name__)


def initialize_database():
    """
    Initialise la base de données et crée un utilisateur admin si nécessaire
    """
    logger.info("Vérification de la base de données...")

    # 1. Créer les tables si elles n'existent pas
    if not os.path.exists(DB_PATH):
        logger.info("Base de données inexistante. Création des tables...")
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

            # Créer toutes les tables directement avec SQLAlchemy
            Base.metadata.create_all(bind=engine)
            logger.info("Tables créées avec succès.")

            # Initialiser les migrations pour suivre les futurs changements
            migration_manager.initialize_database()
            logger.info("Système de migrations initialisé.")
        except Exception as e:
            logger.critical(f"Échec de la création des tables: {str(e)}")
            st.error(f"Erreur critique lors de l'initialisation de la base de données: {str(e)}")
            sys.exit(1)

        # 2. Créer un utilisateur administrateur par défaut
        try:
            with get_db_session() as db:
                # Vérifier si des utilisateurs existent
                user_count = db.query(User).count()

                if user_count == 0:
                    logger.info("Création de l'utilisateur admin par défaut...")

                    # Créer l'utilisateur
                    admin_user = User(
                        id=str(uuid.uuid4()),
                        username="admin",
                        email="admin@exemple.com",
                        password_hash=hash_password("admin123"),
                        is_active=True,
                        created_at=datetime.now()
                    )

                    db.add(admin_user)
                    logger.info("Utilisateur administrateur créé avec succès.")
        except Exception as e:
            logger.error(f"Échec de la création de l'utilisateur admin: {str(e)}")
            # Ne pas planter l'application pour cette erreur, l'utilisateur pourra en créer un manuellement
    else:
        # Base existante - vérifier si elle est à jour avec les migrations
        try:
            # Vérifier si la base contient au moins les tables essentielles
            from sqlalchemy import inspect
            inspector = inspect(engine)

            if "users" not in inspector.get_table_names():
                logger.warning("Base de données existante mais incomplète. Tentative de mise à jour...")
                Base.metadata.create_all(bind=engine)
                migration_manager.initialize_database()

            # Mettre à jour la base avec les dernières migrations (si nécessaire)
            migration_manager.upgrade_database("head")
            logger.info("Base de données à jour avec les dernières migrations.")
        except Exception as e:
            logger.error(f"Erreur lors de la vérification/mise à jour de la base de données: {str(e)}")
            # Continuer quand même, en espérant que la base soit utilisable


@catch_exceptions
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
        # Afficher la page sélectionnée
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
    LOGS_DIR.mkdir(exist_ok=True)

    # Initialiser la base de données si nécessaire
    initialize_database()

    # Démarrer l'application
    main()