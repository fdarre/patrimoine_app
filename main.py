"""
Point d'entrée principal de l'application de gestion patrimoniale
"""

import streamlit as st
import os
from datetime import datetime

from utils.constants import DATA_DIR
from utils.style_loader import load_css, load_js
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

    # Titre principal avec style moderne
    st.title("Application de Gestion Patrimoniale")

    # Navigation dans la barre latérale avec icônes
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

        # Afficher un bouton stylisé pour réessayer
        if st.button("🔄 Réessayer la connexion", key="retry_connection"):
            try:
                db = next(get_db())
                st.success("Connexion réussie!")
                st.rerun()
            except Exception as e:
                st.error(f"Échec de la reconnexion: {str(e)}")
                st.info("Veuillez vérifier la configuration de la base de données.")
                return
        return

    try:
        # Afficher la page sélectionnée directement sans transitions artificielles
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
        # Gestion globale des erreurs avec style moderne
        st.error(f"Une erreur s'est produite: {str(e)}")

        st.markdown("""
        <div class="card-container" style="background-color: rgba(239, 68, 68, 0.1); padding: 1.5rem;">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 2rem; margin-right: 1rem;">⚠️</span>
                <div>
                    <h3 style="margin: 0;">Erreur de l'application</h3>
                    <p>Si le problème persiste, veuillez vérifier vos données ou contacter l'administrateur.</p>
                </div>
            </div>
            <pre style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 0.5rem; overflow: auto;">{str(e)}</pre>
        </div>
        """, unsafe_allow_html=True)

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
        <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(30, 41, 59, 0.4)); 
                    padding: 1rem; border-radius: 0.5rem; border: 1px solid rgba(255, 255, 255, 0.05);">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <div style="width: 2.5rem; height: 2.5rem; border-radius: 50%; background: linear-gradient(135deg, #6366f1, #ec4899); 
                          display: flex; align-items: center; justify-content: center; margin-right: 0.75rem;">
                    <span style="color: white; font-size: 1.25rem;">👤</span>
                </div>
                <div>
                    <div style="font-weight: 600; font-size: 1rem;">{user}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">{current_date}</div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted);">
                <span>Version 3.0</span>
                <span>Pro</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# Point d'entrée
if __name__ == "__main__":
    # S'assurer que les tables existent
    Base.metadata.create_all(bind=engine)
    main()