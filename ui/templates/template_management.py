"""
Interface utilisateur pour la gestion des modèles d'actifs
"""
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.models import Asset, Account, Bank
from services.template_service import template_service
from utils.ui_helpers import show_message
from datetime import datetime
from utils.calculations import get_default_geo_zones


def show_template_management(db: Session, user_id: str):
    """
    Affiche l'interface de gestion des modèles d'actifs

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.header("Gestion des modèles d'actifs")
    st.markdown("""
    Cette page vous permet de gérer des modèles d'actifs qui servent de références pour d'autres actifs.
    Les modifications apportées aux allocations et répartitions géographiques d'un modèle peuvent être 
    propagées automatiquement à tous les actifs qui y sont liés.
    """)

    tabs = st.tabs(["Modèles existants", "Créer un modèle", "Lier des actifs"])

    with tabs[0]:
        show_existing_templates(db, user_id)

    with tabs[1]:
        show_create_template(db, user_id)

    with tabs[2]:
        show_link_to_template(db, user_id)


def show_existing_templates(db: Session, user_id: str):
    """
    Affiche les modèles existants et permet de propager leurs modifications

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.subheader("Modèles d'actifs existants")

    # Récupérer tous les modèles de l'utilisateur
    templates = template_service.get_templates(db, user_id)

    if not templates:
        st.info("Vous n'avez pas encore créé de modèles d'actifs.")
        return

    # Afficher un tableau des modèles existants
    template_data = []
    for template in templates:
        # Compter les actifs liés à ce modèle
        linked_count = len(template_service.get_linked_assets(db, template.id))

        template_data.append({
            "ID": template.id,
            "Nom du modèle": template.template_name,
            "Actif source": template.nom,
            "Type": template.type_produit,
            "Actifs liés": linked_count
        })

    if template_data:
        df = pd.DataFrame(template_data)
        st.dataframe(df.drop(columns=["ID"]), use_container_width=True)

        # Sélectionner un modèle pour en voir les détails et propager les changements
        selected_template_id = st.selectbox(
            "Sélectionner un modèle pour le gérer",
            options=[t["ID"] for t in template_data],
            format_func=lambda x: next((t["Nom du modèle"] for t in template_data if t["ID"] == x), "")
        )

        if selected_template_id:
            # Récupérer le modèle sélectionné
            selected_template = next((t for t in templates if t.id == selected_template_id), None)

            if selected_template:
                show_template_details(db, selected_template)


