"""
Interface du dashboard principal avec styles centralisés
"""

import streamlit as st
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import Bank, Account, Asset, HistoryPoint
from services.visualization_service import VisualizationService
from utils.ui_helpers import show_message

# Couleurs fixes pour les graphiques Matplotlib
CHART_COLORS = {
    'text_light': '#f8fafc',
    'text_muted': '#94a3b8',
    'gray-700': '#374151',
    'background': 'none'
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
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:14px;color:var(--text-muted);">Valeur totale du patrimoine</div>
            <div style="font-size:24px;font-weight:bold;">{total_value:,.2f} €</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        asset_count = len(assets)
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:14px;color:var(--text-muted);">Nombre d'actifs</div>
            <div style="font-size:24px;font-weight:bold;">{asset_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        account_count = db.query(Account).join(Bank).filter(Bank.owner_id == user_id).count()
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:14px;color:var(--text-muted);">Nombre de comptes</div>
            <div style="font-size:24px;font-weight:bold;">{account_count}</div>
        </div>
        """, unsafe_allow_html=True)

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
                fig = VisualizationService.create_pie_chart(category_values_display, figsize=(8, 8))
                if fig:
                    # Ajustements spécifiques pour éviter les chevauchements
                    fig.tight_layout(pad=3.0)
                    fig.patch.set_facecolor(CHART_COLORS['background'])

                    for ax in fig.get_axes():
                        ax.set_facecolor(CHART_COLORS['background'])

                        # Ajustement des textes
                        for text in ax.texts:
                            text.set_color(CHART_COLORS['text_light'])
                            text.set_fontsize(10)

                        # Déplacer la légende en dehors du graphique
                        ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=9)

                    st.pyplot(fig)

        with col2:
            # Répartition géographique
            st.subheader("Répartition géographique")

            # Utiliser le service de visualisation
            geo_values = VisualizationService.calculate_geo_values(db, user_id)

            # Convertir les zones en format capitalisé pour l'affichage
            geo_values_display = {k.capitalize(): v for k, v in geo_values.items() if v > 0}

            if geo_values_display:
                fig = VisualizationService.create_pie_chart(geo_values_display, figsize=(8, 8))
                if fig:
                    # Ajustements pour éviter les chevauchements
                    fig.tight_layout(pad=3.0)
                    fig.patch.set_facecolor(CHART_COLORS['background'])

                    for ax in fig.get_axes():
                        ax.set_facecolor(CHART_COLORS['background'])

                        # Ajustement des textes
                        for text in ax.texts:
                            text.set_color(CHART_COLORS['text_light'])
                            text.set_fontsize(10)

                        # Déplacer la légende en dehors du graphique
                        ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=9)

                    st.pyplot(fig)

        # Évolution historique si disponible
        history_points = db.query(HistoryPoint).order_by(HistoryPoint.date).all()
        if len(history_points) > 1:
            st.subheader("Évolution du patrimoine")
            fig = VisualizationService.create_time_series_chart(db)
            if fig:
                # Stylisation du graphique
                fig.tight_layout(pad=2.0)
                fig.patch.set_facecolor(CHART_COLORS['background'])

                for ax in fig.get_axes():
                    ax.set_facecolor(CHART_COLORS['background'])

                    for text in ax.get_xticklabels() + ax.get_yticklabels():
                        text.set_color(CHART_COLORS['text_light'])
                        text.set_fontsize(9)

                    ax.grid(color=CHART_COLORS['gray-700'], linestyle='--', alpha=0.7)

                    for spine in ax.spines.values():
                        spine.set_color(CHART_COLORS['gray-700'])

                st.pyplot(fig)
        else:
            st.info("L'historique d'évolution sera disponible après plusieurs mises à jour d'actifs.")

        # Top 5 des actifs avec style moderne
        top_assets = sorted(assets, key=lambda x: x.value_eur if x.value_eur is not None else 0.0, reverse=True)[:5]

        if top_assets:
            st.subheader("Top 5 des actifs")

            for i, asset in enumerate(top_assets):
                account = db.query(Account).filter(Account.id == asset.account_id).first()
                bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

                # Calculer la plus-value
                pv = asset.valeur_actuelle - asset.prix_de_revient
                pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
                pv_class = "positive" if pv >= 0 else "negative"
                pv_icon = "📈" if pv >= 0 else "📉"

                # Utiliser une structure HTML plus sûre mais qui conserve le style
                st.markdown(f"""
                <div class="asset-card">
                    <div class="asset-header">
                        <span class="asset-icon">💰</span>
                        <span class="asset-title">{asset.nom}</span>
                        <span class="asset-badge">{asset.type_produit.upper()}</span>
                    </div>
                    <div class="asset-stats">
                        <div class="asset-stat">
                            <div class="stat-label">Valeur</div>
                            <div class="stat-value">{asset.valeur_actuelle:,.2f} {asset.devise}</div>
                        </div>
                        <div class="asset-stat">
                            <div class="stat-label">Performance</div>
                            <div class="stat-value {pv_class}">{pv_icon} {pv_percent:+.2f}%</div>
                        </div>
                    </div>
                    <div class="asset-footer">
                        <span class="asset-account">🏦 {account.libelle} ({bank.nom})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Tâches à faire - Style moderne
        todos = db.query(Asset).filter(Asset.owner_id == user_id).filter(Asset.todo != "").all()
        if todos:
            st.subheader("Tâches à faire")
            for asset in todos:
                account = db.query(Account).filter(Account.id == asset.account_id).first()

                st.markdown(f"""
                <div class="todo-card">
                    <div class="todo-header">✅ {asset.nom}</div>
                    <div class="todo-content">{asset.todo}</div>
                    <div class="todo-footer">Compte: {account.libelle if account else 'Compte inconnu'}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        # Affichage pour le cas sans actif
        st.info("Aucun actif n'a encore été ajouté. Commencez par ajouter des banques, des comptes, puis des actifs.")

        # Bouton pour ajouter une banque
        if st.button("➕ Ajouter une banque"):
            st.session_state["navigation"] = "Banques & Comptes"
            st.rerun()