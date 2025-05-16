"""
Interface améliorée pour la gestion des actifs
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import Bank, Account, Asset
from services.asset_service import AssetService
from services.data_service import DataService
from utils.constants import ASSET_CATEGORIES, PRODUCT_TYPES, CURRENCIES
from utils.calculations import get_default_geo_zones

def show_asset_management(db: Session, user_id: str):
    """
    Interface améliorée pour la gestion des actifs
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
                    if filter_bank != "Toutes les banques":
                        bank_accounts = db.query(Account).filter(Account.bank_id == filter_bank).all()
                        account_options = ["Tous les comptes"] + [acc.id for acc in bank_accounts]
                        account_format = lambda x: "Tous les comptes" if x == "Tous les comptes" else next(
                            (acc.libelle for acc in bank_accounts if acc.id == x), "")
                    else:
                        accounts = db.query(Account).join(Bank).filter(Bank.owner_id == user_id).all()
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
                filtered_assets.sort(key=lambda x: (x.valeur_actuelle - x.prix_de_revient) / x.prix_de_revient if x.prix_de_revient else 0, reverse=True)
            elif sort_by == "Performance ▲":
                filtered_assets.sort(key=lambda x: (x.valeur_actuelle - x.prix_de_revient) / x.prix_de_revient if x.prix_de_revient else 0)

            # Sélection de la vue
            view_type = st.radio("Type d'affichage", ["Tableau", "Cartes", "Compact"], horizontal=True)

            # Afficher le nombre de résultats
            st.write(f"**{len(filtered_assets)}** actifs correspondent à vos critères")

            if filtered_assets:
                if view_type == "Tableau":
                    # Affichage en tableau amélioré
                    display_assets_table(db, filtered_assets)
                elif view_type == "Cartes":
                    # Affichage en cartes
                    display_assets_cards(db, filtered_assets)
                else:
                    # Affichage compact
                    display_assets_compact(db, filtered_assets)
            else:
                st.info("Aucun actif ne correspond aux filtres sélectionnés.")

    # Les onglets "Ajouter un actif" et "Synchronisation" restent inchangés
    with tab2:
        # Code existant pour l'ajout d'actifs
        # On implémente la version améliorée du formulaire d'ajout ici
        show_add_asset_form(db, user_id)

    with tab3:
        # Code existant pour la synchronisation
        show_sync_options(db, user_id)

