"""
Interface d'analyse et visualisations
"""
# Imports de bibliothèques tierces
import pandas as pd
import streamlit as st
from sqlalchemy import func

# Imports de l'application
from config.app_config import ASSET_CATEGORIES, GEO_ZONES
from database.db_config import get_db_session  # Au lieu de get_db
from database.models import Bank, Account, Asset
from services.visualization_service import VisualizationService
from utils.session_manager import session_manager
from utils.visualizations import get_geo_zone_display_name


def show_analysis():
    """
    Affiche l'interface d'analyse et visualisations
    """
    # Récupérer l'ID utilisateur depuis le gestionnaire de session
    user_id = session_manager.get("user_id")

    if not user_id:
        st.error("Utilisateur non authentifié")
        return

    st.header("Analyses et Visualisations", anchor=False)

    # Utiliser le gestionnaire de contexte pour la session DB
    with get_db_session() as db:
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
                account_format = lambda x: "Tous" if x == "Tous" else next(
                    (acc.libelle for acc in bank_accounts if acc.id == x), "")
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
                # 1. Récupérer tous les actifs pertinents d'abord (sans filtres JSON)
                assets_query = db.query(Asset).filter(Asset.owner_id == user_id)

                # Appliquer les filtres non-JSON
                if filter_bank != "Toutes":
                    assets_query = assets_query.join(Account, Asset.account_id == Account.id)
                    assets_query = assets_query.filter(Account.bank_id == filter_bank)

                if filter_account != "Tous":
                    assets_query = assets_query.filter(Asset.account_id == filter_account)

                # Récupérer les actifs - SQLAlchemy déchiffrera les JSON automatiquement
                assets = assets_query.all()

                # 2. Filtrer en Python après déchiffrement
                filtered_assets = []
                total_filtered = 0.0

                for asset in assets:
                    # Appliquer filtre par catégorie si nécessaire
                    if filter_category != "Toutes":
                        if not asset.allocation or not isinstance(asset.allocation,
                                                                  dict) or filter_category not in asset.allocation:
                            continue

                    # Ajouter l'actif à la liste filtrée
                    filtered_assets.append(asset)

                    # Calculer la valeur totale
                    value = asset.value_eur if asset.value_eur is not None else asset.valeur_actuelle
                    if value:
                        total_filtered += value

                # Calculer le pourcentage
                total_all = sum(asset.value_eur or asset.valeur_actuelle or 0.0 for asset in assets)
                percentage = (total_filtered / total_all * 100) if total_all > 0 else 0

                st.markdown(
                    f"### Patrimoine sélectionné: {total_filtered:,.2f} € ({percentage:.1f}% du total)".replace(",",
                                                                                                                " "))

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
                        # Cette partie utilise JSON qui est problématique, on ne l'applique pas ici
                        # Nous filtrerons manuellement après
                        pass

                    # Grouper par banque et exécuter la requête
                    bank_values_query = bank_values_query.group_by(Bank.nom)
                    bank_values_result = bank_values_query.all()

                    # Convertir le résultat en dictionnaire pour le graphique
                    bank_values = {row[0]: row[1] for row in bank_values_result}

                    # Si un filtre de catégorie est actif, nous devons refiltrer manuellement
                    if filter_category != "Toutes":
                        # Calcul manuel des valeurs par banque pour la catégorie sélectionnée
                        corrected_bank_values = {}
                        for asset in filtered_assets:
                            # Trouver la banque de cet actif
                            account = next((acc for acc in assets_query.all() if acc.id == asset.account_id), None)
                            if account:
                                bank = next((b for b in banks if b.id == account.bank_id), None)
                                if bank:
                                    value = asset.value_eur if asset.value_eur is not None else asset.valeur_actuelle
                                    if bank.nom not in corrected_bank_values:
                                        corrected_bank_values[bank.nom] = 0
                                    corrected_bank_values[bank.nom] += value
                        bank_values = corrected_bank_values

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
                        # Cette partie utilise JSON qui est problématique, on ne l'applique pas ici
                        # Nous filtrerons manuellement après
                        pass

                    # Grouper par compte et exécuter la requête
                    account_values_query = account_values_query.group_by(Account.libelle)
                    account_values_result = account_values_query.all()

                    # Convertir le résultat en dictionnaire pour le graphique
                    account_values = {row[0]: row[1] for row in account_values_result}

                    # Si un filtre de catégorie est actif, nous devons refiltrer manuellement
                    if filter_category != "Toutes":
                        # Calcul manuel des valeurs par compte pour la catégorie sélectionnée
                        corrected_account_values = {}
                        for asset in filtered_assets:
                            # Trouver le compte de cet actif
                            account = next((acc for acc in db.query(Account).all() if acc.id == asset.account_id), None)
                            if account:
                                value = asset.value_eur if asset.value_eur is not None else asset.valeur_actuelle
                                if account.libelle not in corrected_account_values:
                                    corrected_account_values[account.libelle] = 0
                                corrected_account_values[account.libelle] += value
                        account_values = corrected_account_values

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
                        # Cette partie utilise JSON qui est problématique, on ne l'applique pas ici
                        # Nous filtrerons manuellement après
                        pass

                    # Grouper par type de produit et exécuter la requête
                    type_values_query = type_values_query.group_by(Asset.type_produit)
                    type_values_result = type_values_query.all()

                    # Convertir le résultat en dictionnaire pour le graphique, avec type capitalisé
                    type_values = {row[0].capitalize(): row[1] for row in type_values_result}

                    # Si un filtre de catégorie est actif, nous devons refiltrer manuellement
                    if filter_category != "Toutes":
                        # Calcul manuel des valeurs par type pour la catégorie sélectionnée
                        corrected_type_values = {}
                        for asset in filtered_assets:
                            type_name = asset.type_produit.capitalize()
                            value = asset.value_eur if asset.value_eur is not None else asset.valeur_actuelle
                            if type_name not in corrected_type_values:
                                corrected_type_values[type_name] = 0
                            corrected_type_values[type_name] += value
                        type_values = corrected_type_values

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
