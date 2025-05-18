"""
Interface de gestion des actifs, incluant les actifs composites
"""

from typing import Dict, List, Any

import pandas as pd
import streamlit as st

from config.app_config import PRODUCT_TYPES, ASSET_CATEGORIES, CURRENCIES
from database.models import Asset
from services.asset_service import AssetService
from services.data_service import DataService
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

                            # Formulaire d'édition conditionnel
                            if f'edit_asset_{selected_asset_id}' in st.session_state and st.session_state[
                                f'edit_asset_{selected_asset_id}']:
                                st.subheader("Modifier l'actif")

                                col1, col2 = st.columns(2)

                                with col1:
                                    edit_name = st.text_input("Nom", value=asset.nom,
                                                              key=f"edit_asset_name_{selected_asset_id}")
                                    edit_type = st.selectbox(
                                        "Type de produit",
                                        options=PRODUCT_TYPES,
                                        index=PRODUCT_TYPES.index(asset.type_produit),
                                        key=f"edit_asset_type_{selected_asset_id}"
                                    )
                                    edit_notes = st.text_area("Notes", value=asset.notes,
                                                              key=f"edit_asset_notes_{selected_asset_id}")

                                with col2:
                                    edit_account = st.selectbox(
                                        "Compte",
                                        options=list(accounts.keys()),
                                        index=list(accounts.keys()).index(asset.compte_id),
                                        format_func=lambda x: f"{accounts[x]['libelle']} ({x})",
                                        key=f"edit_asset_account_{selected_asset_id}"
                                    )
                                    edit_value = st.text_input("Valeur actuelle", value=str(asset.valeur_actuelle),
                                                               key=f"edit_asset_value_{selected_asset_id}")
                                    edit_cost = st.text_input("Prix de revient", value=str(asset.prix_de_revient),
                                                              key=f"edit_asset_cost_{selected_asset_id}")
                                    edit_currency = st.selectbox(
                                        "Devise",
                                        options=CURRENCIES,
                                        index=CURRENCIES.index(asset.devise),
                                        key=f"edit_asset_currency_{selected_asset_id}"
                                    )
                                    edit_todo = st.text_area("Tâche à faire", value=asset.todo,
                                                             key=f"edit_asset_todo_{selected_asset_id}")

                                # Édition des allocations par catégorie
                                st.subheader("Allocation par catégorie")
                                st.info(
                                    "Répartissez la valeur de l'actif entre les différentes catégories (total 100%)")

                                # Créer un conteneur pour les sliders d'allocation
                                allocation_col1, allocation_col2 = st.columns(2)

                                # Variables pour stocker les nouvelles allocations
                                new_allocation = {}
                                allocation_total = 0

                                # Première colonne: principaux types d'actifs
                                with allocation_col1:
                                    for category in ["actions", "obligations", "immobilier", "cash"]:
                                        percentage = st.slider(
                                            f"{category.capitalize()} (%)",
                                            min_value=0.0,
                                            max_value=100.0,
                                            value=float(asset.allocation.get(category, 0.0)),
                                            step=1.0,
                                            key=f"edit_asset_alloc_{selected_asset_id}_{category}"
                                        )
                                        if percentage > 0:
                                            new_allocation[category] = percentage
                                            allocation_total += percentage

                                # Deuxième colonne: autres types d'actifs
                                with allocation_col2:
                                    for category in ["crypto", "metaux", "autre"]:
                                        percentage = st.slider(
                                            f"{category.capitalize()} (%)",
                                            min_value=0.0,
                                            max_value=100.0,
                                            value=float(asset.allocation.get(category, 0.0)),
                                            step=1.0,
                                            key=f"edit_asset_alloc_{selected_asset_id}_{category}"
                                        )
                                        if percentage > 0:
                                            new_allocation[category] = percentage
                                            allocation_total += percentage

                                # Vérifier que le total est de 100%
                                st.progress(allocation_total / 100)
                                if allocation_total != 100:
                                    st.warning(
                                        f"Le total des allocations doit être de 100%. Actuellement: {allocation_total}%")
                                else:
                                    st.success("Allocation valide (100%)")

                                # Édition de la répartition géographique par catégorie
                                st.subheader("Répartition géographique par catégorie")

                                # Créer un objet pour stocker les nouvelles répartitions géographiques
                                new_geo_allocation = {}

                                # Utiliser des onglets pour chaque catégorie ayant une allocation > 0
                                geo_tabs = st.tabs([cat.capitalize() for cat in new_allocation.keys()])

                                for i, (category, allocation_pct) in enumerate(new_allocation.items()):
                                    with geo_tabs[i]:
                                        st.info(
                                            f"Configuration de la répartition géographique pour la partie '{category}' ({allocation_pct}% de l'actif)")

                                        # Obtenir la répartition actuelle ou une répartition par défaut
                                        current_geo = asset.geo_allocation.get(category,
                                                                               get_default_geo_zones(category))

                                        # Interface pour éditer les pourcentages
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
                                                        value=float(current_geo.get(zone, 0.0)),
                                                        step=1.0,
                                                        key=f"edit_asset_geo_{selected_asset_id}_{category}_{zone}"
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
                                                        value=float(current_geo.get(zone, 0.0)),
                                                        step=1.0,
                                                        key=f"edit_asset_geo_{selected_asset_id}_{category}_{zone}"
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
                                                        value=float(current_geo.get(zone, 0.0)),
                                                        step=1.0,
                                                        key=f"edit_asset_geo_{selected_asset_id}_{category}_{zone}"
                                                    )
                                                    if pct > 0:
                                                        geo_zones[zone] = pct
                                                        geo_total += pct

                                        # Vérifier que le total est de 100%
                                        st.progress(geo_total / 100)
                                        if geo_total != 100:
                                            st.warning(
                                                f"Le total de la répartition géographique pour '{category}' doit être de 100%. Actuellement: {geo_total}%")
                                        else:
                                            st.success(f"Répartition géographique pour '{category}' valide (100%)")

                                        # Enregistrer la répartition géographique pour cette catégorie
                                        new_geo_allocation[category] = geo_zones

                                # Validation globale
                                all_geo_valid = all(sum(geo.values()) == 100 for cat, geo in new_geo_allocation.items())

                                col1, col2 = st.columns(2)

                                with col1:
                                    if st.button("Enregistrer les modifications",
                                                 key=f"btn_save_asset_{selected_asset_id}",
                                                 disabled=allocation_total != 100 or not all_geo_valid):
                                        try:
                                            valeur_actuelle = float(edit_value)
                                            prix_de_revient = float(edit_cost)

                                            # Mettre à jour l'actif
                                            updated_asset = AssetService.update_asset(
                                                assets=assets,
                                                asset_id=selected_asset_id,
                                                nom=edit_name,
                                                compte_id=edit_account,
                                                type_produit=edit_type,
                                                allocation=new_allocation,
                                                geo_allocation=new_geo_allocation,
                                                valeur_actuelle=valeur_actuelle,
                                                prix_de_revient=prix_de_revient,
                                                devise=edit_currency,
                                                notes=edit_notes,
                                                todo=edit_todo
                                            )

                                            if updated_asset:
                                                # Mettre à jour l'historique
                                                history = DataService.record_history_entry(assets, history)
                                                DataService.save_data(banks, accounts, assets, history)

                                                st.success("Actif mis à jour avec succès")
                                                st.session_state[f'edit_asset_{selected_asset_id}'] = False
                                                st.rerun()
                                            else:
                                                st.error("Erreur lors de la mise à jour de l'actif")
                                        except ValueError:
                                            st.error("Valeurs numériques invalides")

                                with col2:
                                    if st.button("Annuler", key=f"btn_cancel_asset_{selected_asset_id}"):
                                        st.session_state[f'edit_asset_{selected_asset_id}'] = False
                                        st.rerun()

                            # Formulaire de gestion des composants
                            if f'edit_components_{selected_asset_id}' in st.session_state and st.session_state[
                                f'edit_components_{selected_asset_id}']:
                                st.subheader("Gérer les composants de l'actif")

                                # Afficher les composants actuels
                                if asset.composants and len(asset.composants) > 0:
                                    st.markdown("### Composants actuels")

                                    for i, component in enumerate(asset.composants):
                                        component_asset = AssetService.find_asset_by_id(assets, component["asset_id"])
                                        if component_asset:
                                            col1, col2 = st.columns([3, 1])
                                            with col1:
                                                st.markdown(f"""
                                                <div class="component-card">
                                                <strong>{component_asset.nom}</strong> - {component['percentage']}% 
                                                ({component_asset.valeur_actuelle * component['percentage'] / 100:,.2f} {component_asset.devise})
                                                </div>
                                                """, unsafe_allow_html=True)
                                            with col2:
                                                if st.button("Supprimer", key=f"remove_comp_{selected_asset_id}_{i}"):
                                                    asset.remove_component(component["asset_id"])
                                                    DataService.save_data(banks, accounts, assets, history)
                                                    st.success(f"Composant {component_asset.nom} supprimé.")
                                                    st.rerun()

                                    # Afficher le total des pourcentages
                                    total_percentage = asset.get_components_total_percentage()
                                    st.progress(total_percentage / 100)

                                    if total_percentage > 100:
                                        st.error(
                                            f"Le total des pourcentages des composants ({total_percentage}%) dépasse 100%.")
                                    else:
                                        st.info(
                                            f"Total des composants: {total_percentage}%. Reste à allouer directement: {100 - total_percentage}%")
                                else:
                                    st.info("Cet actif n'a pas encore de composants.")

                                # Ajouter un nouveau composant
                                st.markdown("### Ajouter un composant")

                                # Filtrer les actifs possibles comme composants (éviter les références circulaires)
                                possible_components = []
                                for candidate in assets:
                                    # Ne pas inclure l'actif lui-même
                                    if candidate.id == selected_asset_id:
                                        continue

                                    # Vérifier qu'il n'y a pas de référence circulaire
                                    if not is_circular_reference(assets, selected_asset_id, candidate.id):
                                        possible_components.append(candidate)

                                if possible_components:
                                    col1, col2 = st.columns([3, 1])

                                    with col1:
                                        new_component_id = st.selectbox(
                                            "Actif à ajouter comme composant",
                                            options=[comp.id for comp in possible_components],
                                            format_func=lambda x: next(
                                                (a.nom for a in possible_components if a.id == x), ""),
                                            key=f"new_comp_id_{selected_asset_id}"
                                        )

                                    with col2:
                                        new_comp_percentage = st.number_input(
                                            "Pourcentage (%)",
                                            min_value=0.1,
                                            max_value=100.0,
                                            value=10.0,
                                            step=0.1,
                                            key=f"new_comp_pct_{selected_asset_id}"
                                        )

                                    # Calculer le pourcentage total après ajout
                                    new_total = asset.get_components_total_percentage() + new_comp_percentage

                                    if new_total > 100:
                                        st.warning(
                                            f"Le total des pourcentages ({new_total}%) dépassera 100%. Ajustez le pourcentage.")
                                        add_disabled = True
                                    else:
                                        add_disabled = False

                                    if st.button("Ajouter le composant", disabled=add_disabled,
                                                 key=f"add_comp_btn_{selected_asset_id}"):
                                        # Ajouter le composant
                                        asset.add_component(new_component_id, new_comp_percentage)

                                        # Sauvegarder les changements
                                        DataService.save_data(banks, accounts, assets, history)

                                        st.success("Composant ajouté avec succès.")
                                        st.rerun()
                                else:
                                    st.warning("Aucun actif disponible à ajouter comme composant.")

                                if st.button("Terminer", key=f"finish_components_{selected_asset_id}"):
                                    st.session_state[f'edit_components_{selected_asset_id}'] = False
                                    st.rerun()
            else:
                st.info("Aucun actif ne correspond aux filtres sélectionnés.")

    with tab2:
        st.subheader("Ajouter un nouvel actif")

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
                # Filtrer les comptes par banque pour une meilleure organisation
                asset_bank = st.selectbox(
                    "Banque",
                    options=list(banks.keys()),
                    format_func=lambda x: f"{banks[x]['nom']}",
                    key="new_asset_bank"
                )

                # Filtrer les comptes selon la banque sélectionnée
                bank_accounts = {k: v for k, v in accounts.items() if v["banque_id"] == asset_bank}

                if bank_accounts:
                    asset_account = st.selectbox(
                        "Compte",
                        options=list(bank_accounts.keys()),
                        format_func=lambda x: f"{accounts[x]['libelle']} ({x})",
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

            # Section pour la répartition géographique par catégorie
            st.subheader("Répartition géographique par catégorie")

            # Objet pour stocker les répartitions géographiques
            geo_allocation = {}

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

                if is_composite and assets:
                    st.info("Sélectionnez les actifs qui composent cet actif, et spécifiez le pourcentage pour chacun.")
                    st.warning(
                        "Le total des pourcentages des composants peut aller jusqu'à 100%. Le reste sera alloué directement selon l'allocation définie ci-dessus.")

                    # Permettre l'ajout de composants (jusqu'à 5 pour commencer)
                    num_components = st.number_input("Nombre de composants", min_value=0, max_value=10, value=1, step=1)

                    components_total = 0

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
                    else:
                        st.info(
                            f"Total des composants: {components_total}%. Reste alloué directement: {100 - components_total}%")

                # Vérification globale
                all_geo_valid = all(
                    sum(geo.values()) == 100 for cat, geo in geo_allocation.items() if cat in allocation)
                components_valid = not is_composite or (is_composite and components_total <= 100)

                # Bouton d'ajout d'actif
                if st.button("Ajouter l'actif", key="btn_add_asset",
                             disabled=not asset_name or not asset_account or not asset_value or
                                      not all_geo_valid or allocation_total != 100 or not components_valid):
                    try:
                        # Convertir les valeurs
                        valeur_actuelle = float(asset_value)
                        prix_de_revient = float(asset_cost) if asset_cost else valeur_actuelle

                        # Ajouter l'actif
                        new_asset = AssetService.add_asset(
                            assets=assets,
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

                        # Mettre à jour l'historique
                        history = DataService.record_history_entry(assets, history)

                        # Sauvegarder les données
                        DataService.save_data(banks, accounts, assets, history)

                        st.success(f"Actif '{asset_name}' ajouté avec succès.")
                        st.rerun()
                    except ValueError:
                        st.error("Les valeurs numériques sont invalides.")