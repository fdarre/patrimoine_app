"""
Interface du dashboard principal avec styles centralisés
"""

import streamlit as st
import pandas as pd
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import Bank, Account, Asset, HistoryPoint
from services.visualization_service import VisualizationService
from ui.components.ui_components import styled_metric, styled_info_box, styled_progress
from utils.style_loader import create_card, create_badge, get_theme_color

# Couleurs fixes pour les graphiques Matplotlib (au format hex)
CHART_COLORS = {
    'text_light': '#f8fafc',  # Correspondant à --text-light
    'text_muted': '#94a3b8',  # Correspondant à --text-muted
    'gray-700': '#374151',    # Correspondant à --gray-700
    'background': 'none'      # Fond transparent
}

def show_dashboard(db: Session, user_id: str):
    """
    Affiche le dashboard principal avec styles centralisés
    """
    st.title("Dashboard")

    # Récupérer les données de l'utilisateur
    assets = db.query(Asset).filter(Asset.owner_id == user_id).all()

    # Métriques principales avec style unifié
    col1, col2, col3 = st.columns(3)

    with col1:
        # Calculer la valeur totale directement
        total_value = sum(asset.value_eur or 0.0 for asset in assets)
        styled_metric(
            label="Valeur totale du patrimoine",
            value=f"{total_value:,.2f} €".replace(",", " "),
            icon="💰"
        )

    with col2:
        asset_count = len(assets)
        styled_metric(
            label="Nombre d'actifs",
            value=str(asset_count),
            icon="📦"
        )

    with col3:
        account_count = db.query(Account).join(Bank).filter(Bank.owner_id == user_id).count()
        styled_metric(
            label="Nombre de comptes",
            value=str(account_count),
            icon="🏦"
        )

    # Graphiques principaux (si des actifs existent)
    if assets:
        col1, col2 = st.columns(2)

        with col1:
            # Répartition par catégorie
            st.subheader("Répartition par catégorie d'actif")

            # Utiliser le service de visualisation
            category_values = VisualizationService.calculate_category_values(db, user_id)

            # Convertir les catégories en format capitalisé pour l'affichage
            category_values_display = {k.capitalize(): v for k, v in category_values.items() if v > 0}

            if category_values_display:
                fig = VisualizationService.create_pie_chart(category_values_display)
                if fig:
                    # Appliquer un style adapté au thème de l'app
                    fig.patch.set_facecolor(CHART_COLORS['background'])
                    for ax in fig.get_axes():
                        ax.set_facecolor(CHART_COLORS['background'])
                        for text in ax.texts:
                            text.set_color(CHART_COLORS['text_light'])

                    st.pyplot(fig)

        with col2:
            # Répartition géographique
            st.subheader("Répartition géographique")

            # Utiliser le service de visualisation
            geo_values = VisualizationService.calculate_geo_values(db, user_id)

            # Convertir les zones en format capitalisé pour l'affichage
            geo_values_display = {k.capitalize(): v for k, v in geo_values.items() if v > 0}

            if geo_values_display:
                fig = VisualizationService.create_pie_chart(geo_values_display)
                if fig:
                    # Appliquer un style adapté au thème
                    fig.patch.set_facecolor(CHART_COLORS['background'])
                    for ax in fig.get_axes():
                        ax.set_facecolor(CHART_COLORS['background'])
                        for text in ax.texts:
                            text.set_color(CHART_COLORS['text_light'])

                    st.pyplot(fig)

        # Évolution historique si disponible
        history_points = db.query(HistoryPoint).order_by(HistoryPoint.date).all()
        if len(history_points) > 1:
            st.subheader("Évolution du patrimoine")
            fig = VisualizationService.create_time_series_chart(db)
            if fig:
                # Stylisation du graphique
                fig.patch.set_facecolor(CHART_COLORS['background'])
                for ax in fig.get_axes():
                    ax.set_facecolor(CHART_COLORS['background'])
                    for text in ax.get_xticklabels() + ax.get_yticklabels():
                        text.set_color(CHART_COLORS['text_light'])
                    ax.grid(color=CHART_COLORS['gray-700'], linestyle='--', alpha=0.7)
                    for spine in ax.spines.values():
                        spine.set_color(CHART_COLORS['gray-700'])

                st.pyplot(fig)
        else:
            styled_info_box("L'historique d'évolution sera disponible après plusieurs mises à jour d'actifs.", "info")

        # Top 5 des actifs avec style moderne
        top_assets = sorted(assets, key=lambda x: x.value_eur if x.value_eur is not None else 0.0, reverse=True)[:5]

        if top_assets:
            st.subheader("Top 5 des actifs")

            for i, asset in enumerate(top_assets):
                account = db.query(Account).filter(Account.id == asset.account_id).first()
                bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

                # Utiliser les composants natifs de Streamlit
                st.markdown(f"### {asset.nom} {asset.type_produit.upper()}")

                cols = st.columns(2)
                with cols[0]:
                    st.markdown("**Valeur:**")
                    st.markdown(f"### {asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " "))

                with cols[1]:
                    # Calculer les métriques
                    pv = asset.valeur_actuelle - asset.prix_de_revient
                    pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
                    pv_class = "positive" if pv >= 0 else "negative"
                    pv_icon = "📈" if pv >= 0 else "📉"

                    st.markdown("**Performance:**")
                    st.markdown(f"### <span class='{pv_class}'>{pv_icon} {pv_percent:+.2f}%</span>", unsafe_allow_html=True)

                st.markdown(f"**Compte:** {account.libelle} ({bank.nom})" if account and bank else "Compte non disponible")
                st.markdown("---")

        # Tâches à faire - Style moderne
        todos = db.query(Asset).filter(Asset.owner_id == user_id).filter(Asset.todo != "").all()
        if todos:
            st.subheader("Tâches à faire")
            for asset in todos:
                account = db.query(Account).filter(Account.id == asset.account_id).first()

                st.markdown(f"### ✅ {asset.nom}")
                st.markdown(asset.todo)
                st.markdown(f"*Compte: {account.libelle if account else 'Compte inconnu'}*")
                st.markdown("---")
    else:
        # Affichage pour le cas sans actif avec style unifié
        styled_info_box(
            "Aucun actif n'a encore été ajouté. Commencez par ajouter des banques, des comptes, puis des actifs.",
            "info"
        )

        # Bouton stylisé pour ajouter une banque - utiliser le composant natif
        st.markdown("### Commencer")
        if st.button("➕ Ajouter une banque", key="add_bank_btn"):
            # Changer la page via session_state
            st.session_state["navigation"] = "Banques & Comptes"
            st.rerun()