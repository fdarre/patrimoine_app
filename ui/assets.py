"""
Interface de gestion des actifs, incluant les actifs composites
"""

import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, String  # Import func depuis sqlalchemy

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
                # Simplification du filtre par catégorie
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
                                if asset.allocation and isinstance(asset.allocation, dict):
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
                            if asset.composants and len(asset.composants) > 0:
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
                            if asset.allocation and isinstance(asset.allocation, dict):
                                try:
                                    geo_tabs = st.tabs([cat.capitalize() for cat in asset.allocation.keys()])

                                    for i, (category, percentage) in enumerate(asset.allocation.items()):
                                        with geo_tabs[i]:
                                            # Afficher le pourcentage de cette catégorie
                                            st.info(
                                                f"Cette catégorie représente {percentage}% de l'actif, soit {asset.valeur_actuelle * percentage / 100:,.2f} {asset.devise}".replace(
                                                    ",", " "))

                                            # Obtenir la répartition géographique effective pour cette catégorie
                                            if asset.composants and len(asset.composants) > 0:
                                                effective_geo = AssetService.calculate_effective_geo_allocation(db, asset.id, category)
                                                geo_zones = effective_geo.get(category, {})
                                                st.success("Répartition géographique effective (incluant les composants):")
                                            else:
                                                # Obtenir la répartition géographique pour cette catégorie
                                                geo_zones = asset.geo_allocation.get(category, {}) if asset.geo_allocation else {}

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
                                except Exception as e:
                                    st.error(f"Erreur lors de l'affichage des répartitions géographiques: {str(e)}")

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

                            # Reste du code pour l'édition d'actifs...
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

            # Variables pour stocker les allocations (Initialiser comme dictionnaire vide)
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

            # Section pour la répartition géographique par catégorie
            st.subheader("Répartition géographique par catégorie")

            # Objet pour stocker les répartitions géographiques
            geo_allocation = {}
            all_geo_valid = True

            # Conversion sécurisée en liste pour traitement
            allocation_items = list(allocation.items()) if allocation else []

            # Si aucune catégorie n'a été sélectionnée, afficher un message
            if not allocation_items:
                st.warning(
                    "Veuillez d'abord spécifier au moins une catégorie d'actif avec un pourcentage supérieur à 0%.")
            else:
                # Créer des onglets pour chaque catégorie avec allocation > 0
                geo_tabs = st.tabs([cat.capitalize() for cat, _ in allocation_items])

                # Pour chaque catégorie, demander la répartition géographique
                for i, (category, alloc_pct) in enumerate(allocation_items):
                    with geo_tabs[i]:
                        st.info(
                            f"Configuration de la répartition géographique pour la partie '{category}' ({alloc_pct}% de l'actif)")

                        # Obtenir une répartition par défaut selon la catégorie
                        default_geo = get_default_geo_zones(category)

                        # Variables pour stocker la répartition géographique
                        geo_zones = {}
                        geo_total = 0

                        # Créer des onglets pour faciliter la saisie
                        geo_zone_tabs = st.tabs(["Principales", "Secondaires", "Autres"])

                        with geo_zone_tabs[0]:
                            # Zones principales
                            main_zones = ["us", "europe", "japan", "emerging"]
                            cols = st.columns(2)
                            for j, zone in enumerate(main_zones):
                                with cols[j % 2]:
                                    pct = st.slider(
                                        f"{zone.capitalize()} (%)",
                                        min_value=0.0,
                                        max_value=100.0,
                                        value=float(default_geo.get(zone, 0.0)),
                                        step=1.0,
                                        key=f"new_asset_geo_{category}_{zone}"
                                    )
                                    if pct > 0:
                                        geo_zones[zone] = pct
                                        geo_total += pct

                        with geo_zone_tabs[1]:
                            # Zones secondaires
                            secondary_zones = ["uk", "china", "india", "developed"]
                            cols = st.columns(2)
                            for j, zone in enumerate(secondary_zones):
                                with cols[j % 2]:
                                    pct = st.slider(
                                        f"{zone.capitalize()} (%)",
                                        min_value=0.0,
                                        max_value=100.0,
                                        value=float(default_geo.get(zone, 0.0)),
                                        step=1.0,
                                        key=f"new_asset_geo_{category}_{zone}"
                                    )
                                    if pct > 0:
                                        geo_zones[zone] = pct
                                        geo_total += pct

                        with geo_zone_tabs[2]:
                            # Autres zones
                            other_zones = ["monde", "autre"]
                            cols = st.columns(2)
                            for j, zone in enumerate(other_zones):
                                with cols[j % 2]:
                                    pct = st.slider(
                                        f"{zone.capitalize()} (%)",
                                        min_value=0.0,
                                        max_value=100.0,
                                        value=float(default_geo.get(zone, 0.0)),
                                        step=1.0,
                                        key=f"new_asset_geo_{category}_{zone}"
                                    )
                                    if pct > 0:
                                        geo_zones[zone] = pct
                                        geo_total += pct

                        # Vérifier que le total est de 100%
                        st.progress(geo_total / 100)
                        if geo_total != 100:
                            all_geo_valid = False
                            st.warning(
                                f"Le total de la répartition géographique pour '{category}' doit être de 100%. Actuellement: {geo_total}%")
                        else:
                            st.success(f"Répartition géographique pour '{category}' valide (100%)")

                        # Enregistrer la répartition géographique pour cette catégorie
                        geo_allocation[category] = geo_zones

            # Option pour créer un actif composite
            st.subheader("Actif composite (optionnel)")
            is_composite = st.checkbox("Cet actif est composé d'autres actifs", key="new_asset_is_composite")

            composants = []
            components_valid = True
            components_total = 0

            if is_composite and assets:
                st.info("Sélectionnez les actifs qui composent cet actif, et spécifiez le pourcentage pour chacun.")
                st.warning(
                    "Le total des pourcentages des composants peut aller jusqu'à 100%. Le reste sera alloué directement selon l'allocation définie ci-dessus.")

                # Permettre l'ajout de composants (jusqu'à 5 pour commencer)
                num_components = st.number_input("Nombre de composants", min_value=0, max_value=10, value=1, step=1)

                for i in range(num_components):
                    st.markdown(f"### Composant {i + 1}")
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        component_id = st.selectbox(
                            f"Actif {i + 1}",
                            options=[a.id for a in assets],
                            format_func=lambda x: next((a.nom for a in assets if a.id == x), ""),
                            key=f"new_asset_component_{i}"
                        )

                    with col2:
                        component_pct = st.number_input(
                            f"Pourcentage {i + 1} (%)",
                            min_value=0.1,
                            max_value=100.0,
                            value=10.0,
                            step=0.1,
                            key=f"new_asset_component_pct_{i}"
                        )

                    components_total += component_pct
                    composants.append({"asset_id": component_id, "percentage": component_pct})

                # Afficher le total des composants
                st.progress(components_total / 100)
                if components_total > 100:
                    st.error(f"Le total des composants ({components_total}%) dépasse 100%")
                    components_valid = False
                else:
                    st.info(
                        f"Total des composants: {components_total}%. Reste alloué directement: {100 - components_total}%")

            # Bouton d'ajout avec gestion d'erreurs améliorée
            submit_button = st.button("Ajouter l'actif", key="btn_add_asset")

            if submit_button:
                if not asset_name:
                    st.error("Le nom de l'actif est obligatoire")
                elif not asset_account:
                    st.error("Veuillez sélectionner un compte")
                elif not asset_value:
                    st.error("La valeur actuelle est obligatoire")
                elif allocation_total != 100:
                    st.error(f"Le total des allocations doit être de 100% (actuellement: {allocation_total}%)")
                elif not all_geo_valid:
                    st.error("Toutes les répartitions géographiques doivent totaliser 100%")
                elif not components_valid:
                    st.error("Le total des composants ne doit pas dépasser 100%")
                else:
                    try:
                        # Convertir les valeurs
                        valeur_actuelle = float(asset_value)
                        prix_de_revient = float(asset_cost) if asset_cost else valeur_actuelle

                        # Ajouter l'actif
                        new_asset = AssetService.add_asset(
                            db=db,
                            user_id=user_id,
                            nom=asset_name,
                            compte_id=asset_account,
                            type_produit=asset_type,
                            allocation=allocation,
                            geo_allocation=geo_allocation,
                            valeur_actuelle=valeur_actuelle,
                            prix_de_revient=prix_de_revient,
                            devise=asset_currency,
                            notes=asset_notes,
                            todo=asset_todo,
                            composants=composants if is_composite else []
                        )

                        if new_asset:
                            # Mettre à jour l'historique
                            DataService.record_history_entry(db, user_id)
                            st.success(f"Actif '{asset_name}' ajouté avec succès.")
                            st.rerun()
                        else:
                            st.error("Erreur lors de l'ajout de l'actif.")
                    except ValueError:
                        st.error("Les valeurs numériques sont invalides. Vérifiez la valeur actuelle et le prix de revient.")
                    except Exception as e:
                        st.error(f"Erreur inattendue: {str(e)}")