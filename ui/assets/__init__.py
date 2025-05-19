# ui/assets/__init__.py
"""
Point d'entrée principal pour l'interface de gestion des actifs
"""
import streamlit as st
from sqlalchemy import func, or_

# Imports de l'application
from config.app_config import ASSET_CATEGORIES, PRODUCT_TYPES
from database.db_config import get_db_session  # Utilisation du gestionnaire de contexte
# Importer les modèles de base de données nécessaires
from database.models import Asset, Bank, Account
from utils.session_manager import session_manager  # Utilisation du gestionnaire de session
from .add_form import show_add_asset_form
from .detail_view import display_asset_details
from .edit_form import show_edit_asset_form
# Importer les fonctions des sous-modules - Modifier cet import pour inclure la nouvelle fonction
from .list_view import display_assets_table_with_actions
from .sync_view import show_sync_options


def show_asset_management():
    """
    Interface principale pour la gestion des actifs
    """
    # Récupérer l'ID utilisateur depuis le gestionnaire de session
    user_id = session_manager.get("user_id")

    if not user_id:
        st.error("Utilisateur non authentifié")
        return

    st.header("Gestion des actifs", anchor=False)

    # Onglets principaux
    tab1, tab2, tab3 = st.tabs(["📋 Vue d'ensemble", "➕ Ajouter un actif", "🔄 Synchronisation"])

    # Utiliser le gestionnaire de contexte pour la session DB
    with get_db_session() as db:
        with tab1:
            # OPTIMISATION: Ne récupérer que le nombre d'actifs d'abord
            asset_count = db.query(func.count(Asset.id)).filter(Asset.owner_id == user_id).scalar() or 0
            bank_count = db.query(func.count(Bank.id)).filter(Bank.owner_id == user_id).scalar() or 0

            if asset_count == 0:
                st.info("Aucun actif n'a encore été ajouté.")
            else:
                # Interface de filtrage et affichage des actifs
                # Au lieu de récupérer tous les actifs d'abord, on utilise une requête filtrée
                filtered_query = build_filtered_query(db, user_id)

                # Exécute la requête seulement maintenant, après tous les filtres appliqués
                filtered_assets = filtered_query.all()

                # Afficher le nombre de résultats
                st.write(f"**{len(filtered_assets)}** actifs correspondent à vos critères")

                if filtered_assets:
                    # Utiliser notre nouvelle fonction avec options de modification/suppression
                    display_assets_table_with_actions(db, filtered_assets, user_id)
                else:
                    st.info("Aucun actif ne correspond aux filtres sélectionnés.")

                # Gestion de l'édition d'un actif
                if session_manager.get('edit_asset'):
                    show_edit_asset_form(db, session_manager.get('edit_asset'), user_id)

        # Onglet d'ajout d'actif
        with tab2:
            show_add_asset_form(db, user_id)

        # Onglet de synchronisation
        with tab3:
            show_sync_options(db, user_id)


def build_filtered_query(db, user_id):
    """
    Construit une requête filtrée pour les actifs selon les critères de l'utilisateur

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur

    Returns:
        Requête SQLAlchemy filtrée
    """
    # Interface de filtrage améliorée
    with st.expander("🔍 Filtres", expanded=True):
        # Récupérer les banques une seule fois
        banks = db.query(Bank).filter(Bank.owner_id == user_id).all()

        col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.5, 1])

        with col1:
            filter_bank = st.selectbox(
                "Banque",
                options=["Toutes les banques"] + [bank.id for bank in banks],
                format_func=lambda x: "Toutes les banques" if x == "Toutes les banques" else
                next((bank.nom for bank in banks if bank.id == x), ""),
                key="asset_filter_bank"
            )

        with col2:
            # Filtrer les comptes selon la banque sélectionnée
            accounts = get_filtered_accounts(db, user_id, filter_bank)
            account_options = ["Tous les comptes"] + [acc.id for acc in accounts]
            account_format = lambda x: "Tous les comptes" if x == "Tous les comptes" else next(
                (acc.libelle for acc in accounts if acc.id == x), "")

            filter_account = st.selectbox(
                "Compte",
                options=account_options,
                format_func=account_format,
                key="asset_filter_account"
            )

        with col3:
            # Utilisateur peut filtrer soit par catégorie patrimoniale soit par type de produit
            filter_type = st.radio("Filtrer par", ["Catégorie", "Type de produit"], horizontal=True)

            if filter_type == "Catégorie":
                filter_category = st.selectbox(
                    "Catégorie",
                    options=["Toutes les catégories"] + ASSET_CATEGORIES,
                    format_func=lambda x: x.capitalize() if x != "Toutes les catégories" else x,
                    key="asset_filter_category"
                )
                filter_product_type = "Tous les types"
            else:
                filter_category = "Toutes les catégories"
                filter_product_type = st.selectbox(
                    "Type de produit",
                    options=["Tous les types"] + PRODUCT_TYPES,
                    format_func=lambda x: x.capitalize() if x != "Tous les types" else x,
                    key="asset_filter_product"
                )

        with col4:
            # Ajouter une option de tri
            sort_by = st.selectbox(
                "Trier par",
                options=["Valeur ▼", "Valeur ▲", "Nom A-Z", "Nom Z-A", "Performance ▼", "Performance ▲"],
                key="asset_sort_by"
            )

    # Interface de recherche
    search_query = st.text_input("🔎 Rechercher un actif", placeholder="Nom d'actif, ISIN, description...")

    # OPTIMISATION: Construire et exécuter une requête SQL optimisée
    return filter_and_sort_assets(db, user_id, filter_bank, filter_account,
                                  filter_category, filter_product_type, search_query, sort_by)


