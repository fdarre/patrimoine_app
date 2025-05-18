"""
Interface du dashboard principal avec styles centralisés
"""

import streamlit as st
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session
import matplotlib.pyplot as plt
import numpy as np

from database.models import Bank, Account, Asset, HistoryPoint
from services.visualization_service import VisualizationService
from services.asset_service import asset_service

# Customize Matplotlib
plt.style.use('dark_background')

def show_dashboard(db: Session, user_id: str):
    """
    Affiche le dashboard principal avec styles centralisés
    """
    st.title("Dashboard")

    # Récupérer les données de l'utilisateur
    assets = db.query(Asset).filter(Asset.owner_id == user_id).all()

    # Métriques principales avec style natif de Streamlit
    col1, col2, col3 = st.columns(3)

    with col1:
        # Calculer la valeur totale correctement
        total_value = sum(
            asset.value_eur if asset.value_eur is not None
            else (asset.valeur_actuelle if asset.devise == "EUR" else 0.0)
            for asset in assets
        )
        formatted_value = f"{total_value:,.2f} €".replace(",", " ")
        st.metric(label="Valeur totale du patrimoine", value=formatted_value, delta=None, delta_color="normal")

    with col2:
        asset_count = len(assets)
        st.metric(label="Nombre d'actifs", value=asset_count)

    with col3:
        account_count = db.query(Account).join(Bank).filter(Bank.owner_id == user_id).count()
        st.metric(label="Nombre de comptes", value=account_count)

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
                # Graphique en camembert natif Streamlit
                labels = list(category_values_display.keys())
                values = list(category_values_display.values())

                # Generate a nice color palette
                colors = plt.cm.viridis(np.linspace(0, 1, len(labels)))

                fig, ax = plt.subplots(figsize=(8, 8))
                wedges, texts, autotexts = ax.pie(
                    values,
                    labels=labels,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors,
                    wedgeprops={'edgecolor': 'white', 'linewidth': 1, 'alpha': 0.8}
                )

                # Improve text visibility
                for text in texts:
                    text.set_color('white')
                    text.set_fontsize(10)

                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(9)
                    autotext.set_fontweight('bold')

                ax.axis('equal')
                plt.tight_layout()

                st.pyplot(fig)

        with col2:
            # Répartition géographique
            st.subheader("Répartition géographique")

            # Utiliser le service de visualisation
            geo_values = VisualizationService.calculate_geo_values(db, user_id)

            # Convertir les zones en format capitalisé pour l'affichage
            geo_values_display = {k.capitalize(): v for k, v in geo_values.items() if v > 0}

            if geo_values_display:
                # Graphique en camembert natif Streamlit
                labels = list(geo_values_display.keys())
                values = list(geo_values_display.values())

                # Generate a different color palette for this pie chart
                colors = plt.cm.plasma(np.linspace(0, 1, len(labels)))

                fig, ax = plt.subplots(figsize=(8, 8))
                wedges, texts, autotexts = ax.pie(
                    values,
                    labels=labels,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors,
                    wedgeprops={'edgecolor': 'white', 'linewidth': 1, 'alpha': 0.8}
                )

                # Improve text visibility
                for text in texts:
                    text.set_color('white')
                    text.set_fontsize(10)

                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(9)
                    autotext.set_fontweight('bold')

                ax.axis('equal')
                plt.tight_layout()

                st.pyplot(fig)

        # Évolution historique si disponible
        history_points = db.query(HistoryPoint).order_by(HistoryPoint.date).all()
        if len(history_points) > 1:
            st.subheader("Évolution du patrimoine")

            # Créer un DataFrame pour Streamlit
            history_data = []
            for point in history_points:
                history_data.append({
                    "Date": point.date,
                    "Valeur": point.total
                })

            df = pd.DataFrame(history_data)
            df["Date"] = pd.to_datetime(df["Date"])

            # Afficher avec le graphique natif de Streamlit
            st.line_chart(df.set_index("Date")["Valeur"], use_container_width=True)
        else:
            st.info("L'historique d'évolution sera disponible après plusieurs mises à jour d'actifs.")

        # Top 5 des actifs avec Streamlit native
        top_assets = sorted(assets, key=lambda x: x.value_eur if x.value_eur is not None else 0.0, reverse=True)[:5]

        if top_assets:
            st.subheader("Top 5 des actifs")

            for asset in top_assets:
                account = db.query(Account).filter(Account.id == asset.account_id).first()
                bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

                # Calculer la plus-value de manière standardisée
                pv = asset.valeur_actuelle - asset.prix_de_revient
                pv_percent = (pv / asset.prix_de_revient * 100) if asset.prix_de_revient > 0 else 0

                # Create expander for each asset
                with st.expander(f"💰 {asset.nom} ({asset.type_produit.upper()})"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**Valeur:** {asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " "))
                        if account:
                            st.markdown(f"**Compte:** {account.libelle}")
                        if bank:
                            st.markdown(f"**Banque:** {bank.nom}")

                    with col2:
                        perf_color = "green" if pv >= 0 else "red"
                        perf_sign = "+" if pv >= 0 else ""
                        st.markdown(f"**Performance:** <span style='color:{perf_color}'>{perf_sign}{pv_percent:.2f}%</span>", unsafe_allow_html=True)
                        st.markdown(f"**Plus/Moins-value:** <span style='color:{perf_color}'>{perf_sign}{pv:,.2f} {asset.devise}</span>".replace(",", " "), unsafe_allow_html=True)

        # Tâches à faire - Style moderne avec Streamlit natif
        todos = db.query(Asset).filter(Asset.owner_id == user_id).filter(Asset.todo != "").all()
        if todos:
            st.subheader("Tâches à faire")

            for i, asset in enumerate(todos):
                account = db.query(Account).filter(Account.id == asset.account_id).first()

                # Create a stylish todo container
                st.markdown(f"""
                <div style="background-color:rgba(245, 158, 11, 0.1); 
                            border-left:4px solid #f59e0b; 
                            border-radius:4px; 
                            padding:15px; 
                            margin-bottom:15px;">
                    <h4 style="margin-top:0; color:white;">{asset.nom}</h4>
                    <p style="color:rgba(255,255,255,0.8);">{asset.todo}</p>
                    <div style="font-size:12px; color:rgba(255,255,255,0.6);">
                        Compte: {account.libelle if account else "Non spécifié"}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        # Affichage pour le cas sans actif
        st.info("Aucun actif n'a encore été ajouté. Commencez par ajouter des banques, des comptes, puis des actifs.")

        # Bouton pour ajouter une banque
        if st.button("➕ Ajouter une banque"):
            st.session_state["navigation"] = "Banques & Comptes"
            st.rerun()