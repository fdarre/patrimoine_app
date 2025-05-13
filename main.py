"""
Point d'entrée principal de l'application de gestion patrimoniale
"""

import streamlit as st
import os

from utils.constants import CUSTOM_CSS
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
        layout="wide"
    )

    # Injecter le CSS personnalisé
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

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

    # Titre principal
    st.title("Application de Gestion Patrimoniale", anchor=False)

    # Navigation dans la barre latérale
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Sélectionner une page",
        ["Dashboard", "Gestion des actifs", "Banques & Comptes", "Analyses", "Tâches (Todo)", "Paramètres"]
    )

    # Obtenir une session de base de données
    db = next(get_db())

    try:
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
    finally:
        # Toujours fermer la session de base de données
        db.close()

    # Afficher un message d'aide dans la barre latérale
    st.sidebar.markdown("---")
    with st.sidebar.expander("🔍 Aide"):
        st.markdown("""
        1. Commencez par ajouter des **banques** dans la section "Banques & Comptes"
        2. Puis créez des **comptes** pour chaque banque
        3. Ajoutez vos **actifs** dans ces comptes via la section "Gestion des actifs"
        4. Pour les fonds mixtes, spécifiez l'allocation par catégorie et la répartition géographique pour chaque catégorie
        5. Pour les actifs composites, ajoutez des composants pour modéliser les produits complexes
        6. Consultez votre **dashboard** et les **analyses** détaillées

        Toutes vos données sont stockées dans une base de données sécurisée avec chiffrement des données sensibles.
        """)

    # Bouton de déconnexion
    if st.sidebar.button("Déconnexion"):
        logout()

    # Afficher les informations de version
    st.sidebar.markdown("---")
    st.sidebar.markdown("v3.0 - Base de données sécurisée & Multi-utilisateurs")

    # Afficher l'utilisateur connecté
    if "user" in st.session_state:
        st.sidebar.markdown(f"**Utilisateur:** {st.session_state['user']}")


# Point d'entrée
if __name__ == "__main__":
    # S'assurer que les tables existent
    Base.metadata.create_all(bind=engine)
    main()