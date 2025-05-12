"""
Point d'entrée principal de l'application de gestion patrimoniale
"""

import streamlit as st
import os

from utils.constants import CUSTOM_CSS
from services.data_service import DataService
from ui.dashboard import show_dashboard
from ui.banks_accounts import show_banks_accounts
from ui.assets import show_asset_management
from ui.analysis import show_analysis
from ui.todos import show_todos
from ui.settings import show_settings


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

    # Titre principal
    st.title("Application de Gestion Patrimoniale", anchor=False)

    # Chargement des données
    banks, accounts, assets, history = DataService.load_data()

    # Navigation dans la barre latérale
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Sélectionner une page",
        ["Dashboard", "Gestion des actifs", "Banques & Comptes", "Analyses", "Tâches (Todo)", "Paramètres"]
    )

    # Afficher la page sélectionnée
    if page == "Dashboard":
        show_dashboard(banks, accounts, assets, history)

    elif page == "Gestion des actifs":
        show_asset_management(banks, accounts, assets, history)

    elif page == "Banques & Comptes":
        show_banks_accounts(banks, accounts, assets, history)

    elif page == "Analyses":
        show_analysis(banks, accounts, assets, history)

    elif page == "Tâches (Todo)":
        show_todos(banks, accounts, assets, history)

    elif page == "Paramètres":
        show_settings(banks, accounts, assets, history)

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

        Toutes vos données sont stockées dans le dossier `data/`. Une sauvegarde est 
        créée automatiquement à chaque modification.
        """)

    # Afficher les informations de version
    st.sidebar.markdown("---")
    st.sidebar.markdown("v2.0 - Nouvelle architecture & Actifs composites")


# Point d'entrée
if __name__ == "__main__":
    main()