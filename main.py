"""
Point d'entrée principal de l'application de gestion patrimoniale - Version Streamlit Only
"""

import streamlit as st
import os
import time
from datetime import datetime

from utils.constants import DATA_DIR
from utils.style_loader import load_css, apply_streamlit_config
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
    # Appliquer les configurations et styles de Streamlit
    apply_streamlit_config()

    # Créer un conteneur pour les notifications
    notification_area = st.container()

    # Afficher un indicateur de chargement pendant l'initialisation
    with st.spinner("Chargement de l'application..."):
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

    # Titre principal avec style amélioré
    st.markdown("""
    <h1 style="color:#fff;border-bottom:2px solid var(--primary-color);padding-bottom:0.5rem;">
        Application de Gestion Patrimoniale
    </h1>
    """, unsafe_allow_html=True)

    # Navigation dans la barre latérale avec icônes et descriptions
    st.sidebar.markdown("<h1 style='font-size:1.5rem;'>Navigation</h1>", unsafe_allow_html=True)

    # Amélioration avec des icônes et descriptions
    nav_options = {
        "Dashboard": {"icon": "📊", "desc": "Vue d'ensemble de votre patrimoine"},
        "Gestion des actifs": {"icon": "💼", "desc": "Ajout et gestion de vos actifs"},
        "Banques & Comptes": {"icon": "🏦", "desc": "Gestion des banques et comptes"},
        "Analyses": {"icon": "📈", "desc": "Analyses détaillées et visualisations"},
        "Tâches (Todo)": {"icon": "✅", "desc": "Gestion des tâches à réaliser"},
        "Paramètres": {"icon": "⚙️", "desc": "Configuration de l'application"}
    }

    # Créer un élément pour chaque option de navigation et l'ajouter à la barre latérale
    for option, details in nav_options.items():
        st.sidebar.markdown(f"""
        <div class="nav-item" id="nav_{option.lower().replace(' ', '_')}">
            <div style="display:flex;align-items:center;">
                <div style="font-size:1.5rem;margin-right:10px;">{details['icon']}</div>
                <div>
                    <div style="font-weight:600;">{option}</div>
                    <div style="font-size:0.8rem;color:#adb5bd;">{details['desc']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Utiliser le sélecteur standard de Streamlit pour la navigation
    page = st.sidebar.radio(
        "Sélectionner une page",
        list(nav_options.keys()),
        format_func=lambda x: f"{nav_options[x]['icon']} {x}",
        label_visibility="collapsed"  # Cacher le titre pour éviter la duplication visuelle
    )

    # Obtenir une session de base de données avec gestion des erreurs
    try:
        db = next(get_db())
    except Exception as e:
        st.error(f"Erreur de connexion à la base de données: {str(e)}")

        # Afficher un bouton pour réessayer
        if st.button("🔄 Réessayer la connexion"):
            try:
                db = next(get_db())
                st.success("Connexion à la base de données réussie!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Échec de la reconnexion: {str(e)}")
                st.info("Veuillez vérifier la configuration de la base de données et redémarrer l'application.")
                return
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

        # Option pour revenir à la page précédente
        if st.button("⬅️ Retour à la page précédente"):
            # Si la page précédente est stockée dans la session, y retourner
            if 'previous_page' in st.session_state:
                st.session_state['page'] = st.session_state['previous_page']
                st.rerun()

        # Journalisation de l'erreur
        import logging
        logging.error(f"Erreur dans l'application: {str(e)}", exc_info=True)
    finally:
        # Toujours fermer la session de base de données
        db.close()

    # Mettre à jour la page actuelle dans la session
    if 'page' in st.session_state:
        st.session_state['previous_page'] = st.session_state['page']
    st.session_state['page'] = page

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

    # Bouton de déconnexion avec style amélioré
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns([1, 1])

    with col1:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("📤 Déconnexion", use_container_width=True):
            with st.spinner("Déconnexion en cours..."):
                logout()

    # Afficher les informations de version et l'utilisateur connecté
    st.sidebar.markdown("---")

    # Créer un pied de page avec l'utilisateur connecté et la date
    current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")

    if "user" in st.session_state:
        st.sidebar.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:2rem;font-size:0.8rem;color:#adb5bd;">
            <div>👤 {st.session_state['user']}</div>
            <div>v3.0</div>
        </div>
        <div style="text-align:center;font-size:0.7rem;color:#6c757d;margin-top:0.5rem;">
            {current_datetime}
        </div>
        """, unsafe_allow_html=True)


# Point d'entrée
if __name__ == "__main__":
    # S'assurer que les tables existent
    Base.metadata.create_all(bind=engine)
    main()