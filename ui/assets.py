"""
Interface de gestion des actifs, incluant les actifs composites
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

from models.asset import Asset
from services.asset_service import AssetService
from services.data_service import DataService
from utils.constants import ACCOUNT_TYPES, PRODUCT_TYPES, ASSET_CATEGORIES, GEO_ZONES, CURRENCIES
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