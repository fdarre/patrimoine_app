# ui/assets/sync_view.py
"""
Interface de synchronisation des actifs
"""
import streamlit as st
from sqlalchemy.orm import Session

from database.models import Asset
from services.asset_service import AssetService
from services.data_service import DataService


def show_sync_options(db: Session, user_id: str):
    """
    Affiche les options de synchronisation des actifs
    """
    st.subheader("Synchronisation des actifs")

    # Calculer le nombre d'actifs par type
    isin_count = db.query(Asset).filter(
        Asset.owner_id == user_id,
        Asset.isin.is_not(None),
        Asset.isin != ""
    ).count()

    forex_count = db.query(Asset).filter(
        Asset.owner_id == user_id,
        Asset.devise != "EUR"
    ).count()

    metal_count = db.query(Asset).filter(
        Asset.owner_id == user_id,
        Asset.type_produit == "metal"
    ).count()

    # Afficher les informations de synchronisation
    st.info(
        f"Actifs disponibles pour synchronisation: {isin_count} avec ISIN, {forex_count} en devise étrangère, {metal_count} de type métal")

    # Afficher les cartes de synchronisation
    show_sync_cards(db, user_id, isin_count, forex_count, metal_count)


def show_sync_cards(db, user_id, isin_count, forex_count, metal_count):
    """
    Affiche les cartes de synchronisation pour les différents types d'actifs
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

    # Synchronisation complète avec classe spéciale
    st.markdown("""
    <div class="sync-card sync-card-primary">
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