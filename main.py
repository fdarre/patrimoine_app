"""
Point d'entrée principal de l'application de gestion patrimoniale
"""

import streamlit as st
import os
import time
from datetime import datetime

from utils.constants import DATA_DIR
from utils.style_loader import load_css
from database.db_config import get_db, engine, Base
from ui.dashboard import show_dashboard
from ui.banks_accounts import show_banks_accounts
from ui.assets import show_asset_management
from ui.analysis import show_analysis
from ui.todos import show_todos
from ui.settings import show_settings
from ui.auth import show_auth, check_auth, logout, get_current_user_id


def main():
    """Fonction principale de l'application"""
    # Configuration de base de l'application
    st.set_page_config(
        page_title="Gestion Patrimoniale",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Charger les styles CSS
    load_css()

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

    # Titre principal avec style simplifié
    st.title("Application de Gestion Patrimoniale")

    # Navigation simplifiée - Utiliser uniquement le composant radio de Streamlit
    st.sidebar.title("Navigation")

    # Définition des options de menu avec icônes
    nav_options = {
        "Dashboard": "📊",
        "Gestion des actifs": "💼",
        "Banques & Comptes": "🏦",
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

    # Obtenir une session de base de données avec gestion des erreurs
    try:
        db = next(get_db())
    except Exception as e:
        st.error(f"Erreur de connexion à la base de données: {str(e)}")
        st.warning("Essai de reconnexion dans 5 secondes...")
        time.sleep(5)
        try:
            db = next(get_db())
        except Exception as e:
            st.error(f"Échec de la reconnexion: {str(e)}")
            st.info("Veuillez redémarrer l'application.")
            return

    try:
        # Afficher un indicateur de chargement pour la page sélectionnée
        with st.spinner(f"Chargement de {page}..."):
            # Afficher la page sélectionnée
            if page == "Dashboard":
                show_dashboard(db, user_id)

            elif page == "Gestion des actifs":
                show_asset_management(db, user_id)

            elif page == "Banques & Comptes":
                show_banks_accounts(db, user_id)

            elif page == "Analyses":
                show_analysis(db, user_id)

            elif page == "Tâches (Todo)":
                show_todos(db, user_id)

            elif page == "Paramètres":
                show_settings(db, user_id)
    except Exception as e:
        # Gestion globale des erreurs
        st.error(f"Une erreur s'est produite: {str(e)}")
        st.info("Si le problème persiste, veuillez vérifier vos données ou contacter l'administrateur.")
        # Journalisation de l'erreur
        import logging
        logging.error(f"Erreur dans l'application: {str(e)}", exc_info=True)
    finally:
        # Toujours fermer la session de base de données
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

    # Bouton de déconnexion simplifié
    st.sidebar.markdown("---")
    if st.sidebar.button("📤 Déconnexion"):
        logout()

    # Afficher les informations de version et l'utilisateur connecté
    st.sidebar.markdown("---")

    # Information utilisateur
    if "user" in st.session_state:
        st.sidebar.text(f"Utilisateur: {st.session_state['user']}")
        st.sidebar.text(f"Version: 3.0")


# Point d'entrée
if __name__ == "__main__":
    # S'assurer que les tables existent
    Base.metadata.create_all(bind=engine)
    main()