def display_assets_table(db, assets):
    """Affiche les actifs en mode tableau amélioré"""
    # Préparation des données
    data = []
    for asset in assets:
        # Récupérer le compte et la banque
        account = db.query(Account).filter(Account.id == asset.account_id).first()
        bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

        # Calculer la plus-value
        pv = asset.valeur_actuelle - asset.prix_de_revient
        pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
        pv_class = "positive" if pv >= 0 else "negative"

        # Créer une représentation visuelle de l'allocation
        allocation_html = ""
        if asset.allocation:
            for cat, pct in sorted(asset.allocation.items(), key=lambda x: x[1], reverse=True)[:3]:
                color = {
                    "actions": "#4e79a7",
                    "obligations": "#f28e2c",
                    "immobilier": "#e15759",
                    "crypto": "#76b7b2",
                    "metaux": "#59a14f",
                    "cash": "#edc949",
                    "autre": "#af7aa1"
                }.get(cat, "#bab0ab")
                allocation_html += f'<div style="display:inline-block;margin-right:4px;"><span style="background:{color};width:10px;height:10px;display:inline-block;margin-right:2px;"></span>{cat[:3].capitalize()} {pct}%</div>'

        # Mini indicateur de performance
        perf_indicator = f'<span class="{pv_class}-indicator" style="margin-left:5px;padding:0 3px;">{pv_percent:+.1f}%</span>'

        # Créer un badge pour le type de produit
        product_type_badge = f'<span style="background:#e9ecef;border-radius:3px;padding:1px 5px;font-size:12px;">{asset.type_produit}</span>'

        data.append({
            "ID": asset.id,
            "Nom": asset.nom,
            "Type": product_type_badge,
            "Valeur": f"{asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " "),
            "Performance": f'<span class="{pv_class}">{pv:,.2f} {asset.devise}</span>{perf_indicator}'.replace(",", " "),
            "Allocation": allocation_html,
            "Compte": f"{account.libelle} ({bank.nom})" if account and bank else "N/A",
            "Dernière MAJ": asset.date_maj
        })

    # Créer le DataFrame
    df = pd.DataFrame(data)

    # CSS pour le tableau amélioré
    st.markdown("""
    <style>
    .dataframe {
        border-collapse: collapse;
        width: 100%;
        border: 1px solid #ddd;
        font-size: 14px;
    }
    .dataframe th {
        background-color: #f8f9fa;
        color: #495057;
        text-align: left;
        padding: 12px 8px;
        border-bottom: 2px solid #dee2e6;
    }
    .dataframe td {
        border-bottom: 1px solid #dee2e6;
        padding: 10px 8px;
    }
    .dataframe tr:hover {
        background-color: rgba(0,0,0,0.03);
    }
    .positive {
        color: #28a745;
        font-weight: bold;
    }
    .negative {
        color: #dc3545;
        font-weight: bold;
    }
    .positive-indicator {
        background-color: rgba(40, 167, 69, 0.2);
        border-radius: 3px;
    }
    .negative-indicator {
        background-color: rgba(220, 53, 69, 0.2);
        border-radius: 3px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Afficher le tableau sans la colonne ID
    st.write(df.drop(columns=["ID"]).to_html(escape=False, index=False), unsafe_allow_html=True)

    # Section détails: permet de sélectionner un actif pour voir ses détails
    st.markdown("### 🔍 Détails d'un actif")
    selected_asset_id = st.selectbox(
        "Sélectionner un actif",
        options=[asset["ID"] for asset in data],
        format_func=lambda x: next((a["Nom"] for a in data if a["ID"] == x), "")
    )

    if selected_asset_id:
        display_asset_details(db, selected_asset_id)

def display_assets_cards(db, assets):
    """Affiche les actifs sous forme de cartes"""
    # Disposition en grille
    cols = st.columns(3)

    for i, asset in enumerate(assets):
        # Distribution cyclique dans les colonnes
        with cols[i % 3]:
            # Récupérer le compte et la banque
            account = db.query(Account).filter(Account.id == asset.account_id).first()
            bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

            # Calculer la plus-value
            pv = asset.valeur_actuelle - asset.prix_de_revient
            pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
            pv_class = "positive" if pv >= 0 else "negative"

            # Créer la carte avec le type de produit
            st.markdown(f"""
            <div style="border:1px solid #dee2e6;border-radius:5px;padding:10px;margin-bottom:15px;background-color:#fff;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <h3 style="margin-top:0;font-size:18px;">{asset.nom}</h3>
                    <span style="background:#e9ecef;border-radius:3px;padding:1px 5px;font-size:12px;">{asset.type_produit}</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                    <div><strong>Valeur:</strong> {asset.valeur_actuelle:,.2f} {asset.devise}</div>
                    <div class="{pv_class}">{pv_percent:+.1f}%</div>
                </div>
                <div style="margin-bottom:8px;font-size:12px;color:#6c757d;">
                    {account.libelle} | {bank.nom if bank else "N/A"}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Boutons d'action dans la carte
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Détails", key=f"details_{asset.id}"):
                    st.session_state['view_asset_details'] = asset.id
            with col2:
                if st.button("Modifier", key=f"edit_{asset.id}"):
                    st.session_state['edit_asset'] = asset.id

    # Affichage des détails si un actif est sélectionné
    if 'view_asset_details' in st.session_state:
        display_asset_details(db, st.session_state['view_asset_details'])

def display_assets_compact(db, assets):
    """Affiche les actifs en mode liste compacte"""
    total_value = sum(asset.valeur_actuelle for asset in assets)

    # Création d'une liste compacte
    for asset in assets:
        # Récupérer le compte et la banque
        account = db.query(Account).filter(Account.id == asset.account_id).first()
        bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

        # Calculer la plus-value
        pv = asset.valeur_actuelle - asset.prix_de_revient
        pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
        pv_class = "positive" if pv >= 0 else "negative"

        # Calculer le pourcentage du portefeuille
        portfolio_percent = (asset.valeur_actuelle / total_value * 100) if total_value > 0 else 0

        # Créer une barre de progression proportionnelle à la valeur
        progress_html = f'<div style="background:#f8f9fa;height:4px;width:100%;margin-top:3px;"><div style="background:#4e79a7;height:4px;width:{portfolio_percent}%;"></div></div>'

        # Créer la ligne compacte
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div style="padding:8px 0;border-bottom:1px solid #dee2e6;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <strong>{asset.nom}</strong>
                        <span style="background:#e9ecef;border-radius:3px;padding:1px 5px;font-size:11px;margin-left:5px;">{asset.type_produit}</span>
                    </div>
                    <div>{asset.valeur_actuelle:,.2f} {asset.devise}</div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:12px;color:#6c757d;">
                    <div>{account.libelle} | {bank.nom if bank else "N/A"}</div>
                    <div class="{pv_class}">{pv_percent:+.1f}%</div>
                </div>
                {progress_html}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.button("Détails", key=f"compact_details_{asset.id}"):
                st.session_state['view_asset_details'] = asset.id

    # Affichage des détails si un actif est sélectionné
    if 'view_asset_details' in st.session_state:
        display_asset_details(db, st.session_state['view_asset_details'])

def display_asset_details(db, asset_id):
    """Affiche les détails complets d'un actif"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        st.error("Actif introuvable.")
        return

    # Récupérer le compte et la banque
    account = db.query(Account).filter(Account.id == asset.account_id).first()
    bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

    # Afficher le fil d'ariane (breadcrumb)
    st.markdown(f"""
    <div style="margin-bottom:15px;font-size:14px;color:#6c757d;">
        {bank.nom if bank else "N/A"} > {account.libelle if account else "N/A"} > <strong>{asset.nom}</strong>
    </div>
    """, unsafe_allow_html=True)

    # En-tête avec les informations essentielles
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(asset.nom)
        st.markdown(f"""
        <div style="margin-bottom:10px;">
            <span style="background:#e9ecef;border-radius:3px;padding:2px 8px;font-size:14px;font-weight:bold;">{asset.type_produit.upper()}</span>
            {f'<span style="margin-left:10px;font-family:monospace;background:#f8f9fa;padding:2px 8px;border-radius:3px;">{asset.isin}</span>' if asset.isin else ''}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Calculer la plus-value
        pv = asset.valeur_actuelle - asset.prix_de_revient
        pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
        pv_class = "positive" if pv >= 0 else "negative"

        st.markdown(f"""
        <div style="text-align:right;">
            <div style="font-size:24px;font-weight:bold;">{asset.valeur_actuelle:,.2f} {asset.devise}</div>
            <div class="{pv_class}" style="font-size:16px;">{pv:+,.2f} {asset.devise} ({pv_percent:+.2f}%)</div>
        </div>
        """, unsafe_allow_html=True)

    # Onglets pour les différentes sections de détails
    detail_tabs = st.tabs(["📊 Allocations", "💰 Valorisation", "📋 Informations", "✏️ Édition"])

    with detail_tabs[0]:
        st.subheader("Allocation par catégorie")

        # Créer un graphique avec les allocations
        if asset.allocation:
            # Préparer les données
            categories = list(asset.allocation.keys())
            percentages = list(asset.allocation.values())

            # Créer le graphique
            fig, ax = plt.subplots(figsize=(8, 5))
            bars = ax.bar(categories, percentages, color=['#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1'])

            # Ajouter les pourcentages sur les barres
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{height:.1f}%',
                        ha='center', va='bottom', fontsize=10)

            ax.set_ylabel('Pourcentage (%)')
            ax.set_ylim(0, 100)
            ax.grid(axis='y', linestyle='--', alpha=0.7)

            st.pyplot(fig)

        # Répartition géographique
        st.subheader("Répartition géographique")

        if asset.geo_allocation:
            # Créer des onglets pour chaque catégorie d'allocation
            geo_tabs = st.tabs([cat.capitalize() for cat in asset.allocation.keys()])

            for i, (category, percentage) in enumerate(asset.allocation.items()):
                with geo_tabs[i]:
                    geo_data = asset.geo_allocation.get(category, {})

                    if geo_data:
                        # Créer un graphique en camembert
                        fig, ax = plt.subplots(figsize=(8, 5))

                        # Trier par valeur décroissante
                        sorted_geo = sorted(geo_data.items(), key=lambda x: x[1], reverse=True)
                        labels = [item[0].capitalize() for item in sorted_geo]
                        sizes = [item[1] for item in sorted_geo]

                        # Créer le camembert
                        wedges, texts, autotexts = ax.pie(
                            sizes,
                            labels=labels,
                            autopct='%1.1f%%',
                            startangle=90,
                            wedgeprops={'edgecolor': 'w', 'linewidth': 1}
                        )

                        # Améliorer la lisibilité
                        for text in texts:
                            text.set_fontsize(9)
                        for autotext in autotexts:
                            autotext.set_fontsize(9)
                            autotext.set_weight('bold')

                        ax.axis('equal')

                        st.pyplot(fig)
                    else:
                        st.info(f"Pas de répartition géographique définie pour {category}")

    with detail_tabs[1]:
        st.subheader("Données de valorisation")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Valeur actuelle", f"{asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " "))
            st.metric("Prix de revient", f"{asset.prix_de_revient:,.2f} {asset.devise}".replace(",", " "))

            if asset.devise != "EUR" and asset.exchange_rate:
                st.metric("Taux de change", f"1 {asset.devise} = {asset.exchange_rate:,.4f} EUR".replace(",", " "))
                if asset.value_eur:
                    st.metric("Valeur en EUR", f"{asset.value_eur:,.2f} EUR".replace(",", " "))

        with col2:
            # Plus-value
            pv = asset.valeur_actuelle - asset.prix_de_revient
            pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0

            st.metric("Plus-value",
                     f"{pv:,.2f} {asset.devise}".replace(",", " "),
                     f"{pv_percent:+.2f}%",
                     delta_color="normal" if pv >= 0 else "inverse")

            # Dates importantes
            st.write("**Date de mise à jour:**", asset.date_maj)
            if asset.last_price_sync:
                st.write("**Dernière synchro prix:**", asset.last_price_sync)
            if asset.last_rate_sync:
                st.write("**Dernière synchro taux:**", asset.last_rate_sync)

        # Ajouter un formulaire de mise à jour rapide
        st.subheader("Mise à jour rapide")
        col1, col2 = st.columns(2)
        with col1:
            new_price = st.number_input("Nouveau prix",
                                      min_value=0.0,
                                      value=float(asset.valeur_actuelle),
                                      format="%.2f")
        with col2:
            if st.button("Mettre à jour", key=f"update_price_{asset.id}"):
                # Code pour la mise à jour du prix
                if AssetService.update_manual_price(db, asset.id, new_price):
                    st.success("Prix mis à jour avec succès")
                    st.rerun()
                else:
                    st.error("Erreur lors de la mise à jour du prix")

    with detail_tabs[2]:
        st.subheader("Informations générales")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Type de produit:**", asset.type_produit)
            st.write("**Compte:**", f"{account.libelle} ({account.type})" if account else "N/A")
            st.write("**Banque:**", bank.nom if bank else "N/A")

            if asset.type_produit == "metal" and asset.ounces:
                st.write("**Onces:**", asset.ounces)

        with col2:
            st.write("**Catégorie principale:**", asset.categorie.capitalize())
            st.write("**Date d'ajout:**", asset.date_maj)
            st.write("**Devise:**", asset.devise)

        # Notes et tâches
        if asset.notes:
            st.subheader("Notes")
            st.markdown(f'<div style="background:#f8f9fa;padding:10px;border-radius:5px;">{asset.notes}</div>',
                       unsafe_allow_html=True)

        if asset.todo:
            st.subheader("Tâches à faire")
            st.markdown(f"""
            <div class="todo-card" style="background-color:#fff3cd;border-left:4px solid #ffc107;padding:1rem;border-radius:0.25rem;">
                {asset.todo}
            </div>
            """, unsafe_allow_html=True)

    with detail_tabs[3]:
        # Réutiliser le code existant pour l'édition
        if st.button("Modifier cet actif"):
            st.session_state[f'edit_asset_{asset.id}'] = True

        if f'edit_asset_{asset.id}' in st.session_state and st.session_state[f'edit_asset_{asset.id}']:
            # Récupérer le code de formulaire d'édition existant
            from ui.assets import show_asset_management as original_asset_management
            # Afficher le formulaire d'édition de l'actif avec le code existant
            st.info("Formulaire d'édition avancé de l'actif")
            # Ici on réutiliserait le code du formulaire d'édition existant