def show_template_details(db: Session, template: Asset):
    """
    Affiche les détails d'un modèle et ses actifs liés, avec possibilité de modification

    Args:
        db: Session de base de données
        template: Le modèle à afficher
    """
    st.subheader(f"Détails du modèle: {template.template_name}")

    # Ajouter un onglet pour afficher et modifier le modèle
    edit_tabs = st.tabs(
        ["📊 Afficher les allocations", "✏️ Modifier les allocations", "🌎 Modifier la répartition géographique"])

    with edit_tabs[0]:
        # Afficher les allocations (mode lecture seule)
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Allocation par catégorie:**")
            if template.allocation:
                for cat, percent in template.allocation.items():
                    st.write(f"- {cat.capitalize()}: {percent}%")
            else:
                st.write("Aucune allocation définie")

        with col2:
            st.write("**Géographie par catégorie:**")
            if template.geo_allocation:
                for cat, zones in template.geo_allocation.items():
                    st.write(f"**{cat.capitalize()}:**")
                    for zone, percent in zones.items():
                        st.write(f"  - {zone.capitalize()}: {percent}%")
            else:
                st.write("Aucune répartition géographique définie")

    with edit_tabs[1]:
        # Interface pour modifier l'allocation
        st.write("**Modifier l'allocation par catégorie:**")

        # Récupérer l'allocation actuelle
        current_allocation = template.allocation.copy() if template.allocation else {}

        # Variables pour stocker les nouvelles allocations
        new_allocation = {}
        allocation_total = 0

        # Interface avec deux colonnes
        col1, col2 = st.columns(2)

        # Première colonne: principaux types d'actifs
        with col1:
            for category in ["actions", "obligations", "immobilier", "cash"]:
                percentage = st.slider(
                    f"{category.capitalize()} (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(current_allocation.get(category, 0.0)),
                    step=1.0,
                    key=f"edit_template_alloc_{template.id}_{category}"
                )
                if percentage > 0:
                    new_allocation[category] = percentage
                    allocation_total += percentage

        # Deuxième colonne: autres types d'actifs
        with col2:
            for category in ["crypto", "metaux", "autre"]:
                percentage = st.slider(
                    f"{category.capitalize()} (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(current_allocation.get(category, 0.0)),
                    step=1.0,
                    key=f"edit_template_alloc_{template.id}_{category}"
                )
                if percentage > 0:
                    new_allocation[category] = percentage
                    allocation_total += percentage

        # Vérifier que le total est de 100%
        st.progress(allocation_total / 100)

        allocation_valid = allocation_total == 100

        if not allocation_valid:
            st.warning(f"Le total des allocations doit être de 100%. Actuellement: {allocation_total}%")
        else:
            st.success("Allocation valide (100%)")

            # Bouton pour sauvegarder les modifications d'allocation
            if st.button("Sauvegarder l'allocation", key="save_template_allocation"):
                # Mettre à jour l'allocation du modèle
                template.allocation = new_allocation
                template.date_maj = datetime.now().strftime("%Y-%m-%d")
                db.commit()
                st.success("Allocation du modèle mise à jour avec succès!")
                st.rerun()

    with edit_tabs[2]:
        # Interface pour modifier la répartition géographique
        st.write("**Modifier la répartition géographique:**")

        # Récupérer l'allocation actuelle pour les catégories disponibles
        current_allocation = template.allocation.copy() if template.allocation else {}
        current_geo = template.geo_allocation.copy() if template.geo_allocation else {}

        # S'il n'y a pas d'allocation, informer l'utilisateur
        if not current_allocation:
            st.warning("Veuillez d'abord définir l'allocation par catégorie.")
        else:
            # Créer des onglets pour chaque catégorie avec allocation > 0
            geo_tabs = st.tabs([cat.capitalize() for cat, pct in current_allocation.items() if pct > 0])

            # Variables pour suivre la validité de la répartition géographique
            new_geo_allocation = {}
            all_geo_valid = True

            # Pour chaque catégorie, créer une interface de répartition géographique
            for i, (category, allocation_pct) in enumerate(
                    [(cat, pct) for cat, pct in current_allocation.items() if pct > 0]):
                with geo_tabs[i]:
                    st.info(
                        f"Configuration de la répartition géographique pour la partie '{category}' ({allocation_pct}% de l'actif)")

                    # Obtenir la répartition actuelle ou une répartition par défaut
                    current_category_geo = current_geo.get(category, get_default_geo_zones(category))

                    # Interface pour éditer les pourcentages
                    geo_zones = {}
                    geo_total = 0

                    # Créer des onglets pour faciliter la saisie
                    geo_zone_tabs = st.tabs(["Principales", "Secondaires", "Autres"])

                    with geo_zone_tabs[0]:
                        # Zones principales
                        main_zones = ["amerique_nord", "europe_zone_euro", "europe_hors_zone_euro", "japon"]
                        cols = st.columns(2)
                        for j, zone in enumerate(main_zones):
                            with cols[j % 2]:
                                pct = st.slider(
                                    f"{zone.capitalize()} (%)",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=float(current_category_geo.get(zone, 0.0)),
                                    step=1.0,
                                    key=f"edit_template_geo_{template.id}_{category}_{zone}"
                                )
                                if pct > 0:
                                    geo_zones[zone] = pct
                                    geo_total += pct

                    with geo_zone_tabs[1]:
                        # Zones secondaires
                        secondary_zones = ["chine", "inde", "asie_developpee", "autres_emergents"]
                        cols = st.columns(2)
                        for j, zone in enumerate(secondary_zones):
                            with cols[j % 2]:
                                pct = st.slider(
                                    f"{zone.capitalize()} (%)",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=float(current_category_geo.get(zone, 0.0)),
                                    step=1.0,
                                    key=f"edit_template_geo_{template.id}_{category}_{zone}"
                                )
                                if pct > 0:
                                    geo_zones[zone] = pct
                                    geo_total += pct

                    with geo_zone_tabs[2]:
                        # Autres zones
                        other_zones = ["global_non_classe"]
                        cols = st.columns(2)
                        for j, zone in enumerate(other_zones):
                            with cols[j % 2]:
                                pct = st.slider(
                                    f"{zone.capitalize()} (%)",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=float(current_category_geo.get(zone, 0.0)),
                                    step=1.0,
                                    key=f"edit_template_geo_{template.id}_{category}_{zone}"
                                )
                                if pct > 0:
                                    geo_zones[zone] = pct
                                    geo_total += pct

                    # Vérifier que le total est de 100%
                    st.progress(geo_total / 100)

                    geo_valid = geo_total == 100
                    if not geo_valid:
                        all_geo_valid = False
                        if geo_total < 100:
                            st.warning(
                                f"Le total de la répartition géographique pour '{category}' doit être de 100%. Actuellement: {geo_total}%")
                        else:
                            st.error(
                                f"Le total de la répartition géographique pour '{category}' ne doit pas dépasser 100%. Actuellement: {geo_total}%")
                    else:
                        st.success(f"Répartition géographique pour '{category}' valide (100%)")

                    # Enregistrer la répartition géographique pour cette catégorie
                    new_geo_allocation[category] = geo_zones

            # Bouton pour sauvegarder les modifications de répartition géographique
            if all_geo_valid and st.button("Sauvegarder la répartition géographique", key="save_template_geo"):
                # Mettre à jour la répartition géographique du modèle
                template.geo_allocation = new_geo_allocation
                template.date_maj = datetime.now().strftime("%Y-%m-%d")
                db.commit()
                st.success("Répartition géographique du modèle mise à jour avec succès!")
                st.rerun()

    # Section pour les actifs liés au modèle
    st.markdown("---")
    st.subheader("Actifs liés")

    # Récupérer les actifs liés à ce modèle
    linked_assets = template_service.get_linked_assets(db, template.id)

    if linked_assets:
        st.subheader(f"Actifs liés à ce modèle ({len(linked_assets)})")

        linked_data = []
        for asset in linked_assets:
            linked_data.append({
                "ID": asset.id,
                "Nom": asset.nom,
                "Type": asset.type_produit,
                "Synchronisation": "Activée" if asset.sync_allocations else "Désactivée"
            })

        if linked_data:
            df = pd.DataFrame(linked_data)
            st.dataframe(df.drop(columns=["ID"]), use_container_width=True)

        # Bouton pour propager les modifications
        if st.button("Propager les modifications aux actifs liés"):
            updated_count = template_service.propagate_template_changes(db, template.id)
            if updated_count > 0:
                st.success(f"Modifications propagées à {updated_count} actifs liés")
            else:
                st.warning("Aucun actif n'a été mis à jour")
    else:
        st.info("Aucun actif n'est lié à ce modèle pour le moment.")


