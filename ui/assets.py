"""
Interface de gestion des actifs, incluant les actifs composites
"""

import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from database.models import Bank, Account, Asset
from services.asset_service import AssetService
from services.data_service import DataService
from utils.constants import ACCOUNT_TYPES, PRODUCT_TYPES, ASSET_CATEGORIES, GEO_ZONES, CURRENCIES
from utils.calculations import get_default_geo_zones, is_circular_reference

def show_asset_management(db: Session, user_id: str):
    """
    Affiche l'interface de gestion des actifs

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.header("Gestion des actifs", anchor=False)

    # Onglets pour les différentes fonctions de gestion d'actifs
    tab1, tab2 = st.tabs(["Liste des actifs", "Ajouter un actif"])

    with tab1:
        st.subheader("Liste de tous les actifs")

        # Récupérer les actifs de l'utilisateur
        assets = db.query(Asset).filter(Asset.owner_id == user_id).all()

        if not assets:
            st.info("Aucun actif n'a encore été ajouté.")
        else:
            # Récupérer les banques et comptes de l'utilisateur pour le filtrage
            banks = db.query(Bank).filter(Bank.owner_id == user_id).all()

            # Contrôles de filtrage
            col1, col2, col3 = st.columns(3)

            with col1:
                filter_bank = st.selectbox(
                    "Filtrer par banque",
                    options=["Toutes les banques"] + [bank.id for bank in banks],
                    format_func=lambda x: "Toutes les banques" if x == "Toutes les banques" else
                               next((bank.nom for bank in banks if bank.id == x), ""),
                    key="asset_filter_bank"
                )

            with col2:
                if filter_bank != "Toutes les banques":
                    # Obtenir les comptes pour la banque sélectionnée
                    bank_accounts = db.query(Account).filter(Account.bank_id == filter_bank).all()

                    if bank_accounts:
                        filter_account = st.selectbox(
                            "Filtrer par compte",
                            options=["Tous les comptes"] + [acc.id for acc in bank_accounts],
                            format_func=lambda x: "Tous les comptes" if x == "Tous les comptes" else
                                       next((acc.libelle for acc in bank_accounts if acc.id == x), ""),
                            key="asset_filter_account"
                        )
                    else:
                        filter_account = "Tous les comptes"
                        st.info("Aucun compte pour cette banque.")
                else:
                    filter_account = "Tous les comptes"

            with col3:
                filter_category = st.selectbox(
                    "Filtrer par catégorie",
                    options=["Toutes les catégories"] + ASSET_CATEGORIES,
                    key="asset_filter_category"
                )

            # Appliquer les filtres
            filtered_assets = db.query(Asset).filter(Asset.owner_id == user_id)

            if filter_bank != "Toutes les banques":
                # Obtenir les IDs des comptes de cette banque
                bank_account_ids = [acc.id for acc in db.query(Account).filter(Account.bank_id == filter_bank).all()]
                filtered_assets = filtered_assets.filter(Asset.account_id.in_(bank_account_ids))

            if filter_account != "Tous les comptes":
                filtered_assets = filtered_assets.filter(Asset.account_id == filter_account)

            if filter_category != "Toutes les catégories":
                # Filtrage par catégorie (SQL JSON filtering technique may vary by DB)
                # This is a simplified approach, actual implementation depends on your DB's JSON capabilities
                filtered_assets = filtered_assets.filter(Asset.categorie == filter_category)

            # Exécuter la requête
            filtered_assets = filtered_assets.all()

            # Afficher les actifs filtrés
            if filtered_assets:
                # Utiliser notre service pour créer un DataFrame avec les allocations
                assets_df = AssetService.get_assets_dataframe(
                    db,
                    user_id,
                    account_id=filter_account if filter_account != "Tous les comptes" else None,
                    category=filter_category if filter_category != "Toutes les catégories" else None,
                    bank_id=filter_bank if filter_bank != "Toutes les banques" else None
                )

                st.dataframe(assets_df.drop(columns=["ID"]) if "ID" in assets_df.columns else assets_df,
                             use_container_width=True)

                # Sélection d'un actif pour détails
                selected_asset_id = st.selectbox(
                    "Sélectionner un actif pour détails",
                    options=[asset.id for asset in filtered_assets],
                    format_func=lambda x: next((a.nom for a in filtered_assets if a.id == x), "")
                )

                if selected_asset_id:
                    asset = AssetService.find_asset_by_id(db, selected_asset_id)

                    if asset:
                        with st.expander("Détails de l'actif", expanded=True):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.write("**Nom:**", asset.nom)
                                st.write("**Type:**", asset.type_produit)

                                # Afficher les allocations par catégorie
                                st.markdown("**Allocation par catégorie:**")
                                for category, percentage in asset.allocation.items():
                                    st.markdown(f"- {category.capitalize()}: {percentage}%")

                                # Récupérer les informations du compte et de la banque
                                account = db.query(Account).filter(Account.id == asset.account_id).first()
                                bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

                                st.write("**Compte:**", account.libelle if account else "N/A")
                                st.write("**Date de mise à jour:**", asset.date_maj)
                                if asset.notes:
                                    st.write("**Notes:**", asset.notes)

                            with col2:
                                st.write("**Valeur actuelle:**",
                                         f"{asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " "))
                                st.write("**Prix de revient:**",
                                         f"{asset.prix_de_revient:,.2f} {asset.devise}".replace(",", " "))

                                pv = asset.valeur_actuelle - asset.prix_de_revient
                                pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
                                pv_class = "positive" if pv >= 0 else "negative"
                                st.markdown(
                                    f"""**Plus-value:** <span class="{pv_class}">{pv:,.2f} {asset.devise} ({pv_percent:.2f}%)</span>""".replace(
                                        ",", " "), unsafe_allow_html=True)

                            # Afficher les tâches
                            if asset.todo:
                                st.markdown(f"""
                                <div class="todo-card">
                                <strong>Tâche à faire:</strong> {asset.todo}
                                </div>
                                """, unsafe_allow_html=True)

                            # Afficher les composants si c'est un actif composite
                            if asset.composants:
                                st.subheader("Composition de l'actif")

                                component_data = []
                                for component in asset.composants:
                                    component_asset = AssetService.find_asset_by_id(db, component["asset_id"])
                                    if component_asset:
                                        component_data.append({
                                            "ID": component_asset.id,
                                            "Nom": component_asset.nom,
                                            "Pourcentage": f"{component['percentage']}%",
                                            "Valeur": f"{component_asset.valeur_actuelle * component['percentage'] / 100:,.2f} {component_asset.devise}".replace(
                                                ",", " "),
                                            "Catégorie": component_asset.categorie.capitalize(),
                                            "Type": component_asset.type_produit
                                        })

                                if component_data:
                                    component_df = pd.DataFrame(component_data)
                                    st.markdown(
                                        '<div class="composite-header">Actif composite composé des éléments suivants:</div>',
                                        unsafe_allow_html=True)
                                    st.dataframe(component_df.drop(columns=["ID"]) if "ID" in component_df.columns else component_df)

                                    # Afficher le pourcentage restant directement alloué
                                    components_total = sum(comp.get("percentage", 0) for comp in asset.composants)
                                    direct_percentage = 100 - components_total
                                    if direct_percentage > 0:
                                        st.info(
                                            f"{direct_percentage:.2f}% de l'actif est alloué directement selon l'allocation définie.")

                                    # Si l'actif a des composants, afficher l'allocation effective calculée
                                    st.subheader("Allocation effective (incluant les composants)")
                                    effective_allocation = AssetService.calculate_effective_allocation(db, asset.id)
                                    for category, percentage in sorted(effective_allocation.items(), key=lambda x: x[1],
                                                                       reverse=True):
                                        if percentage > 0:
                                            st.markdown(f"- {category.capitalize()}: {percentage:.2f}%")

                            # Afficher la répartition géographique par catégorie
                            st.subheader("Répartition géographique par catégorie")

                            # Utiliser des onglets pour chaque catégorie
                            if asset.allocation:
                                geo_tabs = st.tabs([cat.capitalize() for cat in asset.allocation.keys()])

                                for i, (category, percentage) in enumerate(asset.allocation.items()):
                                    with geo_tabs[i]:
                                        # Afficher le pourcentage de cette catégorie
                                        st.info(
                                            f"Cette catégorie représente {percentage}% de l'actif, soit {asset.valeur_actuelle * percentage / 100:,.2f} {asset.devise}".replace(
                                                ",", " "))

                                        # Obtenir la répartition géographique effective pour cette catégorie
                                        if asset.composants:
                                            effective_geo = AssetService.calculate_effective_geo_allocation(db, asset.id, category)
                                            geo_zones = effective_geo.get(category, {})
                                            st.success("Répartition géographique effective (incluant les composants):")
                                        else:
                                            # Obtenir la répartition géographique pour cette catégorie
                                            geo_zones = asset.geo_allocation.get(category, {})

                                        if geo_zones:
                                            # Afficher un tableau
                                            geo_data = []
                                            for zone, zone_pct in sorted(geo_zones.items(), key=lambda x: x[1],
                                                                         reverse=True):
                                                geo_data.append([zone.capitalize(), f"{zone_pct:.2f}%"])

                                            geo_df = pd.DataFrame(geo_data, columns=["Zone", "Pourcentage"])
                                            st.dataframe(geo_df, use_container_width=True)
                                        else:
                                            st.warning(f"Aucune répartition géographique définie pour {category}")

                            # Actions pour modifier/supprimer
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                if st.button("Modifier cet actif", key=f"btn_edit_asset_{selected_asset_id}"):
                                    st.session_state[f'edit_asset_{selected_asset_id}'] = True
                                    st.session_state[f'edit_components_{selected_asset_id}'] = False

                            with col2:
                                if st.button("Gérer les composants", key=f"btn_components_{selected_asset_id}"):
                                    st.session_state[f'edit_asset_{selected_asset_id}'] = False
                                    st.session_state[f'edit_components_{selected_asset_id}'] = True

                            with col3:
                                # Vérifier si l'actif est utilisé comme composant
                                is_used = AssetService.is_used_as_component(db, selected_asset_id)

                                if is_used:
                                    st.warning(
                                        "Cet actif est utilisé comme composant dans d'autres actifs et ne peut pas être supprimé.")
                                else:
                                    if st.button("Supprimer cet actif", key=f"btn_delete_asset_{selected_asset_id}"):
                                        if AssetService.delete_asset(db, selected_asset_id):
                                            # Mettre à jour l'historique
                                            DataService.record_history_entry(db, user_id)
                                            st.success("Actif supprimé avec succès.")
                                            st.rerun()
                                        else:
                                            st.error("Impossible de supprimer cet actif.")

                            # Formulaires d'édition conditionnels (très longs, comportant principalement des widgets Streamlit)
                            # Notez que cette partie est omise pour la concision, mais devrait être adaptée pour utiliser les
                            # appels à la base de données plutôt que les structures en mémoire
            else:
                st.info("Aucun actif ne correspond aux filtres sélectionnés.")

    with tab2:
        st.subheader("Ajouter un nouvel actif")

        # Récupérer les comptes disponibles
        accounts = db.query(Account).join(Bank).filter(Bank.owner_id == user_id).all()

        if not accounts:
            st.warning("Veuillez d'abord ajouter des comptes avant d'ajouter des actifs.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                asset_name = st.text_input("Nom de l'actif", key="new_asset_name")
                asset_type = st.selectbox(
                    "Type de produit",
                    options=PRODUCT_TYPES,
                    key="new_asset_type",
                    help="Type de produit financier (ETF, action individuelle, etc.)"
                )
                asset_notes = st.text_area("Notes", key="new_asset_notes",
                                           help="Notes personnelles sur cet actif")
                asset_todo = st.text_area("Tâche à faire (optionnel)", key="new_asset_todo")

            with col2:
                # Récupérer les banques pour filtrer les comptes
                banks = db.query(Bank).filter(Bank.owner_id == user_id).all()

                asset_bank = st.selectbox(
                    "Banque",
                    options=[bank.id for bank in banks],
                    format_func=lambda x: next((f"{bank.nom} ({bank.id})" for bank in banks if bank.id == x), ""),
                    key="new_asset_bank"
                )

                # Filtrer les comptes selon la banque sélectionnée
                bank_accounts = db.query(Account).filter(Account.bank_id == asset_bank).all()

                if bank_accounts:
                    asset_account = st.selectbox(
                        "Compte",
                        options=[acc.id for acc in bank_accounts],
                        format_func=lambda x: next((f"{acc.libelle} ({acc.id})" for acc in bank_accounts if acc.id == x), ""),
                        key="new_asset_account"
                    )
                else:
                    st.warning(f"Aucun compte disponible pour cette banque.")
                    asset_account = None

                asset_value = st.text_input("Valeur actuelle", key="new_asset_value")
                asset_cost = st.text_input("Prix de revient (optionnel)",
                                           value="", key="new_asset_cost",
                                           help="Laissez vide pour utiliser la valeur actuelle")
                asset_currency = st.selectbox(
                    "Devise",
                    options=CURRENCIES,
                    index=0,
                    key="new_asset_currency"
                )

            # Reste du code pour la création d'actif, allocation, répartition géographique, etc.
            # Cette partie est omise pour la concision mais devrait être adaptée pour utiliser
            # les appels à la base de données plutôt que les structures en mémoire