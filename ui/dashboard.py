"""
Interface du dashboard principal avec styles centralisés
"""

import streamlit as st
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import Bank, Account, Asset, HistoryPoint
from services.visualization_service import VisualizationService
from ui.components.ui_components import styled_metric, styled_info_box
from utils.style_loader import create_card, create_badge, get_theme_color

# Définir la fonction styled_progress localement pour éviter le problème d'importation
def styled_progress(value: float, max_value: float = 100.0, color: str = "primary",
                   height: str = "10px", label: Optional[str] = None) -> None:
    """
    Affiche une barre de progression stylisée

    Args:
        value: Valeur actuelle
        max_value: Valeur maximale
        color: Couleur de la barre ('primary', 'success', 'warning', 'danger')
        height: Hauteur de la barre
        label: Libellé à afficher (optionnel)
    """
    # Calculer le pourcentage
    percentage = min(100, max(0, (value / max_value) * 100))

    # Obtenir la couleur
    color_code = get_theme_color(color)

    # Construire le label
    label_html = f'<div style="margin-bottom:5px;">{label}</div>' if label else ''

    # Construire la barre de progression
    progress_html = f"""
    {label_html}
    <div style="background:var(--gray-700);border-radius:4px;height:{height};width:100%;">
        <div style="background:{color_code};border-radius:4px;height:{height};width:{percentage}%;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:12px;margin-top:3px;">
        <span>{value}</span>
        <span>{max_value}</span>
    </div>
    """

    st.markdown(progress_html, unsafe_allow_html=True)

def show_dashboard(db: Session, user_id: str):
    """
    Affiche le dashboard principal avec styles centralisés

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
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
                    fig.patch.set_facecolor('none')  # Fond transparent
                    for ax in fig.get_axes():
                        ax.set_facecolor('none')
                        for text in ax.texts:
                            text.set_color(get_theme_color('text_light'))

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
                    fig.patch.set_facecolor('none')
                    for ax in fig.get_axes():
                        ax.set_facecolor('none')
                        for text in ax.texts:
                            text.set_color(get_theme_color('text_light'))

                    st.pyplot(fig)

        # Évolution historique si disponible
        history_points = db.query(HistoryPoint).order_by(HistoryPoint.date).all()
        if len(history_points) > 1:
            st.subheader("Évolution du patrimoine")
            fig = VisualizationService.create_time_series_chart(db)
            if fig:
                # Stylisation du graphique
                fig.patch.set_facecolor('none')
                for ax in fig.get_axes():
                    ax.set_facecolor('none')
                    for text in ax.get_xticklabels() + ax.get_yticklabels():
                        text.set_color(get_theme_color('text_light'))
                    ax.grid(color=get_theme_color('gray-700'), linestyle='--', alpha=0.7)
                    for spine in ax.spines.values():
                        spine.set_color(get_theme_color('gray-700'))

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

                # Calculer les métriques
                pv = asset.valeur_actuelle - asset.prix_de_revient
                pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
                pv_class = "positive" if pv >= 0 else "negative"
                pv_icon = "📈" if pv >= 0 else "📉"

                # Créer le badge pour le type de produit
                badge_html = create_badge(asset.type_produit.upper(), "primary")

                # Contenu principal de la carte
                content = f"""
                <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                    <div>
                        <div style="color: {get_theme_color('text_muted')}; font-size: 0.875rem;">Valeur</div>
                        <div style="font-size: 1.5rem; font-weight: 700;">{asset.valeur_actuelle:,.2f} {asset.devise}</div>
                    </div>
                    <div>
                        <div style="color: {get_theme_color('text_muted')}; font-size: 0.875rem;">Performance</div>
                        <div class="{pv_class}" style="font-size: 1.5rem; font-weight: 700;">
                            {pv_icon} {pv_percent:+.2f}%
                        </div>
                    </div>
                </div>
                """

                # Pied de page avec info sur le compte
                footer = f"Compte: {account.libelle} ({bank.nom})" if account and bank else "Compte non disponible"

                # Créer la carte complète
                card_html = create_card(
                    title=f"{asset.nom} {badge_html}",
                    content=content,
                    footer=footer,
                    extra_classes=f"card-{i+1}"  # Pour permettre un style spécifique
                )

                st.markdown(card_html, unsafe_allow_html=True)

        # Tâches à faire - Style moderne
        todos = db.query(Asset).filter(Asset.owner_id == user_id).filter(Asset.todo != "").all()
        if todos:
            st.subheader("Tâches à faire")
            for asset in todos:
                account = db.query(Account).filter(Account.id == asset.account_id).first()

                # Créer une carte stylisée pour la tâche
                todo_content = f"""
                <div style="margin-left: 2rem;">
                    <div style="margin-bottom: 0.5rem;">{asset.todo}</div>
                    <div style="font-size: 0.8rem; color: {get_theme_color('text_muted')};">
                        <span style="display: inline-block; background: rgba(255,255,255,0.1); padding: 0.25rem 0.5rem; border-radius: 0.25rem;">
                            {account.libelle if account else "Compte inconnu"}
                        </span>
                    </div>
                </div>
                """

                todo_html = create_card(
                    title=f"✅ {asset.nom}",
                    content=todo_content,
                    extra_classes="todo-card"
                )

                st.markdown(todo_html, unsafe_allow_html=True)
    else:
        # Affichage pour le cas sans actif avec style unifié
        styled_info_box(
            "Aucun actif n'a encore été ajouté. Commencez par ajouter des banques, des comptes, puis des actifs.",
            "info"
        )

        # Bouton stylisé pour ajouter une banque
        st.markdown("""
        <div style="display: flex; justify-content: center; margin-top: 2rem;">
            <a href="javascript:void(0)" 
               onclick="document.querySelector('[data-value=&quot;Banques &amp; Comptes&quot;]').click()" 
               class="btn-primary" 
               style="background: linear-gradient(90deg, var(--primary-color), var(--primary-dark)); 
                     color: white; font-weight: 500; padding: 0.625rem 1.25rem; 
                     border-radius: 0.5rem; text-decoration: none; display: inline-block;">
                Ajouter une banque
            </a>
        </div>
        """, unsafe_allow_html=True)