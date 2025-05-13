"""
Interface d'analyse et visualisations
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func  # Importation correcte de func

from database.models import Bank, Account, Asset, HistoryPoint
from services.visualization_service import VisualizationService
from utils.constants import ASSET_CATEGORIES, GEO_ZONES, GEO_ZONES_DESCRIPTIONS
from utils.visualizations import get_geo_zone_display_name

def show_analysis(db: Session, user_id: str):
    """
    Affiche l'interface d'analyse et visualisations

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.header("Analyses et Visualisations", anchor=False)

    # Vérifier si l'utilisateur a des actifs
    asset_count = db.query(Asset).filter(Asset.owner_id == user_id).count()

    if asset_count == 0:
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

        # Récupérer les banques de l'utilisateur
        banks = db.query(Bank).filter(Bank.owner_id == user_id).all()

        filter_bank = st.selectbox(
            "Banque",
            options=["Toutes"] + [bank.id for bank in banks],
            format_func=lambda x: "Toutes" if x == "Toutes" else
                       next((bank.nom for bank in banks if bank.id == x), ""),
            key="analysis_filter_bank"
        )

        # Comptes disponibles selon la banque sélectionnée
        if filter_bank != "Toutes":
            bank_accounts = db.query(Account).filter(Account.bank_id == filter_bank).all()
            account_options = ["Tous"] + [acc.id for acc in bank_accounts]
            account_format = lambda x: "Tous" if x == "Tous" else next((acc.libelle for acc in bank_accounts if acc.id == x), "")
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
        try:
            # Construire la requête filtrée
            query = db.query(Asset).filter(Asset.owner_id == user_id)

            if filter_bank != "Toutes":
                # Obtenir les IDs des comptes de cette banque
                bank_account_ids = [acc.id for acc in db.query(Account).filter(Account.bank_id == filter_bank).all()]
                query = query.filter(Asset.account_id.in_(bank_account_ids))

            if filter_account != "Tous":
                query = query.filter(Asset.account_id == filter_account)

            # Nouvelle approche pour le filtrage par catégorie
            if filter_category != "Toutes":
                # Pour SQLite, nous ne pouvons pas facilement filtrer dans les champs JSON
                # Récupérons d'abord tous les actifs puis filtrons en Python
                all_assets = query.all()
                filtered_assets = [
                    asset for asset in all_assets
                    if asset.allocation and isinstance(asset.allocation, dict) and filter_category in asset.allocation
                ]
            else:
                # Exécuter la requête normalement
                filtered_assets = query.all()

            # Afficher le résultat de filtrage
            if filtered_assets:
                # Calculer la valeur totale filtrée et non filtrée
                total_filtered = sum(asset.valeur_actuelle for asset in filtered_assets)

                # Utiliser func au lieu de db.func
                total_all = db.query(func.sum(Asset.valeur_actuelle)).filter(
                    Asset.owner_id == user_id
                ).scalar() or 0.0

                percentage = (total_filtered / total_all * 100) if total_all > 0 else 0

                st.markdown(
                    f"### Patrimoine sélectionné: {total_filtered:,.2f} € ({percentage:.1f}% du total)".replace(",", " "))

                # Créer les visualisations selon le groupby sélectionné
                if analysis_groupby == "Catégorie":
                    # Créer la visualisation par catégorie
                    st.subheader("Répartition par catégorie d'actif")

                    # Calculer les valeurs par catégorie
                    category_values = VisualizationService.calculate_category_values(
                        db,
                        user_id,
                        account_id=filter_account if filter_account != "Tous" else None,
                        asset_categories=ASSET_CATEGORIES
                    )

                    # Filtrer les catégories avec des valeurs > 0
                    category_values = {k.capitalize(): v for k, v in category_values.items() if v > 0}

                    if category_values:
                        # Créer le graphique en camembert
                        fig = VisualizationService.create_pie_chart(category_values)
                        if fig:
                            st.pyplot(fig)

                        # Afficher un tableau avec les valeurs
                        st.subheader("Détail par catégorie")
                        data = []
                        for cat, value in sorted(category_values.items(), key=lambda x: x[1], reverse=True):
                            data.append([
                                cat,
                                f"{value:,.2f} €".replace(",", " "),
                                f"{value / total_filtered * 100:.2f}%"
                            ])

                        df = pd.DataFrame(data, columns=["Catégorie", "Valeur", "Pourcentage"])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("Aucune donnée à afficher pour la répartition par catégorie.")

                elif analysis_groupby == "Zone géographique":
                    # Créer la visualisation par zone géographique
                    st.subheader("Répartition géographique")

                    # Ajouter la section d'aide
                    with st.expander("Aide: Pays inclus dans chaque zone géographique"):
                        st.markdown("""
                        | Zone géographique | Pays inclus typiques |
                        | ----------------- | -------------------- |
                        | Amérique du Nord | États-Unis, Canada |
                        | Europe zone euro | Allemagne, France, Espagne, Italie, Pays-Bas, etc. |
                        | Europe hors zone euro | Royaume-Uni, Suisse, Suède, Norvège, Danemark |
                        | Japon | Japon |
                        | Chine | Chine, Hong Kong |
                        | Inde | Inde |
                        | Asie développée | Corée du Sud, Australie, Singapour, Nouvelle-Zélande |
                        | Autres émergents | Brésil, Mexique, Indonésie, Afrique du Sud, Égypte, Turquie, Pologne, Vietnam, Nigeria, Argentine, Chili, Pérou, Colombie, etc. |
                        | Global/Non classé | Pour cas exceptionnels non ventilés |
                        """)

                    # Calculer les valeurs par zone géographique
                    geo_values = VisualizationService.calculate_geo_values(
                        db,
                        user_id,
                        account_id=filter_account if filter_account != "Tous" else None,
                        category=filter_category if filter_category != "Toutes" else None,
                        geo_zones=GEO_ZONES
                    )

                    # Filtrer les zones avec des valeurs > 0 et utiliser des noms affichables
                    geo_values_display = {get_geo_zone_display_name(k): v for k, v in geo_values.items() if v > 0}

                    if geo_values_display:
                        # Créer le graphique en camembert
                        fig = VisualizationService.create_pie_chart(geo_values_display)
                        if fig:
                            st.pyplot(fig)

                        # Afficher un tableau avec les valeurs
                        st.subheader("Détail par zone géographique")
                        data = []
                        for zone, value in sorted(geo_values_display.items(), key=lambda x: x[1], reverse=True):
                            data.append([
                                zone,
                                f"{value:,.2f} €".replace(",", " "),
                                f"{value / total_filtered * 100:.2f}%"
                            ])

                        df = pd.DataFrame(data, columns=["Zone", "Valeur", "Pourcentage"])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("Aucune donnée à afficher pour la répartition géographique.")

                elif analysis_groupby == "Banque":
                    # Créer la visualisation par banque
                    st.subheader("Répartition par banque")

                    # Calculer les valeurs par banque
                    bank_values = {}
                    for asset in filtered_assets:
                        account = db.query(Account).filter(Account.id == asset.account_id).first()
                        if account:
                            bank = db.query(Bank).filter(Bank.id == account.bank_id).first()
                            if bank:
                                if bank.nom not in bank_values:
                                    bank_values[bank.nom] = 0
                                bank_values[bank.nom] += asset.valeur_actuelle

                    if bank_values:
                        # Créer le graphique en camembert
                        fig = VisualizationService.create_pie_chart(bank_values)
                        if fig:
                            st.pyplot(fig)

                        # Afficher un tableau avec les valeurs
                        st.subheader("Détail par banque")
                        data = []
                        for bank_name, value in sorted(bank_values.items(), key=lambda x: x[1], reverse=True):
                            data.append([
                                bank_name,
                                f"{value:,.2f} €".replace(",", " "),
                                f"{value / total_filtered * 100:.2f}%"
                            ])

                        df = pd.DataFrame(data, columns=["Banque", "Valeur", "Pourcentage"])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("Aucune donnée à afficher pour la répartition par banque.")

                elif analysis_groupby == "Compte":
                    # Créer la visualisation par compte
                    st.subheader("Répartition par compte")

                    # Calculer les valeurs par compte
                    account_values = {}
                    for asset in filtered_assets:
                        account = db.query(Account).filter(Account.id == asset.account_id).first()
                        if account:
                            account_name = account.libelle
                            if account_name not in account_values:
                                account_values[account_name] = 0
                            account_values[account_name] += asset.valeur_actuelle

                    if account_values:
                        # Créer le graphique en camembert
                        fig = VisualizationService.create_pie_chart(account_values)
                        if fig:
                            st.pyplot(fig)

                        # Afficher un tableau avec les valeurs
                        st.subheader("Détail par compte")
                        data = []
                        for account_name, value in sorted(account_values.items(), key=lambda x: x[1], reverse=True):
                            data.append([
                                account_name,
                                f"{value:,.2f} €".replace(",", " "),
                                f"{value / total_filtered * 100:.2f}%"
                            ])

                        df = pd.DataFrame(data, columns=["Compte", "Valeur", "Pourcentage"])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("Aucune donnée à afficher pour la répartition par compte.")

                elif analysis_groupby == "Type de produit":
                    # Créer la visualisation par type de produit
                    st.subheader("Répartition par type de produit")

                    # Calculer les valeurs par type de produit
                    type_values = {}
                    for asset in filtered_assets:
                        product_type = asset.type_produit.capitalize()
                        if product_type not in type_values:
                            type_values[product_type] = 0
                        type_values[product_type] += asset.valeur_actuelle

                    if type_values:
                        # Créer le graphique en camembert
                        fig = VisualizationService.create_pie_chart(type_values)
                        if fig:
                            st.pyplot(fig)

                        # Afficher un tableau avec les valeurs
                        st.subheader("Détail par type de produit")
                        data = []
                        for type_name, value in sorted(type_values.items(), key=lambda x: x[1], reverse=True):
                            data.append([
                                type_name,
                                f"{value:,.2f} €".replace(",", " "),
                                f"{value / total_filtered * 100:.2f}%"
                            ])

                        df = pd.DataFrame(data, columns=["Type", "Valeur", "Pourcentage"])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("Aucune donnée à afficher pour la répartition par type de produit.")

                # Évolution historique
                st.subheader("Évolution temporelle")
                fig = VisualizationService.create_time_series_chart(db)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("Pas assez de données historiques pour afficher l'évolution temporelle.")

            else:
                st.warning("Aucun actif ne correspond aux filtres sélectionnés.")
        except Exception as e:
            st.error(f"Erreur lors de la création des visualisations: {str(e)}")
            # Afficher des informations de débogage supplémentaires si nécessaire
            # import traceback
            # st.code(traceback.format_exc())