def show_add_asset_form(db, user_id):
    """
    Affiche un formulaire amélioré pour l'ajout d'actifs
    """
    st.subheader("Ajouter un nouvel actif")

    # Récupérer les comptes disponibles
    accounts = db.query(Account).join(Bank).filter(Bank.owner_id == user_id).all()

    if not accounts:
        st.warning("Veuillez d'abord ajouter des comptes avant d'ajouter des actifs.")
    else:
        # Interface à onglets pour un ajout plus intuitif
        form_tabs = st.tabs(["📝 Informations de base", "📊 Allocation", "🌍 Répartition géographique"])

        with form_tabs[0]:
            col1, col2 = st.columns(2)

            with col1:
                asset_name = st.text_input("Nom de l'actif", key="new_asset_name")
                asset_type = st.selectbox(
                    "Type de produit",
                    options=PRODUCT_TYPES,
                    key="new_asset_type",
                    help="Type de produit financier (ETF, action individuelle, etc.)"
                )
                asset_isin = st.text_input("Code ISIN (optionnel)",
                                         key="new_asset_isin",
                                         help="Pour les ETF, actions et obligations")

                # Champs spécifiques selon le type
                if asset_type == "metal":
                    asset_ounces = st.number_input("Quantité (onces)", min_value=0.0, value=1.0, format="%.3f")
                else:
                    asset_ounces = None

            with col2:
                # Sélection de banque et compte avec interface améliorée
                banks = db.query(Bank).filter(Bank.owner_id == user_id).all()

                asset_bank = st.selectbox(
                    "Banque",
                    options=[bank.id for bank in banks],
                    format_func=lambda x: next((f"{bank.nom}" for bank in banks if bank.id == x), ""),
                    key="new_asset_bank"
                )

                # Filtrer les comptes selon la banque sélectionnée
                bank_accounts = db.query(Account).filter(Account.bank_id == asset_bank).all()

                if bank_accounts:
                    asset_account = st.selectbox(
                        "Compte",
                        options=[acc.id for acc in bank_accounts],
                        format_func=lambda x: next((f"{acc.libelle}" for acc in bank_accounts if acc.id == x), ""),
                        key="new_asset_account"
                    )
                else:
                    st.warning(f"Aucun compte disponible pour cette banque.")
                    asset_account = None

                asset_value = st.number_input("Valeur actuelle",
                                        min_value=0.0,
                                        value=0.0,
                                        format="%.2f",
                                        key="new_asset_value")

                asset_cost = st.number_input("Prix de revient",
                                         min_value=0.0,
                                         value=0.0,
                                         format="%.2f",
                                         help="Laissez à 0 pour utiliser la valeur actuelle",
                                         key="new_asset_cost")

                asset_currency = st.selectbox(
                    "Devise",
                    options=CURRENCIES,
                    index=0,
                    key="new_asset_currency"
                )

            # Champs supplémentaires
            st.subheader("Informations additionnelles")
            asset_notes = st.text_area("Notes", key="new_asset_notes",
                                      help="Notes personnelles sur cet actif")
            asset_todo = st.text_area("Tâche à faire (optionnel)", key="new_asset_todo")

        with form_tabs[1]:
            st.subheader("Allocation par catégorie")
            st.info("Répartissez la valeur de l'actif entre les différentes catégories (total 100%)")

            # Variables pour stocker les allocations
            allocation = {}
            allocation_total = 0

            # Interface améliorée pour l'allocation avec barres de progression
            col1, col2 = st.columns(2)

            # Définition des couleurs par catégorie
            category_colors = {
                "actions": "#4e79a7",
                "obligations": "#f28e2c",
                "immobilier": "#e15759",
                "crypto": "#76b7b2",
                "metaux": "#59a14f",
                "cash": "#edc949",
                "autre": "#af7aa1"
            }

            # Première colonne: principaux types d'actifs
            with col1:
                for category in ["actions", "obligations", "immobilier", "cash"]:
                    percentage = st.slider(
                        f"{category.capitalize()} (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=0.0,  # Par défaut à 0
                        step=1.0,
                        key=f"new_asset_alloc_{category}"
                    )
                    if percentage > 0:
                        allocation[category] = percentage
                        allocation_total += percentage

                        # Afficher une barre de progression colorée pour cette catégorie
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;margin-bottom:8px;">
                            <div style="width:80px;">{category.capitalize()}</div>
                            <div style="background:#f8f9fa;height:8px;width:70%;margin:0 10px;">
                                <div style="background:{category_colors[category]};height:8px;width:{percentage}%;"></div>
                            </div>
                            <div>{percentage}%</div>
                        </div>
                        """, unsafe_allow_html=True)

            # Deuxième colonne: autres types d'actifs
            with col2:
                for category in ["crypto", "metaux", "autre"]:
                    percentage = st.slider(
                        f"{category.capitalize()} (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=0.0,  # Par défaut à 0
                        step=1.0,
                        key=f"new_asset_alloc_{category}"
                    )
                    if percentage > 0:
                        allocation[category] = percentage
                        allocation_total += percentage

                        # Afficher une barre de progression colorée pour cette catégorie
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;margin-bottom:8px;">
                            <div style="width:80px;">{category.capitalize()}</div>
                            <div style="background:#f8f9fa;height:8px;width:70%;margin:0 10px;">
                                <div style="background:{category_colors[category]};height:8px;width:{percentage}%;"></div>
                            </div>
                            <div>{percentage}%</div>
                        </div>
                        """, unsafe_allow_html=True)

            # Barre de progression pour visualiser le total
            st.markdown(f"""
            <div style="margin-top:20px;">
                <h4 style="margin-bottom:5px;">Total: {allocation_total}%</h4>
                <div style="background:#f8f9fa;height:10px;width:100%;border-radius:5px;">
                    <div style="background:{('#28a745' if allocation_total == 100 else '#ffc107' if allocation_total < 100 else '#dc3545')};height:10px;width:{min(allocation_total, 100)}%;border-radius:5px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Message de validation
            if allocation_total < 100:
                st.warning(f"Le total des allocations doit être de 100%. Actuellement: {allocation_total}%")
            elif allocation_total > 100:
                st.error(f"Le total des allocations ne doit pas dépasser 100%. Actuellement: {allocation_total}%")
            else:
                st.success("Allocation valide (100%)")

        with form_tabs[2]:
            st.subheader("Répartition géographique par catégorie")

            # Objet pour stocker les répartitions géographiques
            geo_allocation = {}
            all_geo_valid = True

            # Si aucune catégorie n'a été sélectionnée, afficher un message
            if not allocation:
                st.warning(
                    "Veuillez d'abord spécifier au moins une catégorie d'actif avec un pourcentage supérieur à 0%.")
            else:
                # Créer des onglets pour chaque catégorie avec allocation > 0
                geo_tabs = st.tabs([cat.capitalize() for cat in allocation.keys()])

                # Pour chaque catégorie, demander la répartition géographique
                for i, (category, alloc_pct) in enumerate(allocation.items()):
                    with geo_tabs[i]:
                        st.info(
                            f"Configuration de la répartition géographique pour la partie '{category.capitalize()}' ({alloc_pct}% de l'actif)")

                        # Obtenir une répartition par défaut selon la catégorie
                        default_geo = get_default_geo_zones(category)

                        # Variables pour stocker la répartition géographique
                        geo_zones = {}
                        geo_total = 0

                        # Interface améliorée avec régions groupées
                        geo_categories = {
                            "Marchés développés": ["amerique_nord", "europe_zone_euro", "europe_hors_zone_euro", "japon"],
                            "Marchés émergents": ["chine", "inde", "asie_developpee", "autres_emergents"],
                            "Global": ["global_non_classe"]
                        }

                        # Noms d'affichage pour les zones géographiques
                        geo_display_names = {
                            "amerique_nord": "Amérique du Nord",
                            "europe_zone_euro": "Europe zone euro",
                            "europe_hors_zone_euro": "Europe hors zone euro",
                            "japon": "Japon",
                            "chine": "Chine",
                            "inde": "Inde",
                            "asie_developpee": "Asie développée",
                            "autres_emergents": "Autres émergents",
                            "global_non_classe": "Global/Non classé"
                        }

                        for region_group, zones in geo_categories.items():
                            st.subheader(region_group)
                            # Utiliser des colonnes pour une meilleure disposition
                            if len(zones) > 1:
                                cols = st.columns(2)
                                for j, zone in enumerate(zones):
                                    with cols[j % 2]:
                                        pct = st.slider(
                                            f"{geo_display_names.get(zone, zone)}",
                                            min_value=0.0,
                                            max_value=100.0,
                                            value=float(default_geo.get(zone, 0.0)),
                                            step=1.0,
                                            key=f"new_asset_geo_{category}_{zone}"
                                        )
                                        if pct > 0:
                                            geo_zones[zone] = pct
                                            geo_total += pct
                            else:
                                zone = zones[0]
                                pct = st.slider(
                                    f"{geo_display_names.get(zone, zone)}",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=float(default_geo.get(zone, 0.0)),
                                    step=1.0,
                                    key=f"new_asset_geo_{category}_{zone}"
                                )
                                if pct > 0:
                                    geo_zones[zone] = pct
                                    geo_total += pct

                        # Visualisation du total
                        st.markdown(f"""
                        <div style="margin-top:20px;">
                            <h4 style="margin-bottom:5px;">Total: {geo_total}%</h4>
                            <div style="background:#f8f9fa;height:10px;width:100%;border-radius:5px;">
                                <div style="background:{('#28a745' if geo_total == 100 else '#ffc107' if geo_total < 100 else '#dc3545')};height:10px;width:{min(geo_total, 100)}%;border-radius:5px;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Message de validation
                        if geo_total < 100:
                            st.warning(f"Le total de la répartition géographique pour '{category}' doit être de 100%. Actuellement: {geo_total}%")
                            all_geo_valid = False
                        elif geo_total > 100:
                            st.error(f"Le total de la répartition géographique pour '{category}' ne doit pas dépasser 100%. Actuellement: {geo_total}%")
                            all_geo_valid = False
                        else:
                            st.success(f"Répartition géographique pour '{category}' valide (100%)")

                        # Enregistrer la répartition géographique pour cette catégorie
                        geo_allocation[category] = geo_zones

        # Bouton d'ajout d'actif
        st.subheader("Validation")

        # Vérifier si toutes les conditions sont remplies
        form_valid = (
            asset_name and
            asset_account and
            asset_value > 0 and
            allocation_total == 100 and
            all_geo_valid
        )

        # Afficher un message récapitulatif avant validation
        if form_valid:
            st.success("Toutes les informations sont valides. Vous pouvez ajouter l'actif.")
        else:
            if not asset_name:
                st.warning("Le nom de l'actif est obligatoire.")
            if not asset_account:
                st.warning("Veuillez sélectionner un compte.")
            if asset_value <= 0:
                st.warning("La valeur actuelle doit être supérieure à 0.")
            if allocation_total != 100:
                st.warning(f"Le total des allocations doit être de 100% (actuellement: {allocation_total}%).")
            if not all_geo_valid:
                st.warning("Toutes les répartitions géographiques doivent totaliser 100%.")

        # Styliser le bouton selon l'état de validité du formulaire
        btn_style = "background-color:#28a745;color:white;" if form_valid else "background-color:#6c757d;color:white;"

        # Bouton d'ajout d'actif
        st.markdown(f"""
        <style>
        div.stButton > button {{
            width: 100%;
            height: 3em;
            {btn_style}
        }}
        </style>
        """, unsafe_allow_html=True)

        submit_button = st.button("Ajouter l'actif", key="btn_add_asset", disabled=not form_valid)

        if submit_button:
            try:
                # Utiliser le prix de revient si spécifié, sinon utiliser la valeur actuelle
                prix_de_revient = asset_cost if asset_cost > 0 else asset_value

                # Ajouter l'actif
                new_asset = AssetService.add_asset(
                    db=db,
                    user_id=user_id,
                    nom=asset_name,
                    compte_id=asset_account,
                    type_produit=asset_type,
                    allocation=allocation,
                    geo_allocation=geo_allocation,
                    valeur_actuelle=asset_value,
                    prix_de_revient=prix_de_revient,
                    devise=asset_currency,
                    notes=asset_notes,
                    todo=asset_todo,
                    isin=asset_isin if asset_isin else None,
                    ounces=asset_ounces if asset_type == "metal" else None
                )

                if new_asset:
                    # Mettre à jour l'historique
                    DataService.record_history_entry(db, user_id)
                    st.success(f"Actif '{asset_name}' ajouté avec succès.")
                    st.rerun()
                else:
                    st.error("Erreur lors de l'ajout de l'actif.")
            except ValueError as e:
                st.error(f"Les valeurs numériques sont invalides: {str(e)}")
            except Exception as e:
                st.error(f"Erreur inattendue: {str(e)}")

def show_sync_options(db, user_id):
    """Affiche les options de synchronisation améliorées"""
    st.subheader("Synchronisation automatique")

    # Statistiques globales
    stats_col1, stats_col2, stats_col3 = st.columns(3)

    # Compter les actifs avec ISIN, devises étrangères et métaux
    isin_count = db.query(Asset).filter(Asset.owner_id == user_id, Asset.isin != None).count()
    forex_count = db.query(Asset).filter(Asset.owner_id == user_id, Asset.devise != "EUR").count()
    metal_count = db.query(Asset).filter(Asset.owner_id == user_id, Asset.type_produit == "metal").count()

    with stats_col1:
        st.metric("Actifs avec ISIN", isin_count)
    with stats_col2:
        st.metric("Actifs en devise étrangère", forex_count)
    with stats_col3:
        st.metric("Métaux précieux", metal_count)

    # Interface de synchronisation globale avec des cartes
    st.markdown("""
    <style>
    .sync-card {
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #fff;
    }
    .sync-card h3 {
        margin-top: 0;
        font-size: 18px;
    }
    .sync-card p {
        color: #6c757d;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="sync-card">
            <h3>💱 Taux de change</h3>
            <p>Synchronise les taux de change pour tous les actifs en devise étrangère.</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Synchroniser tous les taux de change", disabled=forex_count == 0):
            with st.spinner("Synchronisation des taux de change en cours..."):
                updated_count = AssetService.sync_currency_rates(db)
                if updated_count > 0:
                    st.success(f"{updated_count} actif(s) mis à jour avec succès")
                    # Mettre à jour l'historique
                    DataService.record_history_entry(db, user_id)
                else:
                    st.info("Aucun actif à mettre à jour ou erreur lors de la synchronisation")

    with col2:
        st.markdown("""
        <div class="sync-card">
            <h3>📈 Prix par ISIN</h3>
            <p>Synchronise les prix via Yahoo Finance pour tous les actifs avec un code ISIN.</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Synchroniser tous les prix via ISIN", disabled=isin_count == 0):
            with st.spinner("Synchronisation des prix via ISIN en cours..."):
                updated_count = AssetService.sync_price_by_isin(db)
                if updated_count > 0:
                    st.success(f"{updated_count} actif(s) mis à jour avec succès")
                    # Mettre à jour l'historique
                    DataService.record_history_entry(db, user_id)
                else:
                    st.info("Aucun actif avec un ISIN à mettre à jour ou erreur lors de la synchronisation")

    # Interface de synchronisation des métaux précieux
    st.markdown("""
    <div class="sync-card">
        <h3>🥇 Métaux précieux</h3>
        <p>Synchronise les prix des actifs de type métal précieux (or, argent, platine, palladium).</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Synchroniser tous les prix des métaux précieux", disabled=metal_count == 0):
        with st.spinner("Synchronisation des prix des métaux précieux en cours..."):
            updated_count = AssetService.sync_metal_prices(db)
            if updated_count > 0:
                st.success(f"{updated_count} actif(s) métaux précieux mis à jour avec succès")
                # Mettre à jour l'historique
                DataService.record_history_entry(db, user_id)
            else:
                st.info("Aucun actif métal à mettre à jour ou erreur lors de la synchronisation")

    # Synchronisation complète
    st.markdown("""
    <div class="sync-card" style="background-color:#e7f5ff;">
        <h3>🔄 Synchronisation complète</h3>
        <p>Lance une synchronisation de tous les types de données (prix, taux de change, métaux).</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Synchronisation complète"):
        with st.spinner("Synchronisation complète en cours..."):
            # Synchroniser les taux de change
            forex_updated = AssetService.sync_currency_rates(db) if forex_count > 0 else 0

            # Synchroniser les prix via ISIN
            isin_updated = AssetService.sync_price_by_isin(db) if isin_count > 0 else 0

            # Synchroniser les métaux précieux
            metals_updated = AssetService.sync_metal_prices(db) if metal_count > 0 else 0

            # Mettre à jour l'historique si au moins un actif a été mis à jour
            if forex_updated > 0 or isin_updated > 0 or metals_updated > 0:
                DataService.record_history_entry(db, user_id)
                st.success(f"Synchronisation complète terminée avec succès!\n- {forex_updated} taux de change\n- {isin_updated} prix via ISIN\n- {metals_updated} métaux précieux")
            else:
                st.info("Aucun actif mis à jour lors de la synchronisation complète.")

    # Table des actifs avec leur dernière synchronisation
    st.subheader("État de synchronisation des actifs")

    sync_assets = db.query(Asset).filter(Asset.owner_id == user_id).all()

    if sync_assets:
        # Ajouter une barre de recherche
        search_sync = st.text_input("🔎 Rechercher", placeholder="Nom d'actif, ISIN, erreur...")

        # Filtrer les actifs selon la recherche
        if search_sync:
            sync_assets = [
                asset for asset in sync_assets
                if search_sync.lower() in asset.nom.lower() or
                   (asset.isin and search_sync.lower() in asset.isin.lower()) or
                   (asset.sync_error and search_sync.lower() in asset.sync_error.lower())
            ]

        # Ajouter des options de filtrage par statut de synchronisation
        status_options = ["Tous les actifs", "Avec erreurs", "Synchronisés récemment", "Jamais synchronisés"]
        status_filter = st.radio("Filtrer par statut", status_options, horizontal=True)

        if status_filter == "Avec erreurs":
            sync_assets = [asset for asset in sync_assets if asset.sync_error]
        elif status_filter == "Synchronisés récemment":
            sync_assets = [asset for asset in sync_assets if asset.last_price_sync or asset.last_rate_sync]
        elif status_filter == "Jamais synchronisés":
            sync_assets = [asset for asset in sync_assets if not asset.last_price_sync and not asset.last_rate_sync]

        # Préparer les données pour le tableau
        sync_data = []
        for asset in sync_assets:
            last_price_sync = asset.last_price_sync.strftime(
                "%Y-%m-%d %H:%M") if asset.last_price_sync else "Jamais"
            last_rate_sync = asset.last_rate_sync.strftime("%Y-%m-%d %H:%M") if asset.last_rate_sync else "Jamais"

            # Définir le statut visuel
            if asset.sync_error:
                status_html = '<span style="color:#dc3545;">⚠️ Erreur</span>'
            elif not asset.last_price_sync and not asset.last_rate_sync:
                status_html = '<span style="color:#6c757d;">📅 Jamais</span>'
            else:
                status_html = '<span style="color:#28a745;">✓ Synchronisé</span>'

            sync_data.append({
                "ID": asset.id,
                "Nom": asset.nom,
                "ISIN": asset.isin or "-",
                "Devise": asset.devise,
                "Dernier prix": last_price_sync,
                "Dernier taux": last_rate_sync,
                "Statut": status_html,
                "Erreur": asset.sync_error or "-"
            })

        # Créer le DataFrame
        sync_df = pd.DataFrame(sync_data)

        # Afficher le tableau avec les options de tri
        st.write(sync_df.drop(columns=["ID"]).to_html(escape=False, index=False), unsafe_allow_html=True)

        # Sélection d'un actif pour synchronisation individuelle
        st.subheader("Synchronisation individuelle")
        selected_sync_id = st.selectbox(
            "Sélectionner un actif à synchroniser",
            options=[a["ID"] for a in sync_data],
            format_func=lambda x: next((a["Nom"] for a in sync_data if a["ID"] == x), "")
        )

        if selected_sync_id:
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Synchroniser prix (ISIN)", key=f"sync_isin_{selected_sync_id}"):
                    with st.spinner("Synchronisation du prix via ISIN en cours..."):
                        result = AssetService.sync_price_by_isin(db, selected_sync_id)
                        if result == 1:
                            st.success("Prix synchronisé avec succès")
                            st.rerun()
                        else:
                            st.error("Erreur lors de la synchronisation du prix")

            with col2:
                if st.button("Synchroniser taux de change", key=f"sync_rate_{selected_sync_id}"):
                    with st.spinner("Synchronisation du taux de change en cours..."):
                        result = AssetService.sync_currency_rates(db, selected_sync_id)
                        if result == 1:
                            st.success("Taux de change synchronisé avec succès")
                            st.rerun()
                        else:
                            st.error("Erreur lors de la synchronisation du taux de change")

            with col3:
                if st.button("Synchroniser métal précieux", key=f"sync_metal_{selected_sync_id}"):
                    with st.spinner("Synchronisation du prix du métal en cours..."):
                        result = AssetService.sync_metal_prices(db, selected_sync_id)
                        if result == 1:
                            st.success("Prix du métal synchronisé avec succès")
                            st.rerun()
                        else:
                            st.error("Erreur lors de la synchronisation du prix du métal")
    else:
        st.info("Aucun actif disponible")