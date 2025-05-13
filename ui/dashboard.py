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
    st.header("Dashboard", anchor=False)

    # Récupérer les données de l'utilisateur
    assets = db.query(Asset).filter(Asset.owner_id == user_id).all()

    # Métriques principales
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        # Calculer la valeur totale directement à partir des actifs de la base de données
        total_value = db.query(Asset).filter(Asset.owner_id == user_id).with_entities(
            func.sum(Asset.valeur_actuelle)
        ).scalar() or 0.0
        st.metric("Valeur totale du patrimoine", f"{total_value:,.2f} €".replace(",", " "))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        asset_count = db.query(Asset).filter(Asset.owner_id == user_id).count()
        st.metric("Nombre d'actifs", asset_count)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        account_count = db.query(Account).join(Bank).filter(Bank.owner_id == user_id).count()
        st.metric("Nombre de comptes", account_count)
        st.markdown('</div>', unsafe_allow_html=True)

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

        # Top 5 des actifs
        st.subheader("Top 5 des actifs")
        top_assets = db.query(Asset).filter(Asset.owner_id == user_id).order_by(
            Asset.valeur_actuelle.desc()
        ).limit(5).all()

        if top_assets:
            data = []
            for asset in top_assets:
                # Récupérer le compte et la banque associés
                account = db.query(Account).filter(Account.id == asset.account_id).first()
                bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

                pv = asset.valeur_actuelle - asset.prix_de_revient
                pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
                pv_class = "positive" if pv >= 0 else "negative"

                # Calculer la répartition pour l'affichage
                allocation_display = " / ".join(f"{cat.capitalize()} {pct}%" for cat, pct in asset.allocation.items())

                data.append([
                    asset.nom,
                    f"{asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " "),
                    f'<span class="{pv_class}">{pv:,.2f} {asset.devise} ({pv_percent:.2f}%)</span>'.replace(",", " "),
                    allocation_display,
                    f"{account.libelle} ({bank.nom})" if account and bank else "N/A"
                ])

            df = pd.DataFrame(data, columns=["Nom", "Valeur", "Plus-value", "Allocation", "Compte"])
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Tâches à faire
        todos = db.query(Asset).filter(Asset.owner_id == user_id).filter(Asset.todo != "").all()
        if todos:
            st.subheader("Tâches à faire")
            for asset in todos:
                account = db.query(Account).filter(Account.id == asset.account_id).first()
                st.markdown(f"""
                <div class="todo-card">
                <strong>{asset.nom}</strong> ({account.libelle if account else "N/A"}): {asset.todo}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Aucun actif n'a encore été ajouté. Commencez par ajouter des banques, des comptes, puis des actifs.")
        st.markdown("""
        1. Allez dans la section **Banques & Comptes** pour ajouter vos banques
        2. Ajoutez ensuite des comptes associés à ces banques
        3. Enfin, ajoutez vos actifs dans la section **Gestion des actifs**
        """)