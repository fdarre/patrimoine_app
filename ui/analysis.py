"""
Interface d'analyse et visualisations
"""

import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Any
import matplotlib.pyplot as plt

from models.asset import Asset
from services.visualization_service import VisualizationService
from services.asset_service import AssetService
from utils.calculations import calculate_category_values, calculate_geo_values, calculate_total_patrimony
from utils.constants import ASSET_CATEGORIES, GEO_ZONES


def show_analysis(
        banks: Dict[str, Dict[str, Any]],
        accounts: Dict[str, Dict[str, Any]],
        assets: List[Asset],
        history: List[Dict[str, Any]]
):
    """
    Affiche l'interface d'analyse et visualisations

    Args:
        banks: Dictionnaire des banques
        accounts: Dictionnaire des comptes
        assets: Liste des actifs
        history: Liste des points d'historique
    """
    st.header("Analyses et Visualisations", anchor=False)

    if not assets:
        st.info("Ajoutez des actifs pour voir les analyses.")
        return

    # Filtres pour l'analyse
    col1, col2 = st.columns([1, 3])

    with col1:
        analysis_groupby = st.radio(
            "Grouper par",
            options=["Catégorie", "Banque", "Compte", "Type de produit", "Zone géographique"],
            index=0,
            key="analysis_groupby"
        )

        # Option de filtrage supplémentaire
        st.markdown("### Filtres")

        filter_bank = st.selectbox(
            "Banque",
            options=["Toutes"] + list(banks.keys()),
            format_func=lambda x: "Toutes" if x == "Toutes" else banks[x]["nom"],
            key="analysis_filter_bank"
        )

        # Comptes disponibles selon la banque sélectionnée
        if filter_bank != "Toutes":
            bank_accounts = {k: v for k, v in accounts.items() if v["banque_id"] == filter_bank}
            account_options = ["Tous"] + list(bank_accounts.keys())
            account_format = lambda x: "Tous" if x == "Tous" else accounts[x]["libelle"]
        else:
            account_options = ["Tous"]
            account_format = lambda x: "Tous"

        filter_account = st.selectbox(
            "Compte",
            options=account_options,
            format_func=account_format,
            key="analysis_filter_account"
        )

        filter_category = st.selectbox(
            "Catégorie",
            options=["Toutes"] + ASSET_CATEGORIES,
            key="analysis_filter_category"
        )

    with col2:
        # Filtrer les actifs selon les critères
        filtered_assets = assets.copy()

        if filter_bank != "Toutes":
            bank_account_ids = [acc_id for acc_id, acc in accounts.items() if acc["banque_id"] == filter_bank]
            filtered_assets = [asset for asset in filtered_assets if asset.compte_id in bank_account_ids]

        if filter_account != "Tous":
            filtered_assets = [asset for asset in filtered_assets if asset.compte_id == filter_account]

        if filter_category != "Toutes":
            # Pour les actifs mixtes, inclure ceux qui ont cette catégorie dans leur allocation
            filtered_assets = [asset for asset in filtered_assets if filter_category in asset.allocation]

        # Afficher le résultat de filtrage
        if filtered_assets:
            # Calculer la valeur totale filtrée et non filtrée
            total_filtered = sum(asset.valeur_actuelle for asset in filtered_assets)
            total_all = sum(asset.valeur_actuelle for asset in assets)
            percentage = (total_filtered / total_all * 100) if total_all > 0 else 0

            st.markdown(
                f"### Patrimoine sélectionné: {total_filtered:,.2f} € ({percentage:.1f}% du total)".replace(",", " "))
        else:
            st.warning("Aucun actif ne correspond aux filtres sélectionnés.")
            return

        # Créer le graphique approprié en fonction de la sélection
        if analysis_groupby == "Catégorie":
            # Calculer les valeurs par catégorie (en tenant compte des fonds mixtes)
            category_values = calculate_category_values(assets, accounts, filtered_assets)

            # Convertir les catégories en format capitalisé pour l'affichage
            category_values_display = {k.capitalize(): v for k, v in category_values.items() if v > 0}

            # Créer le graphique
            fig = VisualizationService.create_pie_chart(category_values_display, "Répartition par catégorie d'actif")
            if fig:
                st.pyplot(fig)

            # Tableau détaillé des données
            data = []
            for category, value in sorted(category_values_display.items(), key=lambda x: x[1], reverse=True):
                percentage = (value / total_filtered * 100) if total_filtered > 0 else 0
                data.append([
                    category,
                    f"{value:,.2f} €".replace(",", " "),
                    f"{percentage:.1f}%"
                ])

            df = pd.DataFrame(data, columns=["Catégorie", "Valeur", "Pourcentage"])
            st.dataframe(df, use_container_width=True)

        elif analysis_groupby == "Banque":
            # Agréger par banque
            bank_totals = {}
            for asset in filtered_assets:
                account = accounts[asset.compte_id]
                bank_id = account["banque_id"]
                bank_name = banks[bank_id]["nom"]

                if bank_name not in bank_totals:
                    bank_totals[bank_name] = 0
                bank_totals[bank_name] += asset.valeur_actuelle

            # Créer le graphique
            fig = VisualizationService.create_bar_chart(bank_totals, "Répartition par banque", ylabel="Valeur (€)",
                                                        horizontal=True)
            if fig:
                st.pyplot(fig)

            # Tableau détaillé des données
            data = []
            for bank, value in sorted(bank_totals.items(), key=lambda x: x[1], reverse=True):
                percentage = (value / total_filtered * 100) if total_filtered > 0 else 0
                data.append([
                    bank,
                    f"{value:,.2f} €".replace(",", " "),
                    f"{percentage:.1f}%"
                ])

            df = pd.DataFrame(data, columns=["Banque", "Valeur", "Pourcentage"])
            st.dataframe(df, use_container_width=True)

        elif analysis_groupby == "Compte":
            # Agréger par compte
            account_totals = {}
            for asset in filtered_assets:
                account_id = asset.compte_id
                account_name = accounts[account_id]["libelle"]
                bank_name = banks[accounts[account_id]["banque_id"]]["nom"]
                account_key = f"{account_name} ({bank_name})"

                if account_key not in account_totals:
                    account_totals[account_key] = 0
                account_totals[account_key] += asset.valeur_actuelle

            # Créer le graphique
            fig = VisualizationService.create_bar_chart(account_totals, "Répartition par compte", ylabel="Valeur (€)",
                                                        horizontal=False)
            if fig:
                st.pyplot(fig)

            # Tableau détaillé des données
            data = []
            for account, value in sorted(account_totals.items(), key=lambda x: x[1], reverse=True):
                percentage = (value / total_filtered * 100) if total_filtered > 0 else 0
                data.append([
                    account,
                    f"{value:,.2f} €".replace(",", " "),
                    f"{percentage:.1f}%"
                ])

            df = pd.DataFrame(data, columns=["Compte", "Valeur", "Pourcentage"])
            st.dataframe(df, use_container_width=True)

        elif analysis_groupby == "Type de produit":
            # Agréger par type de produit
            type_totals = {}
            for asset in filtered_assets:
                product_type = asset.type_produit.capitalize()

                if product_type not in type_totals:
                    type_totals[product_type] = 0
                type_totals[product_type] += asset.valeur_actuelle

            # Créer le graphique
            fig = VisualizationService.create_bar_chart(type_totals, "Répartition par type de produit",
                                                        ylabel="Valeur (€)", horizontal=False)
            if fig:
                st.pyplot(fig)

            # Tableau détaillé des données
            data = []
            for type_name, value in sorted(type_totals.items(), key=lambda x: x[1], reverse=True):
                percentage = (value / total_filtered * 100) if total_filtered > 0 else 0
                data.append([
                    type_name,
                    f"{value:,.2f} €".replace(",", " "),
                    f"{percentage:.1f}%"
                ])

            df = pd.DataFrame(data, columns=["Type de produit", "Valeur", "Pourcentage"])
            st.dataframe(df, use_container_width=True)

        elif analysis_groupby == "Zone géographique":
            # Calculer les valeurs par zone géographique (en tenant compte des fonds mixtes)
            geo_values = calculate_geo_values(
                assets,
                accounts,
                filtered_assets,
                category=filter_category if filter_category != "Toutes" else None
            )

            # Convertir les zones en format capitalisé pour l'affichage
            geo_values_display = {k.capitalize(): v for k, v in geo_values.items() if v > 0}

            # Créer le graphique
            fig = VisualizationService.create_pie_chart(geo_values_display, "Répartition géographique globale")
            if fig:
                st.pyplot(fig)

            # Tableau détaillé des données
            data = []
            for zone, value in sorted(geo_values_display.items(), key=lambda x: x[1], reverse=True):
                percentage = (value / total_filtered * 100) if total_filtered > 0 else 0
                data.append([
                    zone,
                    f"{value:,.2f} €".replace(",", " "),
                    f"{percentage:.1f}%"
                ])

            df = pd.DataFrame(data, columns=["Zone géographique", "Valeur", "Pourcentage"])
            st.dataframe(df, use_container_width=True)

    # Analyses spécifiques par catégorie
    st.subheader("Répartition géographique par catégorie")

    # Créer des onglets pour les différentes catégories d'actifs
    category_tabs = st.tabs(["Actions", "Obligations", "Immobilier", "Autre"])

    with category_tabs[0]:
        # Calculer les valeurs par zone géographique pour la catégorie "actions"
        geo_values = calculate_geo_values(assets, accounts, filtered_assets, category="actions")

        # Calculer la valeur totale allouée aux actions
        total_actions = sum(asset.valeur_actuelle * asset.allocation.get("actions", 0) / 100
                            for asset in filtered_assets if "actions" in asset.allocation)

        if total_actions > 0:
            # Convertir les zones en format capitalisé pour l'affichage
            geo_values_display = {k.capitalize(): v for k, v in geo_values.items() if v > 0}

            # Créer le graphique
            fig = VisualizationService.create_pie_chart(geo_values_display,
                                                        f"Répartition géographique - Actions ({total_actions:,.0f} €)".replace(
                                                            ",", " "))
            if fig:
                st.pyplot(fig)

            # Tableau détaillé des données
            data = []
            for zone, value in sorted(geo_values_display.items(), key=lambda x: x[1], reverse=True):
                percentage = (value / total_actions * 100) if total_actions > 0 else 0
                data.append([
                    zone,
                    f"{value:,.2f} €".replace(",", " "),
                    f"{percentage:.1f}%"
                ])

            df = pd.DataFrame(data, columns=["Zone géographique", "Valeur", "Pourcentage"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun actif de type 'actions' dans la sélection.")

    with category_tabs[1]:
        # Calculer les valeurs par zone géographique pour la catégorie "obligations"
        geo_values = calculate_geo_values(assets, accounts, filtered_assets, category="obligations")

        # Calculer la valeur totale allouée aux obligations
        total_obligations = sum(asset.valeur_actuelle * asset.allocation.get("obligations", 0) / 100
                                for asset in filtered_assets if "obligations" in asset.allocation)

        if total_obligations > 0:
            # Convertir les zones en format capitalisé pour l'affichage
            geo_values_display = {k.capitalize(): v for k, v in geo_values.items() if v > 0}

            # Créer le graphique
            fig = VisualizationService.create_pie_chart(geo_values_display,
                                                        f"Répartition géographique - Obligations ({total_obligations:,.0f} €)".replace(
                                                            ",", " "))
            if fig:
                st.pyplot(fig)

            # Tableau détaillé des données
            data = []
            for zone, value in sorted(geo_values_display.items(), key=lambda x: x[1], reverse=True):
                percentage = (value / total_obligations * 100) if total_obligations > 0 else 0
                data.append([
                    zone,
                    f"{value:,.2f} €".replace(",", " "),
                    f"{percentage:.1f}%"
                ])

            df = pd.DataFrame(data, columns=["Zone géographique", "Valeur", "Pourcentage"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun actif de type 'obligations' dans la sélection.")

    with category_tabs[2]:
        # Calculer les valeurs par zone géographique pour la catégorie "immobilier"
        geo_values = calculate_geo_values(assets, accounts, filtered_assets, category="immobilier")

        # Calculer la valeur totale allouée à l'immobilier
        total_immobilier = sum(asset.valeur_actuelle * asset.allocation.get("immobilier", 0) / 100
                               for asset in filtered_assets if "immobilier" in asset.allocation)

        if total_immobilier > 0:
            # Convertir les zones en format capitalisé pour l'affichage
            geo_values_display = {k.capitalize(): v for k, v in geo_values.items() if v > 0}

            # Créer le graphique
            fig = VisualizationService.create_pie_chart(geo_values_display,
                                                        f"Répartition géographique - Immobilier ({total_immobilier:,.0f} €)".replace(
                                                            ",", " "))
            if fig:
                st.pyplot(fig)

            # Tableau détaillé des données
            data = []
            for zone, value in sorted(geo_values_display.items(), key=lambda x: x[1], reverse=True):
                percentage = (value / total_immobilier * 100) if total_immobilier > 0 else 0
                data.append([
                    zone,
                    f"{value:,.2f} €".replace(",", " "),
                    f"{percentage:.1f}%"
                ])

            df = pd.DataFrame(data, columns=["Zone géographique", "Valeur", "Pourcentage"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun actif de type 'immobilier' dans la sélection.")

    with category_tabs[3]:
        # Calculer les valeurs par zone géographique pour les autres catégories
        other_categories = ["crypto", "metaux", "cash", "autre"]
        other_geo_values = {}

        for category in other_categories:
            cat_geo_values = calculate_geo_values(assets, accounts, filtered_assets, category=category)
            for zone, value in cat_geo_values.items():
                if value > 0:
                    if zone not in other_geo_values:
                        other_geo_values[zone] = 0
                    other_geo_values[zone] += value

        # Calculer la valeur totale allouée aux autres catégories
        total_other = sum(asset.valeur_actuelle * sum(asset.allocation.get(cat, 0) for cat in other_categories) / 100
                          for asset in filtered_assets
                          if any(cat in asset.allocation for cat in other_categories))

        if total_other > 0:
            # Convertir les zones en format capitalisé pour l'affichage
            other_geo_values_display = {k.capitalize(): v for k, v in other_geo_values.items() if v > 0}

            # Créer le graphique
            fig = VisualizationService.create_pie_chart(other_geo_values_display,
                                                        f"Répartition géographique - Autres actifs ({total_other:,.0f} €)".replace(
                                                            ",", " "))
            if fig:
                st.pyplot(fig)

            # Tableau détaillé des données
            data = []
            for zone, value in sorted(other_geo_values_display.items(), key=lambda x: x[1], reverse=True):
                percentage = (value / total_other * 100) if total_other > 0 else 0
                data.append([
                    zone,
                    f"{value:,.2f} €".replace(",", " "),
                    f"{percentage:.1f}%"
                ])

            df = pd.DataFrame(data, columns=["Zone géographique", "Valeur", "Pourcentage"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun autre type d'actif dans la sélection.")

    # Option pour exporter les analyses
    with st.expander("Exporter l'analyse"):
        export_format = st.radio(
            "Format d'exportation",
            options=["JSON", "CSV"],
            index=0,
            horizontal=True,
            key="export_format"
        )

        if st.button("Exporter", key="export_btn"):
            # Créer des données d'analyse complètes
            export_data = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_all": sum(asset.valeur_actuelle for asset in assets),
                "total_filtered": sum(asset.valeur_actuelle for asset in filtered_assets),
                "filters": {
                    "bank": filter_bank,
                    "account": filter_account,
                    "category": filter_category
                },
                "groupby": analysis_groupby,
                "categories": {},
                "banks": {},
                "accounts": {},
                "product_types": {},
                "geo_zones": {}
            }

            # Remplir les données par catégorie
            category_values = calculate_category_values(assets, accounts, filtered_assets)
            for category, value in category_values.items():
                if value > 0:
                    export_data["categories"][category] = value

            # Remplir les données par banque
            for asset in filtered_assets:
                # Par banque
                bank_id = accounts[asset.compte_id]["banque_id"]
                bank_name = banks[bank_id]["nom"]
                if bank_name not in export_data["banks"]:
                    export_data["banks"][bank_name] = 0
                export_data["banks"][bank_name] += asset.valeur_actuelle

                # Par compte
                account_name = accounts[asset.compte_id]["libelle"]
                account_key = f"{account_name} ({bank_name})"
                if account_key not in export_data["accounts"]:
                    export_data["accounts"][account_key] = 0
                export_data["accounts"][account_key] += asset.valeur_actuelle

                # Par type de produit
                product_type = asset.type_produit.capitalize()
                if product_type not in export_data["product_types"]:
                    export_data["product_types"][product_type] = 0
                export_data["product_types"][product_type] += asset.valeur_actuelle

            # Par zone géographique
            geo_values = calculate_geo_values(assets, accounts, filtered_assets)
            export_data["geo_zones"] = {k: v for k, v in geo_values.items() if v > 0}

            if export_format == "JSON":
                export_json = json.dumps(export_data, indent=2)
                st.download_button(
                    "Télécharger JSON",
                    data=export_json,
                    file_name=f"analyse_patrimoniale_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    key="download_json"
                )
            elif export_format == "CSV":
                # Convertir en structure plate pour CSV
                flat_data = []

                # Exporter selon le groupement sélectionné
                if analysis_groupby == "Catégorie":
                    for category, value in export_data["categories"].items():
                        percentage = (value / export_data["total_filtered"]) * 100
                        flat_data.append({
                            "Type": "Catégorie",
                            "Nom": category,
                            "Valeur": value,
                            "Pourcentage": percentage
                        })
                elif analysis_groupby == "Banque":
                    for bank, value in export_data["banks"].items():
                        percentage = (value / export_data["total_filtered"]) * 100
                        flat_data.append({
                            "Type": "Banque",
                            "Nom": bank,
                            "Valeur": value,
                            "Pourcentage": percentage
                        })
                elif analysis_groupby == "Compte":
                    for account, value in export_data["accounts"].items():
                        percentage = (value / export_data["total_filtered"]) * 100
                        flat_data.append({
                            "Type": "Compte",
                            "Nom": account,
                            "Valeur": value,
                            "Pourcentage": percentage
                        })
                elif analysis_groupby == "Type de produit":
                    for product_type, value in export_data["product_types"].items():
                        percentage = (value / export_data["total_filtered"]) * 100
                        flat_data.append({
                            "Type": "Type de produit",
                            "Nom": product_type,
                            "Valeur": value,
                            "Pourcentage": percentage
                        })
                elif analysis_groupby == "Zone géographique":
                    for zone, value in export_data["geo_zones"].items():
                        percentage = (value / export_data["total_filtered"]) * 100
                        flat_data.append({
                            "Type": "Zone géographique",
                            "Nom": zone,
                            "Valeur": value,
                            "Pourcentage": percentage
                        })

                flat_df = pd.DataFrame(flat_data)
                csv = flat_df.to_csv(index=False)

                st.download_button(
                    "Télécharger CSV",
                    data=csv,
                    file_name=f"analyse_patrimoniale_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="download_csv"
                )