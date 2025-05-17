"""
Interface du dashboard principal
"""

import streamlit as st
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import Bank, Account, Asset, HistoryPoint
from services.visualization_service import VisualizationService

def show_dashboard(db: Session, user_id: str):
    """
    Affiche le dashboard principal

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.title("Dashboard")

    # Récupérer les données de l'utilisateur
    assets = db.query(Asset).filter(Asset.owner_id == user_id).all()

    # Métriques principales - Avec style moderne
    col1, col2, col3 = st.columns(3)

    with col1:
        # Calculer la valeur totale directement
        total_value = sum(asset.value_eur or 0.0 for asset in assets)
        st.metric("Valeur totale du patrimoine", f"{total_value:,.2f} €".replace(",", " "))

    with col2:
        asset_count = len(assets)
        st.metric("Nombre d'actifs", asset_count)

    with col3:
        account_count = db.query(Account).join(Bank).filter(Bank.owner_id == user_id).count()
        st.metric("Nombre de comptes", account_count)

    # Graphiques principaux (si des actifs existent)
    if assets:
        col1, col2 = st.columns(2)

        with col1:
            # Répartition par catégorie
            st.subheader("Répartition par catégorie d'actif")

            # Utiliser le service de visualisation mis à jour pour SQLAlchemy
            category_values = VisualizationService.calculate_category_values(db, user_id)

            # Convertir les catégories en format capitalisé pour l'affichage
            category_values_display = {k.capitalize(): v for k, v in category_values.items() if v > 0}

            if category_values_display:
                fig = VisualizationService.create_pie_chart(category_values_display)
                if fig:
                    st.pyplot(fig)

        with col2:
            # Répartition géographique
            st.subheader("Répartition géographique")

            # Utiliser le service de visualisation mis à jour pour SQLAlchemy
            geo_values = VisualizationService.calculate_geo_values(db, user_id)

            # Convertir les zones en format capitalisé pour l'affichage
            geo_values_display = {k.capitalize(): v for k, v in geo_values.items() if v > 0}

            if geo_values_display:
                fig = VisualizationService.create_pie_chart(geo_values_display)
                if fig:
                    st.pyplot(fig)

        # Évolution historique si disponible
        history_points = db.query(HistoryPoint).order_by(HistoryPoint.date).all()
        if len(history_points) > 1:
            st.subheader("Évolution du patrimoine")
            fig = VisualizationService.create_time_series_chart(db)
            if fig:
                st.pyplot(fig)
        else:
            st.info("L'historique d'évolution sera disponible après plusieurs mises à jour d'actifs.")

        # Top 5 des actifs avec style moderne
        top_assets = sorted(assets, key=lambda x: x.value_eur if x.value_eur is not None else 0.0, reverse=True)[:5]

        if top_assets:
            st.subheader("Top 5 des actifs")

            # Utiliser des cartes modernes au lieu d'un tableau
            for i, asset in enumerate(top_assets):
                account = db.query(Account).filter(Account.id == asset.account_id).first()
                bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

                # Calculer les métriques
                pv = asset.valeur_actuelle - asset.prix_de_revient
                pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
                pv_class = "positive" if pv >= 0 else "negative"
                pv_icon = "📈" if pv >= 0 else "📉"

                # Style de la carte avec dégradé basé sur la position
                gradient_start = "#6366f1"  # Indigo
                gradient_end = "#ec4899"    # Rose

                # Afficher une carte moderne
                st.markdown(f"""
                <div class="card-container" style="background: linear-gradient(135deg, {gradient_start}, {gradient_end}, {gradient_start});">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <h3 style="margin: 0; font-size: 1.25rem;">{asset.nom}</h3>
                        <span class="badge badge-primary">{asset.type_produit.upper()}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.875rem;">Valeur</div>
                            <div style="font-size: 1.5rem; font-weight: 700;">{asset.valeur_actuelle:,.2f} {asset.devise}</div>
                        </div>
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.875rem;">Performance</div>
                            <div class="{pv_class}" style="font-size: 1.5rem; font-weight: 700;">{pv_icon} {pv_percent:+.2f}%</div>
                        </div>
                    </div>
                    <div style="color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem;">Compte</div>
                    <div style="font-weight: 500;">{account.libelle} ({bank.nom})</div>
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
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.25rem; margin-right: 0.75rem;">✅</span>
                        <strong style="font-size: 1.1rem;">{asset.nom}</strong>
                    </div>
                    <div style="margin-left: 2rem;">
                        <div style="margin-bottom: 0.5rem;">{asset.todo}</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">
                            <span style="display: inline-block; background: rgba(255,255,255,0.1); padding: 0.25rem 0.5rem; border-radius: 0.25rem;">{account.libelle}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        # Affichage amélioré pour le cas sans actif
        st.markdown("""
        <div class="card-container" style="text-align: center; padding: 2rem;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Noun_project_-_Wallet.svg/1024px-Noun_project_-_Wallet.svg.png" style="width: 100px; height: 100px; margin-bottom: 1rem; opacity: 0.3;">
            <h3>Aucun actif n'a encore été ajouté</h3>
            <p style="color: var(--text-muted); margin-bottom: 2rem;">Commencez par ajouter des banques, des comptes, puis des actifs.</p>
            <div style="display: flex; justify-content: center; gap: 1rem;">
                <a href="javascript:void(0)" onclick="document.querySelector('[data-value=&quot;Banques &amp; Comptes&quot;]').click()" class="btn-primary" style="background: linear-gradient(90deg, var(--primary-color), var(--primary-dark)); color: white; font-weight: 500; padding: 0.625rem 1.25rem; border-radius: 0.5rem; text-decoration: none;">Ajouter une banque</a>
            </div>
        </div>
        """, unsafe_allow_html=True)