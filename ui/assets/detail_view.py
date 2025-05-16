# ui/assets/detail_view.py
"""
Module pour l'affichage détaillé d'un actif
"""
import streamlit as st
import matplotlib.pyplot as plt
from sqlalchemy.orm import Session

from database.models import Asset, Account, Bank
from services.asset_service import AssetService


def display_asset_details(db: Session, asset_id: str):
    """
    Affiche les détails complets d'un actif

    Args:
        db: Session de base de données
        asset_id: ID de l'actif à afficher
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        st.error("Actif introuvable.")
        return

    # Récupérer le compte et la banque
    account = db.query(Account).filter(Account.id == asset.account_id).first()
    bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

    # Afficher le fil d'ariane (breadcrumb)
    st.markdown(f"""
    <div style="margin-bottom:15px;font-size:14px;color:#6c757d;">
        {bank.nom if bank else "N/A"} > {account.libelle if account else "N/A"} > <strong>{asset.nom}</strong>
    </div>
    """, unsafe_allow_html=True)

    # En-tête avec les informations essentielles
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(asset.nom)
        st.markdown(f"""
        <div style="margin-bottom:10px;">
            <span style="background:#e9ecef;border-radius:3px;padding:2px 8px;font-size:14px;font-weight:bold;">{asset.type_produit.upper()}</span>
            {f'<span style="margin-left:10px;font-family:monospace;background:#f8f9fa;padding:2px 8px;border-radius:3px;">{asset.isin}</span>' if asset.isin else ''}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Calculer la plus-value
        pv = asset.valeur_actuelle - asset.prix_de_revient
        pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
        pv_class = "positive" if pv >= 0 else "negative"

        st.markdown(f"""
        <div style="text-align:right;">
            <div style="font-size:24px;font-weight:bold;">{asset.valeur_actuelle:,.2f} {asset.devise}</div>
            <div class="{pv_class}" style="font-size:16px;">{pv:+,.2f} {asset.devise} ({pv_percent:+.2f}%)</div>
        </div>
        """, unsafe_allow_html=True)

    # Onglets pour les différentes sections de détails
    detail_tabs = st.tabs(["📊 Allocations", "💰 Valorisation", "📋 Informations", "✏️ Édition"])

    with detail_tabs[0]:
        display_asset_allocations(asset)

    with detail_tabs[1]:
        display_asset_valuation(asset, db)

    with detail_tabs[2]:
        display_asset_information(asset, account, bank)

    with detail_tabs[3]:
        # Réutiliser le code existant pour l'édition
        if st.button("Modifier cet actif"):
            st.session_state[f'edit_asset_{asset.id}'] = True

        if f'edit_asset_{asset.id}' in st.session_state and st.session_state[f'edit_asset_{asset.id}']:
            # Utiliser une référence à la fonction d'édition existante
            st.info("Formulaire d'édition avancé de l'actif")
            # Rediriger vers le formulaire d'édition
            st.session_state['edit_asset'] = asset.id
            st.rerun()


def display_asset_allocations(asset):
    """
    Affiche les allocations par catégorie et répartition géographique d'un actif

    Args:
        asset: Actif à afficher
    """
    st.subheader("Allocation par catégorie")

    # Créer un graphique avec les allocations
    if asset.allocation:
        # Préparer les données
        categories = list(asset.allocation.keys())
        percentages = list(asset.allocation.values())

        # Créer le graphique
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(categories, percentages,
                      color=['#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1'])

        # Ajouter les pourcentages sur les barres
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + 1, f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=10)

        ax.set_ylabel('Pourcentage (%)')
        ax.set_ylim(0, 100)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        st.pyplot(fig)

    # Répartition géographique
    st.subheader("Répartition géographique")

    if asset.geo_allocation:
        # Créer des onglets pour chaque catégorie d'allocation
        geo_tabs = st.tabs([cat.capitalize() for cat in asset.allocation.keys()])

        for i, (category, percentage) in enumerate(asset.allocation.items()):
            with geo_tabs[i]:
                geo_data = asset.geo_allocation.get(category, {})

                if geo_data:
                    # Créer un graphique en camembert
                    fig, ax = plt.subplots(figsize=(8, 5))

                    # Trier par valeur décroissante
                    sorted_geo = sorted(geo_data.items(), key=lambda x: x[1], reverse=True)
                    labels = [item[0].capitalize() for item in sorted_geo]
                    sizes = [item[1] for item in sorted_geo]

                    # Créer le camembert
                    wedges, texts, autotexts = ax.pie(
                        sizes,
                        labels=labels,
                        autopct='%1.1f%%',
                        startangle=90,
                        wedgeprops={'edgecolor': 'w', 'linewidth': 1}
                    )

                    # Améliorer la lisibilité
                    for text in texts:
                        text.set_fontsize(9)
                    for autotext in autotexts:
                        autotext.set_fontsize(9)
                        autotext.set_weight('bold')

                    ax.axis('equal')

                    st.pyplot(fig)
                else:
                    st.info(f"Pas de répartition géographique définie pour {category}")


