# ui/assets/sync_view.py
"""
Module pour l'interface de synchronisation des actifs
"""
import streamlit as st
from sqlalchemy.orm import Session
import pandas as pd

from database.models import Asset, Account, Bank
from services.asset_service import AssetService
from services.data_service import DataService


def show_sync_options(db: Session, user_id: str):
    """
    Affiche les options de synchronisation améliorées

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.subheader("Synchronisation automatique")

    # Statistiques globales
    stats_col1, stats_col2, stats_col3 = st.columns(3)

    # Compter les actifs avec ISIN, devises étrangères et métaux
    isin_count = db.query(Asset).filter(Asset.owner_id == user_id, Asset.isin != None).count()
    forex_count = db.query(Asset).filter(Asset.owner_id == user_id, Asset.devise != "EUR").count()
    metal_count = db.query(Asset).filter(Asset.owner_id == user_id, Asset.type_produit == "metal").count()

    with stats_col1:
        st.metric("Actifs avec ISIN", isin_count)
    with stats_col2:
        st.metric("Actifs en devise étrangère", forex_count)
    with stats_col3:
        st.metric("Métaux précieux", metal_count)

    # Interface de synchronisation globale avec des cartes
    apply_sync_card_styles()

    show_sync_cards(db, user_id, isin_count, forex_count, metal_count)

    # Table des actifs avec leur dernière synchronisation
    st.subheader("État de synchronisation des actifs")

    show_sync_status_table(db, user_id)


def show_sync_cards(db, user_id, isin_count, forex_count, metal_count):
    """
    Affiche les cartes de synchronisation pour les différents types d'actifs

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
        isin_count: Nombre d'actifs avec ISIN
        forex_count: Nombre d'actifs en devise étrangère
        metal_count: Nombre d'actifs de type métal
    """
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="sync-card">
            <h3>💱 Taux de change</h3>
            <p>Synchronise les taux de change pour tous les actifs en devise étrangère.</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Synchroniser tous les taux de change", disabled=forex_count == 0):
            with st.spinner("Synchronisation des taux de change en cours..."):
                updated_count = AssetService.sync_currency_rates(db)
                if updated_count > 0:
                    st.success(f"{updated_count} actif(s) mis à jour avec succès")
                    # Mettre à jour l'historique
                    DataService.record_history_entry(db, user_id)
                else:
                    st.info("Aucun actif à mettre à jour ou erreur lors de la synchronisation")

    with col2:
        st.markdown("""
        <div class="sync-card">
            <h3>📈 Prix par ISIN</h3>
            <p>Synchronise les prix via Yahoo Finance pour tous les actifs avec un code ISIN.</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Synchroniser tous les prix via ISIN", disabled=isin_count == 0):
            with st.spinner("Synchronisation des prix via ISIN en cours..."):
                updated_count = AssetService.sync_price_by_isin(db)
                if updated_count > 0:
                    st.success(f"{updated_count} actif(s) mis à jour avec succès")
                    # Mettre à jour l'historique
                    DataService.record_history_entry(db, user_id)
                else:
                    st.info("Aucun actif avec un ISIN à mettre à jour ou erreur lors de la synchronisation")

    # Interface de synchronisation des métaux précieux
    st.markdown("""
    <div class="sync-card">
        <h3>🥇 Métaux précieux</h3>
        <p>Synchronise les prix des actifs de type métal précieux (or, argent, platine, palladium).</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Synchroniser tous les prix des métaux précieux", disabled=metal_count == 0):
        with st.spinner("Synchronisation des prix des métaux précieux en cours..."):
            updated_count = AssetService.sync_metal_prices(db)
            if updated_count > 0:
                st.success(f"{updated_count} actif(s) métaux précieux mis à jour avec succès")
                # Mettre à jour l'historique
                DataService.record_history_entry(db, user_id)
            else:
                st.info("Aucun actif métal à mettre à jour ou erreur lors de la synchronisation")

    # Synchronisation complète
    st.markdown("""
    <div class="sync-card" style="background-color:#e7f5ff;">
        <h3>🔄 Synchronisation complète</h3>
        <p>Lance une synchronisation de tous les types de données (prix, taux de change, métaux).</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Synchronisation complète"):
        with st.spinner("Synchronisation complète en cours..."):
            # Synchroniser les taux de change
            forex_updated = AssetService.sync_currency_rates(db) if forex_count > 0 else 0

            # Synchroniser les prix via ISIN
            isin_updated = AssetService.sync_price_by_isin(db) if isin_count > 0 else 0

            # Synchroniser les métaux précieux
            metals_updated = AssetService.sync_metal_prices(db) if metal_count > 0 else 0

            # Mettre à jour l'historique si au moins un actif a été mis à jour
            if forex_updated > 0 or isin_updated > 0 or metals_updated > 0:
                DataService.record_history_entry(db, user_id)
                st.success(
                    f"Synchronisation complète terminée avec succès!\n- {forex_updated} taux de change\n- {isin_updated} prix via ISIN\n- {metals_updated} métaux précieux")
            else:
                st.info("Aucun actif mis à jour lors de la synchronisation complète.")


def show_sync_status_table(db, user_id):
    """
    Affiche un tableau avec l'état de synchronisation des actifs

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    sync_assets = db.query(Asset).filter(Asset.owner_id == user_id).all()

    if sync_assets:
        # Ajouter une barre de recherche
        search_sync = st.text_input("🔎 Rechercher", placeholder="Nom d'actif, ISIN, erreur...")

        # Filtrer les actifs selon la recherche
        if search_sync:
            sync_assets = [
                asset for asset in sync_assets
                if search_sync.lower() in asset.nom.lower() or
                   (asset.isin and search_sync.lower() in asset.isin.lower()) or
                   (asset.sync_error and search_sync.lower() in asset.sync_error.lower())
            ]

        # Ajouter des options de filtrage par statut de synchronisation
        status_options = ["Tous les actifs", "Avec erreurs", "Synchronisés récemment", "Jamais synchronisés"]
        status_filter = st.radio("Filtrer par statut", status_options, horizontal=True)

        if status_filter == "Avec erreurs":
            sync_assets = [asset for asset in sync_assets if asset.sync_error]
        elif status_filter == "Synchronisés récemment":
            sync_assets = [asset for asset in sync_assets if asset.last_price_sync or asset.last_rate_sync]
        elif status_filter == "Jamais synchronisés":
            sync_assets = [asset for asset in sync_assets if not asset.last_price_sync and not asset.last_rate_sync]

        # Préparer les données pour le tableau
        sync_data = []
        for asset in sync_assets:
            last_price_sync = asset.last_price_sync.strftime(
                "%Y-%m-%d %H:%M") if asset.last_price_sync else "Jamais"
            last_rate_sync = asset.last_rate_sync.strftime("%Y-%m-%d %H:%M") if asset.last_rate_sync else "Jamais"

            # Définir le statut visuel
            if asset.sync_error:
                status_html = '<span style="color:#dc3545;">⚠️ Erreur</span>'
            elif not asset.last_price_sync and not asset.last_rate_sync:
                status_html = '<span style="color:#6c757d;">📅 Jamais</span>'
            else:
                status_html = '<span style="color:#28a745;">✓ Synchronisé</span>'

            sync_data.append({
                "ID": asset.id,
                "Nom": asset.nom,
                "ISIN": asset.isin or "-",
                "Devise": asset.devise,
                "Dernier prix": last_price_sync,
                "Dernier taux": last_rate_sync,
                "Statut": status_html,
                "Erreur": asset.sync_error or "-"
            })

        # Créer le DataFrame et afficher de manière robuste
        if sync_data:
            # Créer le DataFrame
            sync_df = pd.DataFrame(sync_data)

            # Définir explicitement les colonnes à afficher (approche robuste)
            display_columns = [col for col in sync_df.columns if col != "ID"]

            # Afficher le DataFrame avec uniquement les colonnes sélectionnées
            st.write(sync_df[display_columns].to_html(escape=False, index=False), unsafe_allow_html=True)

            # Sélection d'un actif pour synchronisation individuelle
            st.subheader("Synchronisation individuelle")

            selected_sync_id = st.selectbox(
                "Sélectionner un actif à synchroniser",
                options=[a["ID"] for a in sync_data],
                format_func=lambda x: next((a["Nom"] for a in sync_data if a["ID"] == x), "")
            )

            if selected_sync_id:
                show_individual_sync_buttons(db, selected_sync_id, user_id)
        else:
            st.info("Aucun actif ne correspond aux critères de recherche.")
    else:
        st.info("Aucun actif disponible")


def show_individual_sync_buttons(db, asset_id, user_id):
    """
    Affiche les boutons de synchronisation individuelle pour un actif

    Args:
        db: Session de base de données
        asset_id: ID de l'actif
        user_id: ID de l'utilisateur
    """
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Synchroniser prix (ISIN)", key=f"sync_isin_{asset_id}"):
            with st.spinner("Synchronisation du prix via ISIN en cours..."):
                result = AssetService.sync_price_by_isin(db, asset_id)
                if result == 1:
                    st.success("Prix synchronisé avec succès")
                    # Mettre à jour l'historique
                    DataService.record_history_entry(db, user_id)
                    st.rerun()
                else:
                    st.error("Erreur lors de la synchronisation du prix")

    with col2:
        if st.button("Synchroniser taux de change", key=f"sync_rate_{asset_id}"):
            with st.spinner("Synchronisation du taux de change en cours..."):
                result = AssetService.sync_currency_rates(db, asset_id)
                if result == 1:
                    st.success("Taux de change synchronisé avec succès")
                    # Mettre à jour l'historique
                    DataService.record_history_entry(db, user_id)
                    st.rerun()
                else:
                    st.error("Erreur lors de la synchronisation du taux de change")

    with col3:
        if st.button("Synchroniser métal précieux", key=f"sync_metal_{asset_id}"):
            with st.spinner("Synchronisation du prix du métal en cours..."):
                result = AssetService.sync_metal_prices(db, asset_id)
                if result == 1:
                    st.success("Prix du métal synchronisé avec succès")
                    # Mettre à jour l'historique
                    DataService.record_history_entry(db, user_id)
                    st.rerun()
                else:
                    st.error("Erreur lors de la synchronisation du prix du métal")


def apply_sync_card_styles():
    """
    Applique les styles CSS pour les cartes de synchronisation
    """
    st.markdown("""
    <style>
    .sync-card {
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #fff;
    }
    .sync-card h3 {
        margin-top: 0;
        font-size: 18px;
    }
    .sync-card p {
        color: #6c757d;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)