def show_create_template(db: Session, user_id: str):
    """
    Affiche l'interface pour créer un nouveau modèle à partir d'un actif existant

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.subheader("Créer un nouveau modèle d'actifs")
    st.markdown("""
    Désignez un actif existant comme modèle de référence. 
    Ses allocations et répartitions géographiques serviront de base pour d'autres actifs.
    """)

    # Récupérer les candidats pour devenir des modèles
    candidates = template_service.get_template_candidates(db, user_id)

    if not candidates:
        st.info(
            "Aucun actif éligible pour devenir un modèle. Vous devez créer des actifs qui ne sont pas déjà liés à un modèle.")
        return

    # Sélectionner un actif
    candidate_id = st.selectbox(
        "Sélectionner un actif",
        options=[c.id for c in candidates],
        format_func=lambda x: next((f"{c.nom} ({c.type_produit})" for c in candidates if c.id == x), "")
    )

    selected_candidate = next((c for c in candidates if c.id == candidate_id), None)

    if selected_candidate:
        # Afficher les allocations
        st.write("**Allocations de l'actif sélectionné:**")

        if selected_candidate.allocation:
            col1, col2 = st.columns(2)
            with col1:
                for cat, percent in selected_candidate.allocation.items():
                    if percent > 0:
                        st.write(f"- {cat.capitalize()}: {percent}%")

        # Champ pour le nom du modèle
        template_name = st.text_input(
            "Nom du modèle",
            value=f"Modèle {selected_candidate.nom}",
            help="Donnez un nom descriptif à ce modèle pour le retrouver facilement"
        )

        # Bouton pour créer le modèle
        if st.button("Créer le modèle"):
            if template_service.create_template(db, candidate_id, template_name):
                st.success(f"Modèle '{template_name}' créé avec succès")
                st.rerun()
            else:
                st.error("Erreur lors de la création du modèle")


def show_link_to_template(db: Session, user_id: str):
    """
    Affiche l'interface pour lier des actifs existants à un modèle

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.subheader("Lier des actifs à un modèle")
    st.markdown("""
    Liez des actifs existants à un modèle pour qu'ils puissent hériter de ses allocations et 
    répartitions géographiques, maintenant ou lors de futures mises à jour.
    """)

    # Récupérer les modèles disponibles
    templates = template_service.get_templates(db, user_id)

    if not templates:
        st.info("Aucun modèle disponible. Veuillez d'abord créer un modèle.")
        return

    # Sélectionner un modèle
    template_id = st.selectbox(
        "Sélectionner un modèle",
        options=[t.id for t in templates],
        format_func=lambda x: next((f"{t.template_name}" for t in templates if t.id == x), "")
    )

    selected_template = next((t for t in templates if t.id == template_id), None)

    if selected_template:
        # Récupérer les actifs qui peuvent être liés à ce modèle
        # (ceux qui ne sont pas déjà des modèles et qui ne sont pas déjà liés à un modèle)
        linkable_assets = db.query(Asset).filter(
            Asset.owner_id == user_id,
            Asset.is_template == False,
            Asset.template_id.is_(None)
        ).all()

        if not linkable_assets:
            st.info(
                "Aucun actif disponible à lier. Tous vos actifs sont déjà liés à des modèles ou sont des modèles eux-mêmes.")
            return

        # Sélectionner un actif à lier
        asset_id = st.selectbox(
            "Sélectionner un actif à lier",
            options=[a.id for a in linkable_assets],
            format_func=lambda x: next((f"{a.nom} ({a.type_produit})" for a in linkable_assets if a.id == x), "")
        )

        # Option pour synchroniser immédiatement
        sync_now = st.checkbox(
            "Synchroniser immédiatement",
            value=True,
            help="Si coché, les allocations de l'actif seront immédiatement remplacées par celles du modèle"
        )

        # Bouton pour lier
        if st.button("Lier l'actif au modèle"):
            if template_service.link_to_template(db, asset_id, template_id, sync_allocations=sync_now):
                st.success(f"Actif lié avec succès au modèle '{selected_template.template_name}'")
                st.rerun()
            else:
                st.error("Erreur lors de la liaison au modèle")