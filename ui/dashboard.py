"""
Interface du dashboard principal
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any

from models.asset import Asset
from services.visualization_service import VisualizationService
from utils.calculations import calculate_category_values, calculate_geo_values, calculate_total_patrimony


def show_dashboard(
        banks: Dict[str, Dict[str, Any]],
        accounts: Dict[str, Dict[str, Any]],
        assets: List[Asset],
        history: List[Dict[str, Any]]
):
    """
    Affiche le dashboard principal

    Args:
        banks: Dictionnaire des banques
        accounts: Dictionnaire des comptes
        assets: Liste des actifs
        history: Liste des points d'historique
    """
    st.header("Dashboard", anchor=False)

    # Métriques principales
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_value = calculate_total_patrimony(assets)
        st.metric("Valeur totale du patrimoine", f"{total_value:,.2f} €".replace(",", " "))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Nombre d'actifs", len(assets))
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Nombre de comptes", len(accounts))
        st.markdown('</div>', unsafe_allow_html=True)

    # Graphiques principaux
    if assets:
        col1, col2 = st.columns(2)

        with col1:
            # Répartition par catégorie
            st.subheader("Répartition par catégorie d'actif")

            # Calculer les valeurs par catégorie (en tenant compte des fonds mixtes)
            category_values = calculate_category_values(assets, accounts)

            # Convertir les catégories en format capitalisé pour l'affichage
            category_values_display = {k.capitalize(): v for k, v in category_values.items() if v > 0}

            if category_values_display:
                fig = VisualizationService.create_pie_chart(category_values_display)
                if fig:
                    st.pyplot(fig)

        with col2:
            # Répartition géographique
            st.subheader("Répartition géographique")

            # Calculer les valeurs par zone géographique (en tenant compte des fonds mixtes)
            geo_values = calculate_geo_values(assets, accounts)

            # Convertir les zones en format capitalisé pour l'affichage
            geo_values_display = {k.capitalize(): v for k, v in geo_values.items() if v > 0}

            if geo_values_display:
                fig = VisualizationService.create_pie_chart(geo_values_display)
                if fig:
                    st.pyplot(fig)

        # Évolution historique si disponible
        if len(history) > 1:
            st.subheader("Évolution du patrimoine")
            fig = VisualizationService.create_time_series_chart(history)
            if fig:
                st.pyplot(fig)
        else:
            st.info("L'historique d'évolution sera disponible après plusieurs mises à jour d'actifs.")

        # Top 5 des actifs
        st.subheader("Top 5 des actifs")
        top_assets = sorted(assets, key=lambda x: x.valeur_actuelle, reverse=True)[:5]

        if top_assets:
            data = []
            for asset in top_assets:
                account = accounts[asset.compte_id]
                bank = banks[account["banque_id"]]
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
                    f"{account['libelle']} ({bank['nom']})"
                ])

            df = pd.DataFrame(data, columns=["Nom", "Valeur", "Plus-value", "Allocation", "Compte"])
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Tâches à faire
        todos = [asset for asset in assets if asset.todo]
        if todos:
            st.subheader("Tâches à faire")
            for asset in todos:
                account = accounts[asset.compte_id]
                st.markdown(f"""
                <div class="todo-card">
                <strong>{asset.nom}</strong> ({account['libelle']}): {asset.todo}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Aucun actif n'a encore été ajouté. Commencez par ajouter des banques, des comptes, puis des actifs.")
        st.markdown("""
        1. Allez dans la section **Banques & Comptes** pour ajouter vos banques
        2. Ajoutez ensuite des comptes associés à ces banques
        3. Enfin, ajoutez vos actifs dans la section **Gestion des actifs**
        """)