def display_asset_valuation(asset, db: Session):
    """
    Affiche les données de valorisation d'un actif

    Args:
        asset: Actif à afficher
        db: Session de base de données pour les mises à jour
    """
    st.subheader("Données de valorisation")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Valeur actuelle", f"{asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " "))
        st.metric("Prix de revient", f"{asset.prix_de_revient:,.2f} {asset.devise}".replace(",", " "))

        if asset.devise != "EUR" and asset.exchange_rate:
            st.metric("Taux de change", f"1 {asset.devise} = {asset.exchange_rate:,.4f} EUR".replace(",", " "))
            if asset.value_eur:
                st.metric("Valeur en EUR", f"{asset.value_eur:,.2f} EUR".replace(",", " "))

    with col2:
        # Plus-value
        pv = asset.valeur_actuelle - asset.prix_de_revient
        pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0

        st.metric("Plus-value",
                  f"{pv:,.2f} {asset.devise}".replace(",", " "),
                  f"{pv_percent:+.2f}%",
                  delta_color="normal" if pv >= 0 else "inverse")

        # Dates importantes
        st.write("**Date de mise à jour:**", asset.date_maj)
        if asset.last_price_sync:
            st.write("**Dernière synchro prix:**", asset.last_price_sync)
        if asset.last_rate_sync:
            st.write("**Dernière synchro taux:**", asset.last_rate_sync)

    # Ajouter un formulaire de mise à jour rapide
    st.subheader("Mise à jour rapide")
    col1, col2 = st.columns(2)
    with col1:
        new_price = st.number_input("Nouveau prix",
                                    min_value=0.0,
                                    value=float(asset.valeur_actuelle),
                                    format="%.2f")
    with col2:
        if st.button("Mettre à jour", key=f"update_price_{asset.id}"):
            # Code pour la mise à jour du prix
            if AssetService.update_manual_price(db, asset.id, new_price):
                st.success("Prix mis à jour avec succès")
                st.rerun()
            else:
                st.error("Erreur lors de la mise à jour du prix")


def display_asset_information(asset, account, bank):
    """
    Affiche les informations générales d'un actif

    Args:
        asset: Actif à afficher
        account: Compte associé
        bank: Banque associée
    """
    st.subheader("Informations générales")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Type de produit:**", asset.type_produit)
        st.write("**Compte:**", f"{account.libelle} ({account.type})" if account else "N/A")
        st.write("**Banque:**", bank.nom if bank else "N/A")

        if asset.type_produit == "metal" and asset.ounces:
            st.write("**Onces:**", asset.ounces)

    with col2:
        st.write("**Catégorie principale:**", asset.categorie.capitalize())
        st.write("**Date d'ajout:**", asset.date_maj)
        st.write("**Devise:**", asset.devise)

    # Notes et tâches
    if asset.notes:
        st.subheader("Notes")
        st.markdown(f'<div style="background:#f8f9fa;padding:10px;border-radius:5px;">{asset.notes}</div>',
                    unsafe_allow_html=True)

    if asset.todo:
        st.subheader("Tâches à faire")
        st.markdown(f"""
        <div class="todo-card" style="background-color:#fff3cd;border-left:4px solid #ffc107;padding:1rem;border-radius:0.25rem;">
            {asset.todo}
        </div>
        """, unsafe_allow_html=True)