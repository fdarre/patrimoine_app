# ui/assets/__init__.py
"""
Point d'entrée principal pour l'interface de gestion des actifs
"""
import streamlit as st
from sqlalchemy.orm import Session

# Importer les modèles de base de données nécessaires
from database.models import Asset, Bank, Account
from utils.constants import ASSET_CATEGORIES, PRODUCT_TYPES

# Importer les fonctions des sous-modules
from .list_view import display_assets_table, display_assets_cards, display_assets_compact
from .detail_view import display_asset_details
from .add_form import show_add_asset_form
from .edit_form import show_edit_asset_form
from .sync_view import show_sync_options


def show_asset_management(db: Session, user_id: str):
    """
    Interface principale pour la gestion des actifs

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.header("Gestion des actifs", anchor=False)

    # Onglets principaux
    tab1, tab2, tab3 = st.tabs(["📋 Vue d'ensemble", "➕ Ajouter un actif", "🔄 Synchronisation"])

    with tab1:
        # Récupérer les données
        assets = db.query(Asset).filter(Asset.owner_id == user_id).all()
        banks = db.query(Bank).filter(Bank.owner_id == user_id).all()

        if not assets:
            st.info("Aucun actif n'a encore été ajouté.")
        else:
            # Interface de filtrage et affichage des actifs
            filtered_assets = apply_filters(db, assets, banks, user_id)

            # Sélection de la vue
            view_type = st.radio("Type d'affichage", ["Tableau", "Cartes", "Compact"], horizontal=True)

            # Afficher le nombre de résultats
            st.write(f"**{len(filtered_assets)}** actifs correspondent à vos critères")

            if filtered_assets:
                if view_type == "Tableau":
                    display_assets_table(db, filtered_assets)
                elif view_type == "Cartes":
                    display_assets_cards(db, filtered_assets)
                else:
                    display_assets_compact(db, filtered_assets)
            else:
                st.info("Aucun actif ne correspond aux filtres sélectionnés.")

            # Gestion des détails d'un actif sélectionné
            if 'view_asset_details' in st.session_state:
                display_asset_details(db, st.session_state['view_asset_details'])

            # Gestion de l'édition d'un actif
            if 'edit_asset' in st.session_state:
                show_edit_asset_form(db, st.session_state['edit_asset'], user_id)

    # Onglet d'ajout d'actif
    with tab2:
        show_add_asset_form(db, user_id)

    # Onglet de synchronisation
    with tab3:
        show_sync_options(db, user_id)


def apply_filters(db, assets, banks, user_id):
    """
    Applique les filtres de recherche et tri aux actifs

    Args:
        db: Session de base de données
        assets: Liste des actifs
        banks: Liste des banques
        user_id: ID de l'utilisateur

    Returns:
        Liste des actifs filtrés
    """
    # Interface de filtrage améliorée
    with st.expander("🔍 Filtres", expanded=True):
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

    # Appliquer les filtres et le tri
    return filter_and_sort_assets(db, assets, user_id, filter_bank, filter_account,
                                  filter_category, filter_product_type, search_query, sort_by)


def get_filtered_accounts(db, user_id, filter_bank):
    """
    Récupère les comptes filtrés par banque
    """
    if filter_bank != "Toutes les banques":
        return db.query(Account).filter(Account.bank_id == filter_bank).all()
    else:
        return db.query(Account).join(Bank).filter(Bank.owner_id == user_id).all()


def filter_and_sort_assets(db, assets, user_id, filter_bank, filter_account,
                           filter_category, filter_product_type, search_query, sort_by):
    """
    Filtre et trie les actifs selon les critères spécifiés
    """
    # Appliquer les filtres à la requête
    filtered_assets_query = db.query(Asset).filter(Asset.owner_id == user_id)

    if filter_bank != "Toutes les banques":
        bank_account_ids = [acc.id for acc in db.query(Account).filter(Account.bank_id == filter_bank).all()]
        filtered_assets_query = filtered_assets_query.filter(Asset.account_id.in_(bank_account_ids))

    if filter_account != "Tous les comptes":
        filtered_assets_query = filtered_assets_query.filter(Asset.account_id == filter_account)

    if filter_category != "Toutes les catégories":
        filtered_assets_query = filtered_assets_query.filter(Asset.categorie == filter_category)

    if filter_product_type != "Tous les types":
        filtered_assets_query = filtered_assets_query.filter(Asset.type_produit == filter_product_type)

    # Exécuter la requête
    filtered_assets = filtered_assets_query.all()

    # Appliquer la recherche textuelle
    if search_query:
        filtered_assets = [
            asset for asset in filtered_assets
            if search_query.lower() in asset.nom.lower() or
               (asset.isin and search_query.lower() in asset.isin.lower()) or
               (asset.notes and search_query.lower() in asset.notes.lower())
        ]

    # Appliquer le tri
    if sort_by == "Valeur ▼":
        filtered_assets.sort(key=lambda x: x.valeur_actuelle, reverse=True)
    elif sort_by == "Valeur ▲":
        filtered_assets.sort(key=lambda x: x.valeur_actuelle)
    elif sort_by == "Nom A-Z":
        filtered_assets.sort(key=lambda x: x.nom.lower())
    elif sort_by == "Nom Z-A":
        filtered_assets.sort(key=lambda x: x.nom.lower(), reverse=True)
    elif sort_by == "Performance ▼":
        filtered_assets.sort(
            key=lambda x: (x.valeur_actuelle - x.prix_de_revient) / x.prix_de_revient if x.prix_de_revient else 0,
            reverse=True)
    elif sort_by == "Performance ▲":
        filtered_assets.sort(
            key=lambda x: (x.valeur_actuelle - x.prix_de_revient) / x.prix_de_revient if x.prix_de_revient else 0)

    return filtered_assets


def show_asset_management(db: Session, user_id: str):
    """
    Interface principale pour la gestion des actifs

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.header("Gestion des actifs", anchor=False)

    # Onglets principaux
    tab1, tab2, tab3 = st.tabs(["📋 Vue d'ensemble", "➕ Ajouter un actif", "🔄 Synchronisation"])

    with tab1:
        # Récupérer les données
        assets = db.query(Asset).filter(Asset.owner_id == user_id).all()
        banks = db.query(Bank).filter(Bank.owner_id == user_id).all()

        if not assets:
            st.info("Aucun actif n'a encore été ajouté.")
        else:
            # Interface de filtrage et affichage des actifs
            filtered_assets = apply_filters(db, assets, banks, user_id)

            # Sélection de la vue
            view_type = st.radio("Type d'affichage", ["Tableau", "Cartes", "Compact"], horizontal=True)

            # Afficher le nombre de résultats
            st.write(f"**{len(filtered_assets)}** actifs correspondent à vos critères")

            if filtered_assets:
                if view_type == "Tableau":
                    display_assets_table(db, filtered_assets)
                elif view_type == "Cartes":
                    display_assets_cards(db, filtered_assets)
                else:
                    display_assets_compact(db, filtered_assets)
            else:
                st.info("Aucun actif ne correspond aux filtres sélectionnés.")

            # Gestion des détails d'un actif sélectionné
            if 'view_asset_details' in st.session_state:
                display_asset_details(db, st.session_state['view_asset_details'])

            # Gestion de l'édition d'un actif
            if 'edit_asset' in st.session_state:
                show_edit_asset_form(db, st.session_state['edit_asset'], user_id)

    # Onglet d'ajout d'actif
    with tab2:
        show_add_asset_form(db, user_id)

    # Onglet de synchronisation
    with tab3:
        show_sync_options(db, user_id)


