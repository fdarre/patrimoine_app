"""
Interface de gestion des actifs
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
from utils.calculations import get_default_geo_zones

def show_asset_management(db: Session, user_id: str):
    """
    Affiche l'interface de gestion des actifs

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.header("Gestion des actifs", anchor=False)

    # Onglets pour les différentes fonctions de gestion d'actifs
    tab1, tab2, tab3 = st.tabs(["Liste des actifs", "Ajouter un actif", "Synchronisation"])

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
                            # Utiliser des onglets à l'intérieur de l'expander pour éviter les expanders imbriqués
                            detail_tabs = st.tabs(["Informations", "Valorisation"])

                            with detail_tabs[0]:
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.write("**Nom:**", asset.nom)
                                    st.write("**Type:**", asset.type_produit)
                                    if asset.isin:
                                        st.write("**Code ISIN:**", asset.isin)

                                    if asset.type_produit == "metal" and asset.ounces:
                                        st.write("**Onces:**", asset.ounces)

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
                                    if asset.last_price_sync:
                                        st.write("**Dernière synchro prix:**", asset.last_price_sync)
                                    if asset.notes:
                                        st.write("**Notes:**", asset.notes)

                                with col2:
                                    st.write("**Valeur actuelle:**",
                                             f"{asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " "))
                                    st.write("**Prix de revient:**",
                                             f"{asset.prix_de_revient:,.2f} {asset.devise}".replace(",", " "))

                                    if asset.devise != "EUR" and asset.exchange_rate:
                                        st.write("**Taux de change:**", f"1 {asset.devise} = {asset.exchange_rate:,.4f} EUR".replace(",", " "))
                                        if asset.value_eur:
                                            st.write("**Valeur en EUR:**", f"{asset.value_eur:,.2f} EUR".replace(",", " "))
                                        if asset.last_rate_sync:
                                            st.write("**Dernière synchro taux:**", asset.last_rate_sync)

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

                                # Afficher message d'erreur de synchronisation
                                if asset.sync_error:
                                    st.warning(f"Erreur de synchronisation: {asset.sync_error}")

                            with detail_tabs[1]:
                                st.subheader("Mise à jour de la valeur")

                                col1, col2 = st.columns(2)
                                with col1:
                                    new_price = st.number_input("Nouveau prix",
                                                              min_value=0.0,
                                                              value=float(asset.valeur_actuelle),
                                                              format="%.2f")
                                with col2:
                                    if st.button("Mettre à jour le prix manuellement"):
                                        if AssetService.update_manual_price(db, asset.id, new_price):
                                            st.success("Prix mis à jour avec succès")
                                            st.rerun()
                                        else:
                                            st.error("Erreur lors de la mise à jour du prix")

                                st.divider()

                                # Section pour synchronisation automatique des prix
                                st.subheader("Synchronisation automatique")

                                # Synchronisation par ISIN
                                if asset.isin:
                                    if st.button("Synchroniser via Yahoo Finance (ISIN)"):
                                        result = AssetService.sync_price_by_isin(db, asset.id)
                                        if result == 1:
                                            st.success(f"Prix synchronisé avec succès")
                                            st.rerun()
                                        else:
                                            st.error("Erreur lors de la synchronisation du prix")
                                else:
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        new_isin = st.text_input("Code ISIN", placeholder="FR0000000000")
                                    with col2:
                                        if st.button("Ajouter ISIN") and new_isin:
                                            # Mettre à jour l'actif avec le nouveau code ISIN
                                            updated_asset = AssetService.update_asset(
                                                db=db,
                                                asset_id=asset.id,
                                                nom=asset.nom,
                                                compte_id=asset.account_id,
                                                type_produit=asset.type_produit,
                                                allocation=asset.allocation,
                                                geo_allocation=asset.geo_allocation,
                                                valeur_actuelle=asset.valeur_actuelle,
                                                prix_de_revient=asset.prix_de_revient,
                                                devise=asset.devise,
                                                notes=asset.notes,
                                                todo=asset.todo,
                                                isin=new_isin,
                                                ounces=asset.ounces
                                            )
                                            if updated_asset:
                                                st.success("Code ISIN ajouté avec succès")
                                                st.rerun()

                                # Synchronisation pour les métaux précieux
                                if asset.type_produit == "metal":
                                    st.divider()
                                    st.subheader("Métaux précieux")

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if asset.ounces:
                                            st.write(f"Quantité actuelle: {asset.ounces} onces")
                                            new_ounces = st.number_input("Nouvelle quantité (onces)",
                                                                       min_value=0.0,
                                                                       value=float(asset.ounces),
                                                                       format="%.3f")
                                        else:
                                            new_ounces = st.number_input("Quantité (onces)",
                                                                     min_value=0.0,
                                                                     value=1.0,
                                                                     format="%.3f")

                                    with col2:
                                        metal_types = ["gold", "silver", "platinum", "palladium"]
                                        selected_metal = st.selectbox("Type de métal", options=metal_types)

                                        if st.button("Mettre à jour les onces"):
                                            # Mettre à jour l'actif avec la nouvelle quantité d'onces
                                            updated_asset = AssetService.update_asset(
                                                db=db,
                                                asset_id=asset.id,
                                                nom=asset.nom,
                                                compte_id=asset.account_id,
                                                type_produit=asset.type_produit,
                                                allocation=asset.allocation,
                                                geo_allocation=asset.geo_allocation,
                                                valeur_actuelle=asset.valeur_actuelle,
                                                prix_de_revient=asset.prix_de_revient,
                                                devise=asset.devise,
                                                notes=asset.notes,
                                                todo=asset.todo,
                                                isin=asset.isin,
                                                ounces=new_ounces
                                            )
                                            if updated_asset:
                                                st.success("Onces mises à jour avec succès")
                                                st.rerun()

                                    if st.button("Synchroniser le prix du métal"):
                                        result = AssetService.sync_metal_prices(db, asset.id)
                                        if result == 1:
                                            st.success(f"Prix du métal synchronisé avec succès")
                                            st.rerun()
                                        else:
                                            st.error("Erreur lors de la synchronisation du prix du métal")

                                # Synchronisation du taux de change
                                if asset.devise != "EUR":
                                    st.divider()
                                    st.subheader("Taux de change")

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if asset.exchange_rate:
                                            current_rate = asset.exchange_rate
                                        else:
                                            current_rate = 1.0

                                        new_rate = st.number_input(f"Taux de change (1 {asset.devise} en EUR)",
                                                                min_value=0.0001,
                                                                value=float(current_rate),
                                                                format="%.4f")

                                    with col2:
                                        if st.button("Mettre à jour le taux de change manuellement"):
                                            if AssetService.update_manual_exchange_rate(db, asset.id, new_rate):
                                                st.success("Taux de change mis à jour avec succès")
                                                st.rerun()
                                            else:
                                                st.error("Erreur lors de la mise à jour du taux de change")

                                    if st.button("Synchroniser le taux de change automatiquement"):
                                        result = AssetService.sync_currency_rates(db, asset.id)
                                        if result == 1:
                                            st.success(f"Taux de change synchronisé avec succès")
                                            st.rerun()
                                        else:
                                            st.error("Erreur lors de la synchronisation du taux de change")

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
                            col1, col2 = st.columns(2)

                            with col1:
                                if st.button("Modifier cet actif", key=f"btn_edit_asset_{selected_asset_id}"):
                                    st.session_state[f'edit_asset_{selected_asset_id}'] = True

                            with col2:
                                if st.button("Supprimer cet actif", key=f"btn_delete_asset_{selected_asset_id}"):
                                    if AssetService.delete_asset(db, selected_asset_id):
                                        # Mettre à jour l'historique
                                        DataService.record_history_entry(db, user_id)
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
                                    edit_isin = st.text_input("Code ISIN", value=asset.isin or "",
                                                              key=f"edit_asset_isin_{selected_asset_id}")

                                    if asset.type_produit == "metal" or edit_type == "metal":
                                        edit_ounces = st.number_input("Onces",
                                                                    value=float(asset.ounces) if asset.ounces else 0.0,
                                                                    format="%.3f",
                                                                    key=f"edit_asset_ounces_{selected_asset_id}")
                                    else:
                                        edit_ounces = asset.ounces

                                with col2:
                                    edit_account = st.selectbox(
                                        "Compte",
                                        options=list(db.query(Account).join(Bank).filter(Bank.owner_id == user_id).all()),
                                        index=next((i for i, acc in enumerate(db.query(Account).join(Bank).filter(Bank.owner_id == user_id).all())
                                                  if acc.id == asset.account_id), 0),
                                        format_func=lambda x: f"{x.libelle} ({x.id})",
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
                                            value=float(asset.allocation.get(category, 0.0)) if asset.allocation else 0.0,
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
                                            value=float(asset.allocation.get(category, 0.0)) if asset.allocation else 0.0,
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
                                        current_geo = asset.geo_allocation.get(category, get_default_geo_zones(category)) if asset.geo_allocation else get_default_geo_zones(category)

                                        # Interface pour éditer les pourcentages
                                        geo_zones = {}
                                        geo_total = 0

                                        # Créer des onglets pour faciliter la saisie
                                        geo_zone_tabs = st.tabs(["Marchés développés", "Marchés émergents", "Global"])

                                        with geo_zone_tabs[0]:
                                            # Zones principales
                                            main_zones = ["amerique_nord", "europe_zone_euro", "europe_hors_zone_euro", "japon"]
                                            cols = st.columns(2)
                                            for j, zone in enumerate(main_zones):
                                                with cols[j % 2]:
                                                    zone_display = {
                                                        "amerique_nord": "Amérique du Nord",
                                                        "europe_zone_euro": "Europe zone euro",
                                                        "europe_hors_zone_euro": "Europe hors zone euro",
                                                        "japon": "Japon"
                                                    }
                                                    pct = st.slider(
                                                        f"{zone_display.get(zone, zone.capitalize())} (%)",
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
                                            # Marchés émergents et Asie
                                            secondary_zones = ["chine", "inde", "asie_developpee", "autres_emergents"]
                                            cols = st.columns(2)
                                            for j, zone in enumerate(secondary_zones):
                                                with cols[j % 2]:
                                                    zone_display = {
                                                        "chine": "Chine",
                                                        "inde": "Inde",
                                                        "asie_developpee": "Asie développée",
                                                        "autres_emergents": "Autres émergents"
                                                    }
                                                    pct = st.slider(
                                                        f"{zone_display.get(zone, zone.capitalize())} (%)",
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
                                            # Global
                                            other_zones = ["global_non_classe"]
                                            cols = st.columns(2)
                                            for j, zone in enumerate(other_zones):
                                                with cols[j % 2]:
                                                    zone_display = {"global_non_classe": "Global/Non classé"}
                                                    pct = st.slider(
                                                        f"{zone_display.get(zone, zone.capitalize())} (%)",
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
                                all_geo_valid = all(
                                    sum(geo.values()) == 100 for cat, geo in new_geo_allocation.items())

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
                                                db=db,
                                                asset_id=selected_asset_id,
                                                nom=edit_name,
                                                compte_id=edit_account.id,
                                                type_produit=edit_type,
                                                allocation=new_allocation,
                                                geo_allocation=new_geo_allocation,
                                                valeur_actuelle=valeur_actuelle,
                                                prix_de_revient=prix_de_revient,
                                                devise=edit_currency,
                                                notes=edit_notes,
                                                todo=edit_todo,
                                                isin=edit_isin if edit_isin else None,
                                                ounces=edit_ounces if edit_type == "metal" else None
                                            )

                                            if updated_asset:
                                                # Mettre à jour l'historique
                                                DataService.record_history_entry(db, user_id)

                                                st.success("Actif mis à jour avec succès")
                                                st.session_state[f'edit_asset_{selected_asset_id}'] = False
                                                st.rerun()
                                            else:
                                                st.error("Erreur lors de la mise à jour de l'actif")
                                        except ValueError as e:
                                            st.error(f"Valeurs numériques invalides: {str(e)}")

                                with col2:
                                    if st.button("Annuler", key=f"btn_cancel_asset_{selected_asset_id}"):
                                        st.session_state[f'edit_asset_{selected_asset_id}'] = False
                                        st.rerun()
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

                # Champs spécifiques selon le type
                if asset_type == "metal":
                    asset_ounces = st.number_input("Quantité (onces)", min_value=0.0, value=1.0, format="%.3f")
                else:
                    asset_ounces = None

                asset_isin = st.text_input("Code ISIN (optionnel)",
                                           key="new_asset_isin",
                                           help="Pour les ETF, actions et obligations")

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
                        geo_zone_tabs = st.tabs(["Marchés développés", "Marchés émergents", "Global"])

                        with geo_zone_tabs[0]:
                            # Marchés développés principaux
                            main_zones = ["amerique_nord", "europe_zone_euro", "europe_hors_zone_euro", "japon"]
                            cols = st.columns(2)
                            for j, zone in enumerate(main_zones):
                                with cols[j % 2]:
                                    zone_display = {
                                        "amerique_nord": "Amérique du Nord",
                                        "europe_zone_euro": "Europe zone euro",
                                        "europe_hors_zone_euro": "Europe hors zone euro",
                                        "japon": "Japon"
                                    }
                                    pct = st.slider(
                                        f"{zone_display.get(zone, zone.capitalize())} (%)",
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
                            # Marchés émergents et Asie
                            secondary_zones = ["chine", "inde", "asie_developpee", "autres_emergents"]
                            cols = st.columns(2)
                            for j, zone in enumerate(secondary_zones):
                                with cols[j % 2]:
                                    zone_display = {
                                        "chine": "Chine",
                                        "inde": "Inde",
                                        "asie_developpee": "Asie développée",
                                        "autres_emergents": "Autres émergents"
                                    }
                                    pct = st.slider(
                                        f"{zone_display.get(zone, zone.capitalize())} (%)",
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
                            # Global
                            other_zones = ["global_non_classe"]
                            cols = st.columns(2)
                            for j, zone in enumerate(other_zones):
                                with cols[j % 2]:
                                    zone_display = {"global_non_classe": "Global/Non classé"}
                                    pct = st.slider(
                                        f"{zone_display.get(zone, zone.capitalize())} (%)",
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

            # Bouton d'ajout d'actif
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

    with tab3:
        st.subheader("Synchronisation automatique")

        # Interface de synchronisation globale
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Synchronisation des taux de change")
            if st.button("Synchroniser tous les taux de change"):
                updated_count = AssetService.sync_currency_rates(db)
                if updated_count > 0:
                    st.success(f"{updated_count} actif(s) mis à jour avec succès")
                    # Mettre à jour l'historique
                    DataService.record_history_entry(db, user_id)
                else:
                    st.info("Aucun actif à mettre à jour ou erreur lors de la synchronisation")

        with col2:
            st.markdown("### Synchronisation des prix par ISIN")
            if st.button("Synchroniser tous les prix via ISIN"):
                updated_count = AssetService.sync_price_by_isin(db)
                if updated_count > 0:
                    st.success(f"{updated_count} actif(s) mis à jour avec succès")
                    # Mettre à jour l'historique
                    DataService.record_history_entry(db, user_id)
                else:
                    st.info("Aucun actif avec un ISIN à mettre à jour ou erreur lors de la synchronisation")

        # Interface de synchronisation des métaux précieux
        st.markdown("### Synchronisation des métaux précieux")
        if st.button("Synchroniser tous les prix des métaux précieux"):
            updated_count = AssetService.sync_metal_prices(db)
            if updated_count > 0:
                st.success(f"{updated_count} actif(s) métaux précieux mis à jour avec succès")
                # Mettre à jour l'historique
                DataService.record_history_entry(db, user_id)
            else:
                st.info("Aucun actif métal à mettre à jour ou erreur lors de la synchronisation")

        # Table des actifs avec leur dernière synchronisation
        st.markdown("### État de synchronisation des actifs")

        sync_assets = db.query(Asset).filter(Asset.owner_id == user_id).all()

        if sync_assets:
            sync_data = []
            for asset in sync_assets:
                last_price_sync = asset.last_price_sync.strftime(
                    "%Y-%m-%d %H:%M") if asset.last_price_sync else "Jamais"
                last_rate_sync = asset.last_rate_sync.strftime("%Y-%m-%d %H:%M") if asset.last_rate_sync else "Jamais"

                sync_data.append([
                    asset.nom,
                    asset.isin or "-",
                    asset.devise,
                    last_price_sync,
                    last_rate_sync,
                    asset.sync_error or "-"
                ])

            sync_df = pd.DataFrame(sync_data,
                                   columns=["Nom", "ISIN", "Devise", "Dernière synchro prix", "Dernière synchro taux",
                                            "Erreur"])
            st.dataframe(sync_df, use_container_width=True)
        else:
            st.info("Aucun actif disponible")