def get_filtered_accounts(db, user_id, filter_bank):
    """
    Récupère les comptes filtrés par banque de manière optimisée
    """
    if filter_bank != "Toutes les banques":
        # OPTIMISATION: Ajouter un index sur bank_id pour cette requête
        return db.query(Account).filter(Account.bank_id == filter_bank).all()
    else:
        # OPTIMISATION: Utiliser une jointure pour récupérer seulement les comptes de l'utilisateur
        return db.query(Account).join(Bank).filter(Bank.owner_id == user_id).all()


def filter_and_sort_assets(db, user_id, filter_bank, filter_account,
                           filter_category, filter_product_type, search_query, sort_by):
    """
    Filtre et trie les actifs selon les critères spécifiés au niveau SQL

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
        filter_bank: Filtre par banque
        filter_account: Filtre par compte
        filter_category: Filtre par catégorie
        filter_product_type: Filtre par type de produit
        search_query: Texte de recherche
        sort_by: Critère de tri

    Returns:
        Requête SQLAlchemy filtrée et triée
    """
    # OPTIMISATION: Eager loading pour charger les relations en une seule requête
    query = db.query(Asset).filter(Asset.owner_id == user_id)

    # OPTIMISATION: Appliquer les filtres au niveau SQL
    if filter_bank != "Toutes les banques":
        # Jointure optimisée au lieu de sous-requêtes
        query = query.join(Account, Asset.account_id == Account.id)
        query = query.filter(Account.bank_id == filter_bank)

    if filter_account != "Tous les comptes":
        query = query.filter(Asset.account_id == filter_account)

    if filter_product_type != "Tous les types":
        query = query.filter(Asset.type_produit == filter_product_type)

    # OPTIMISATION: Filtrage sur JSON pour les catégories en SQLite
    if filter_category != "Toutes les catégories":
        # Pour SQLite, utiliser json_extract
        query = query.filter(func.json_extract(Asset.allocation, f'$.{filter_category}').isnot(None))

    # OPTIMISATION: Filtrage par recherche textuelle au niveau SQL
    if search_query:
        search_pattern = f"%{search_query.lower()}%"
        query = query.filter(
            or_(
                func.lower(Asset.nom).like(search_pattern),
                func.lower(Asset.isin or '').like(search_pattern),
                func.lower(Asset.notes or '').like(search_pattern)
            )
        )

    # OPTIMISATION: Tri au niveau SQL
    if sort_by == "Valeur ▼":
        query = query.order_by(Asset.valeur_actuelle.desc())
    elif sort_by == "Valeur ▲":
        query = query.order_by(Asset.valeur_actuelle)
    elif sort_by == "Nom A-Z":
        query = query.order_by(func.lower(Asset.nom))
    elif sort_by == "Nom Z-A":
        query = query.order_by(func.lower(Asset.nom).desc())
    # Pour le tri par performance, il faudra encore le faire en Python car c'est un calcul complexe
    elif sort_by in ["Performance ▼", "Performance ▲"]:
        # Ce tri sera fait en Python après récupération des résultats
        pass

    return query