def apply_filters(db, assets, banks, user_id):
    """
    Applique les filtres de recherche et tri aux actifs

    Args:
        db: Session de base de données
        assets: Liste des actifs
        banks: Liste des banques
        user_id: ID de l'utilisateur

    Returns:
        Liste des actifs filtrés
    """
    # Interface de filtrage améliorée
    with st.expander("🔍 Filtres", expanded=True):
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

    # Appliquer les filtres et le tri
    return filter_and_sort_assets(db, assets, user_id, filter_bank, filter_account,
                                  filter_category, filter_product_type, search_query, sort_by)


def get_filtered_accounts(db, user_id, filter_bank):
    """
    Récupère les comptes filtrés par banque
    """
    if filter_bank != "Toutes les banques":
        return db.query(Account).filter(Account.bank_id == filter_bank).all()
    else:
        return db.query(Account).join(Bank).filter(Bank.owner_id == user_id).all()


def filter_and_sort_assets(db, assets, user_id, filter_bank, filter_account,
                           filter_category, filter_product_type, search_query, sort_by):
    """
    Filtre et trie les actifs selon les critères spécifiés
    """
    # Appliquer les filtres à la requête
    filtered_assets_query = db.query(Asset).filter(Asset.owner_id == user_id)

    if filter_bank != "Toutes les banques":
        bank_account_ids = [acc.id for acc in db.query(Account).filter(Account.bank_id == filter_bank).all()]
        filtered_assets_query = filtered_assets_query.filter(Asset.account_id.in_(bank_account_ids))

    if filter_account != "Tous les comptes":
        filtered_assets_query = filtered_assets_query.filter(Asset.account_id == filter_account)

    if filter_category != "Toutes les catégories":
        filtered_assets_query = filtered_assets_query.filter(Asset.categorie == filter_category)

    if filter_product_type != "Tous les types":
        filtered_assets_query = filtered_assets_query.filter(Asset.type_produit == filter_product_type)

    # Exécuter la requête
    filtered_assets = filtered_assets_query.all()

    # Appliquer la recherche textuelle
    if search_query:
        filtered_assets = [
            asset for asset in filtered_assets
            if search_query.lower() in asset.nom.lower() or
               (asset.isin and search_query.lower() in asset.isin.lower()) or
               (asset.notes and search_query.lower() in asset.notes.lower())
        ]

    # Appliquer le tri
    if sort_by == "Valeur ▼":
        filtered_assets.sort(key=lambda x: x.valeur_actuelle, reverse=True)
    elif sort_by == "Valeur ▲":
        filtered_assets.sort(key=lambda x: x.valeur_actuelle)
    elif sort_by == "Nom A-Z":
        filtered_assets.sort(key=lambda x: x.nom.lower())
    elif sort_by == "Nom Z-A":
        filtered_assets.sort(key=lambda x: x.nom.lower(), reverse=True)
    elif sort_by == "Performance ▼":
        filtered_assets.sort(
            key=lambda x: (x.valeur_actuelle - x.prix_de_revient) / x.prix_de_revient if x.prix_de_revient else 0,
            reverse=True)
    elif sort_by == "Performance ▲":
        filtered_assets.sort(
            key=lambda x: (x.valeur_actuelle - x.prix_de_revient) / x.prix_de_revient if x.prix_de_revient else 0)

    return filtered_assets