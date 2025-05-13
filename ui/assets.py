"""
Interface de gestion des actifs, incluant les actifs composites
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
from typing import Dict, List, Optional, Any

from models.asset import Asset
from services.asset_service import AssetService
from services.data_service import DataService
from utils.constants import ACCOUNT_TYPES, PRODUCT_TYPES, ASSET_CATEGORIES, GEO_ZONES, CURRENCIES, DATA_DIR
from utils.calculations import get_default_geo_zones, is_circular_reference


def show_asset_management(
        banks: Dict[str, Dict[str, Any]],
        accounts: Dict[str, Dict[str, Any]],
        assets: List[Asset],
        history: List[Dict[str, Any]]
):
    """
    Affiche l'interface de gestion des actifs

    Args:
        banks: Dictionnaire des banques
        accounts: Dictionnaire des comptes
        assets: Liste des actifs
        history: Liste des points d'historique
    """
    st.header("Gestion des actifs", anchor=False)

    # Debug info - afficher les informations sur les données chargées
    with st.expander("Informations de débogage"):
        st.write("### Banques")
        st.write(f"Nombre de banques: {len(banks)}")
        st.json(banks)

        st.write("### Comptes")
        st.write(f"Nombre de comptes: {len(accounts)}")
        st.json(accounts)

        st.write("### Actifs")
        st.write(f"Nombre d'actifs: {len(assets)}")

        st.write("### Environnement")
        st.write(f"Chemin de travail: {os.getcwd()}")
        st.write(f"Fichiers dans data/: {os.listdir('data/') if os.path.exists('data/') else 'Dossier non trouvé'}")

    # Onglets pour les différentes fonctions de gestion d'actifs
    tab1, tab2 = st.tabs(["Liste des actifs", "Ajouter un actif"])

    with tab1:
        st.subheader("Liste de tous les actifs")

        if not assets:
            st.info("Aucun actif n'a encore été ajouté.")
        else:
            # Contrôles de filtrage
            col1, col2, col3 = st.columns(3)

            with col1:
                filter_bank = st.selectbox(
                    "Filtrer par banque",
                    options=["Toutes les banques"] + list(banks.keys()),
                    format_func=lambda x: "Toutes les banques" if x == "Toutes les banques"
                    else f"{banks[x]['nom']}",
                    key="asset_filter_bank"
                )

            with col2:
                if filter_bank != "Toutes les banques":
                    # Obtenir les comptes pour la banque sélectionnée
                    bank_accounts = {k: v for k, v in accounts.items()
                                     if v["banque_id"] == filter_bank}

                    if bank_accounts:
                        filter_account = st.selectbox(
                            "Filtrer par compte",
                            options=["Tous les comptes"] + list(bank_accounts.keys()),
                            format_func=lambda x: "Tous les comptes" if x == "Tous les comptes"
                            else f"{accounts[x]['libelle']}",
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
            filtered_assets = assets.copy()

            if filter_bank != "Toutes les banques":
                bank_account_ids = [acc_id for acc_id, acc in accounts.items()
                                    if acc["banque_id"] == filter_bank]
                filtered_assets = [asset for asset in filtered_assets
                                   if asset.compte_id in bank_account_ids]

            if filter_account != "Tous les comptes":
                filtered_assets = [asset for asset in filtered_assets
                                   if asset.compte_id == filter_account]

            if filter_category != "Toutes les catégories":
                # Pour les actifs mixtes, on filtre si la catégorie est présente dans l'allocation
                filtered_assets = [asset for asset in filtered_assets
                                   if filter_category in asset.allocation]

            # Afficher les actifs filtrés
            if filtered_assets:
                # Utiliser notre fonction pour créer un DataFrame avec les allocations
                assets_df = AssetService.get_assets_dataframe(
                    assets=filtered_assets,
                    accounts=accounts,
                    banks=banks,
                    account_id=filter_account if filter_account != "Tous les comptes" else None,
                    category=filter_category if filter_category != "Toutes les catégories" else None,
                    bank_id=filter_bank if filter_bank != "Toutes les banques" else None
                )

                # Cacher la colonne ID mais l'utiliser pour la sélection
                st.markdown(assets_df.drop(columns=["ID"]).to_html(escape=False, index=False), unsafe_allow_html=True)

                # Sélection d'un actif pour détails
                selected_asset_id = st.selectbox(
                    "Sélectionner un actif pour détails",
                    options=[asset.id for asset in filtered_assets],
                    format_func=lambda x: next((a.nom for a in filtered_assets if a.id == x), "")
                )

                if selected_asset_id:
                    asset = AssetService.find_asset_by_id(assets, selected_asset_id)

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

                                st.write("**Compte:**", accounts[asset.compte_id]["libelle"])
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
                            if asset.is_composite():
                                st.subheader("Composition de l'actif")

                                component_data = []
                                for component in asset.composants:
                                    component_asset = AssetService.find_asset_by_id(assets, component["asset_id"])
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
                                    st.dataframe(component_df.drop(columns=["ID"]))

                                    # Afficher le pourcentage restant directement alloué
                                    direct_percentage = 100 - asset.get_components_total_percentage()
                                    if direct_percentage > 0:
                                        st.info(
                                            f"{direct_percentage:.2f}% de l'actif est alloué directement selon l'allocation définie.")

                                    # Si l'actif a des composants, afficher l'allocation effective calculée
                                    st.subheader("Allocation effective (incluant les composants)")
                                    effective_allocation = AssetService.calculate_effective_allocation(assets, asset)
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
                                        if asset.is_composite():
                                            effective_geo = AssetService.calculate_effective_geo_allocation(assets,
                                                                                                            asset,
                                                                                                            category)
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
                                is_used = AssetService.is_used_as_component(assets, selected_asset_id)

                                if is_used:
                                    st.warning(
                                        "Cet actif est utilisé comme composant dans d'autres actifs et ne peut pas être supprimé.")
                                else:
                                    if st.button("Supprimer cet actif", key=f"btn_delete_asset_{selected_asset_id}"):
                                        if AssetService.delete_asset(assets, selected_asset_id):
                                            # Mettre à jour l'historique
                                            history = DataService.record_history_entry(assets, history)
                                            DataService.save_data(banks, accounts, assets, history)
                                            st.success("Actif supprimé avec succès.")
                                            st.rerun()
                                        else:
                                            st.error("Impossible de supprimer cet actif.")

                            # Nombreuses autres fonctionnalités d'édition d'actifs que j'ai omises ici pour la concision
            else:
                st.info("Aucun actif ne correspond aux filtres sélectionnés.")

    with tab2:
        st.subheader("Ajouter un nouvel actif")

        if not accounts:
            st.error("ERREUR: Aucun compte n'a été chargé. Vérifiez le fichier accounts.json.")
            st.warning("Veuillez d'abord ajouter des comptes avant d'ajouter des actifs.")
        else:
            st.success(f"Comptes disponibles: {len(accounts)}")

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
                # Filtrer les comptes par banque pour une meilleure organisation
                asset_bank = st.selectbox(
                    "Banque",
                    options=list(banks.keys()),
                    format_func=lambda x: f"{banks[x]['nom']} ({x})",
                    key="new_asset_bank"
                )

                # Filtrer les comptes selon la banque sélectionnée et déboguer
                bank_accounts = {k: v for k, v in accounts.items() if v["banque_id"] == asset_bank}
                st.write(f"Bank ID sélectionnée: '{asset_bank}'")
                st.write(f"Comptes filtrés pour cette banque: {bank_accounts}")

                if bank_accounts:
                    asset_account = st.selectbox(
                        "Compte",
                        options=list(bank_accounts.keys()),
                        format_func=lambda x: f"{accounts[x]['libelle']} ({x})",
                        key="new_asset_account"
                    )
                else:
                    st.error(f"ERREUR: Aucun compte trouvé pour la banque '{asset_bank}'")
                    st.warning(f"Vérifiez que la banque_id dans accounts.json correspond bien à '{asset_bank}'")
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

            # Section pour l'allocation par catégorie
            st.subheader("Allocation par catégorie")
            st.info("Répartissez la valeur de l'actif entre les différentes catégories (total 100%)")

            # Variables pour stocker les allocations
            allocation = {}
            allocation_total = 0

            # Créer une interface avec deux colonnes pour les catégories
            allocation_col1, allocation_col2 = st.columns(2)

            # Première colonne: principaux types d'actifs
            with allocation_col1:
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

            # Deuxième colonne: autres types d'actifs
            with allocation_col2:
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

            # Barre de progression pour visualiser le total
            st.progress(allocation_total / 100)

            # Vérifier que le total est de 100%
            if allocation_total != 100:
                st.warning(f"Le total des allocations doit être de 100%. Actuellement: {allocation_total}%")
            else:
                st.success("Allocation valide (100%)")

            # Reste du code pour l'ajout d'actifs...
            # (Je l'omets pour plus de clarté, car il s'agit principalement de UI et nous nous concentrons sur le débogage)