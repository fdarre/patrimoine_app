"""
Interface d'analyse et visualisations
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_

from database.models import Bank, Account, Asset, HistoryPoint
from services.visualization_service import VisualizationService
from config.app_config import ASSET_CATEGORIES, GEO_ZONES, GEO_ZONES_DESCRIPTIONS
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
            # OPTIMISATION: Construire la requête de base une seule fois
            # Construire la requête de base pour les actifs filtrés
            base_query = db.query(Asset).filter(Asset.owner_id == user_id)

            # Appliquer les filtres de base
            if filter_bank != "Toutes":
                # OPTIMISATION: Utiliser une jointure au lieu de sous-requêtes
                base_query = base_query.join(Account, Asset.account_id == Account.id)
                base_query = base_query.filter(Account.bank_id == filter_bank)

            if filter_account != "Tous":
                base_query = base_query.filter(Asset.account_id == filter_account)

            # Pour le filtre par catégorie, nécessite un traitement spécial
            filtered_query = base_query
            if filter_category != "Toutes":
                # Pour SQLite, utiliser json_extract pour filtrer sur les champs JSON
                filtered_query = filtered_query.filter(
                    func.json_extract(Asset.allocation, f'$.{filter_category}').isnot(None)
                )

            # Calculer la valeur totale des actifs filtrés
            total_filtered = filtered_query.with_entities(
                func.sum(func.coalesce(Asset.value_eur, 0.0))
            ).scalar() or 0.0

            # Calculer la valeur totale de tous les actifs
            total_all = db.query(func.sum(
                func.coalesce(Asset.value_eur, 0.0)
            )).filter(
                Asset.owner_id == user_id
            ).scalar() or 0.0

            percentage = (total_filtered / total_all * 100) if total_all > 0 else 0

            st.markdown(
                f"### Patrimoine sélectionné: {total_filtered:,.2f} € ({percentage:.1f}% du total)".replace(",", " "))

            # Créer les visualisations selon le groupby sélectionné
            if analysis_groupby == "Catégorie":
                # OPTIMISATION: Utiliser la fonction optimisée pour les catégories
                st.subheader("Répartition par catégorie d'actif")

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
                # OPTIMISATION: Utiliser la fonction optimisée pour les zones géographiques
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
                # OPTIMISATION: Utiliser une requête d'agrégation pour les banques
                st.subheader("Répartition par banque")

                # Requête d'agrégation optimisée pour les banques
                bank_values_query = db.query(
                    Bank.nom,
                    func.sum(func.coalesce(Asset.value_eur, 0.0)).label('total_value')
                ).join(
                    Account, Asset.account_id == Account.id
                ).join(
                    Bank, Account.bank_id == Bank.id
                ).filter(
                    Asset.owner_id == user_id
                )

                # Appliquer les mêmes filtres que la requête de base
                if filter_account != "Tous":
                    bank_values_query = bank_values_query.filter(Account.id == filter_account)

                if filter_category != "Toutes":
                    bank_values_query = bank_values_query.filter(
                        func.json_extract(Asset.allocation, f'$.{filter_category}').isnot(None)
                    )

                # Grouper par banque et exécuter la requête
                bank_values_query = bank_values_query.group_by(Bank.nom)
                bank_values_result = bank_values_query.all()

                # Convertir le résultat en dictionnaire pour le graphique
                bank_values = {row[0]: row[1] for row in bank_values_result}

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
                # OPTIMISATION: Utiliser une requête d'agrégation pour les comptes
                st.subheader("Répartition par compte")

                # Requête d'agrégation optimisée pour les comptes
                account_values_query = db.query(
                    Account.libelle,
                    func.sum(func.coalesce(Asset.value_eur, 0.0)).label('total_value')
                ).join(
                    Asset, Asset.account_id == Account.id
                ).filter(
                    Asset.owner_id == user_id
                )

                # Appliquer les filtres
                if filter_bank != "Toutes":
                    account_values_query = account_values_query.filter(Account.bank_id == filter_bank)

                if filter_category != "Toutes":
                    account_values_query = account_values_query.filter(
                        func.json_extract(Asset.allocation, f'$.{filter_category}').isnot(None)
                    )

                # Grouper par compte et exécuter la requête
                account_values_query = account_values_query.group_by(Account.libelle)
                account_values_result = account_values_query.all()

                # Convertir le résultat en dictionnaire pour le graphique
                account_values = {row[0]: row[1] for row in account_values_result}

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
                # OPTIMISATION: Utiliser une requête d'agrégation pour les types de produit
                st.subheader("Répartition par type de produit")

                # Requête d'agrégation optimisée pour les types de produit
                type_values_query = db.query(
                    Asset.type_produit,
                    func.sum(func.coalesce(Asset.value_eur, 0.0)).label('total_value')
                ).filter(
                    Asset.owner_id == user_id
                )

                # Appliquer les filtres
                if filter_bank != "Toutes":
                    type_values_query = type_values_query.join(Account, Asset.account_id == Account.id)
                    type_values_query = type_values_query.filter(Account.bank_id == filter_bank)

                if filter_account != "Tous":
                    type_values_query = type_values_query.filter(Asset.account_id == filter_account)

                if filter_category != "Toutes":
                    type_values_query = type_values_query.filter(
                        func.json_extract(Asset.allocation, f'$.{filter_category}').isnot(None)
                    )

                # Grouper par type de produit et exécuter la requête
                type_values_query = type_values_query.group_by(Asset.type_produit)
                type_values_result = type_values_query.all()

                # Convertir le résultat en dictionnaire pour le graphique, avec type capitalisé
                type_values = {row[0].capitalize(): row[1] for row in type_values_result}

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

        except Exception as e:
            st.error(f"Erreur lors de la création des visualisations: {str(e)}")
            # Afficher des informations de débogage supplémentaires
            import traceback
            st.code(traceback.format_exc())