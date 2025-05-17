# ui/assets/list_view.py
"""
Fonctions d'affichage des actifs sous différentes formes (tableau, cartes, compact)
avec pagination et interface améliorée
"""
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from database.models import Asset, Account, Bank
from utils.pagination import paginate_query, render_pagination_controls


def display_assets_table(db: Session, assets):
    """
    Affiche les actifs en mode tableau amélioré avec pagination

    Args:
        db: Session de base de données
        assets: Liste des actifs à afficher
    """
    # Préparation des données
    data = []

    # OPTIMISATION: Récupérer tous les comptes et banques en une seule requête
    asset_ids = [asset.id for asset in assets]

    # Créer une map de relation account-bank pour chaque asset_id
    account_bank_map = {}
    if asset_ids:
        # Jointure optimisée pour récupérer toutes les relations en une seule requête
        account_bank_query = (
            db.query(Account, Bank, Asset.id)
            .join(Bank, Account.bank_id == Bank.id)
            .join(Asset, Asset.account_id == Account.id)
            .filter(Asset.id.in_(asset_ids))
            .all()
        )

        # Créer le dictionnaire de mapping pour lookups rapides
        for account, bank, asset_id in account_bank_query:
            account_bank_map[asset_id] = (account, bank)

    for asset in assets:
        # Utiliser le mapping au lieu de faire une requête à chaque itération
        account, bank = account_bank_map.get(asset.id, (None, None))

        # Calculer la plus-value
        pv = asset.valeur_actuelle - asset.prix_de_revient
        pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
        pv_class = "positive" if pv >= 0 else "negative"

        # Créer une représentation visuelle de l'allocation
        allocation_html = create_allocation_html(asset.allocation)

        # Mini indicateur de performance
        perf_indicator = f'<span class="{pv_class}-indicator" style="margin-left:5px;padding:0 3px;">{pv_percent:+.1f}%</span>'

        # Créer un badge pour le type de produit avec texte blanc sur fond foncé
        product_type_badge = f'<span class="badge">{asset.type_produit}</span>'

        data.append({
            "ID": asset.id,
            "Nom": f'<span style="color:#fff;">{asset.nom}</span>',
            "Type": product_type_badge,
            "Valeur": f'<span style="color:#fff;">{asset.valeur_actuelle:,.2f} {asset.devise}</span>'.replace(",", " "),
            "Performance": f'<span class="{pv_class}">{pv:,.2f} {asset.devise}</span>{perf_indicator}'.replace(",",
                                                                                                               " "),
            "Allocation": allocation_html,
            "Compte": f'<span style="color:#ddd;">{account.libelle} ({bank.nom})</span>' if account and bank else "N/A",
            "Dernière MAJ": f'<span style="color:#ddd;">{asset.date_maj}</span>'
        })

    # Créer le DataFrame
    df = pd.DataFrame(data)

    # Pagination
    page_size = 10  # Nombre d'éléments par page
    df_paginated, total_pages, current_page = paginate_dataframe(df, page_size, "assets_table_page")

    # Afficher le nombre total d'éléments et la pagination actuelle
    st.write(
        f"Affichage de {(current_page - 1) * page_size + 1}-{min(current_page * page_size, len(df))} sur {len(df)} actifs")

    # CSS pour le tableau amélioré
    apply_table_styling()

    # Afficher le tableau sans la colonne ID
    st.write(df_paginated.drop(columns=["ID"]).to_html(escape=False, index=False), unsafe_allow_html=True)

    # Afficher les contrôles de pagination
    render_pagination_controls(total_pages, "assets_table_page")

    # Section détails: permet de sélectionner un actif pour voir ses détails
    st.markdown("### 🔍 Détails d'un actif")

    # Bouton de rafraîchissement des données
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Rafraîchir", key="refresh_table"):
            st.rerun()

    # Amélioration de la sélection d'actif
    with col1:
        selected_asset_id = st.selectbox(
            "Sélectionner un actif",
            options=[asset["ID"] for asset in data],
            format_func=lambda x: next(
                (a["Nom"].replace('<span style="color:#fff;">', '').replace('</span>', '') for a in data if
                 a["ID"] == x),
                "")
        )

    if selected_asset_id:
        # Utiliser une boîte de progression pour indiquer le chargement
        with st.spinner("Chargement des détails de l'actif..."):
            # On utilise la fonctionnalité session_state pour mémoriser l'actif sélectionné
            st.session_state['view_asset_details'] = selected_asset_id
            # Ajout d'un retour visuel
            st.success("Actif sélectionné pour affichage détaillé")


def display_assets_cards(db: Session, assets):
    """
    Affiche les actifs sous forme de cartes avec pagination

    Args:
        db: Session de base de données
        assets: Liste des actifs à afficher
    """
    # OPTIMISATION: Récupérer tous les comptes et banques en une seule requête
    asset_ids = [asset.id for asset in assets]

    # Créer une map de relation account-bank pour chaque asset_id
    account_bank_map = {}
    if asset_ids:
        # Jointure optimisée pour récupérer toutes les relations en une seule requête
        account_bank_query = (
            db.query(Account, Bank, Asset.id)
            .join(Bank, Account.bank_id == Bank.id)
            .join(Asset, Asset.account_id == Account.id)
            .filter(Asset.id.in_(asset_ids))
            .all()
        )

        # Créer le dictionnaire de mapping pour lookups rapides
        for account, bank, asset_id in account_bank_query:
            account_bank_map[asset_id] = (account, bank)

    # Pagination
    page_size = 9  # 3x3 grille

    # Créer une liste d'indices paginée
    if "assets_cards_page" not in st.session_state:
        st.session_state["assets_cards_page"] = 1

    current_page = st.session_state["assets_cards_page"]
    total_pages = (len(assets) + page_size - 1) // page_size

    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, len(assets))

    # Afficher le nombre total d'éléments et la pagination actuelle
    st.write(f"Affichage de {start_idx + 1}-{end_idx} sur {len(assets)} actifs")

    # Disposition en grille
    cols = st.columns(3)

    for i, idx in enumerate(range(start_idx, end_idx)):
        asset = assets[idx]
        # Distribution cyclique dans les colonnes
        with cols[i % 3]:
            # Récupérer le compte et la banque depuis le mapping
            account, bank = account_bank_map.get(asset.id, (None, None))

            # Calculer la plus-value
            pv = asset.valeur_actuelle - asset.prix_de_revient
            pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
            pv_class = "positive" if pv >= 0 else "negative"

            # Créer la carte avec le type de produit
            st.markdown(f"""
            <div class="sync-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <h3 style="margin-top:0;font-size:18px;color:#fff;">{asset.nom}</h3>
                    <span class="badge">{asset.type_produit}</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:5px;color:#ddd;">
                    <div><strong>Valeur:</strong> {asset.valeur_actuelle:,.2f} {asset.devise}</div>
                    <div class="{pv_class}">{pv_percent:+.1f}%</div>
                </div>
                <div style="margin-bottom:8px;font-size:12px;color:#adb5bd;">
                    {account.libelle if account else "N/A"} | {bank.nom if bank else "N/A"}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Boutons d'action dans la carte
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Détails", key=f"details_{asset.id}"):
                    with st.spinner("Chargement des détails..."):
                        st.session_state['view_asset_details'] = asset.id
                        st.success("Détails chargés")
            with col2:
                if st.button("Modifier", key=f"edit_{asset.id}"):
                    with st.spinner("Préparation du formulaire..."):
                        st.session_state['edit_asset'] = asset.id
                        st.success("Formulaire prêt")

    # Afficher les contrôles de pagination
    render_pagination_controls(total_pages, "assets_cards_page")


def display_assets_compact(db: Session, assets):
    """
    Affiche les actifs en mode liste compacte avec pagination

    Args:
        db: Session de base de données
        assets: Liste des actifs à afficher
    """
    # OPTIMISATION: Récupérer tous les comptes et banques en une seule requête
    asset_ids = [asset.id for asset in assets]

    # Créer une map de relation account-bank pour chaque asset_id
    account_bank_map = {}
    if asset_ids:
        # Jointure optimisée pour récupérer toutes les relations en une seule requête
        account_bank_query = (
            db.query(Account, Bank, Asset.id)
            .join(Bank, Account.bank_id == Bank.id)
            .join(Asset, Asset.account_id == Account.id)
            .filter(Asset.id.in_(asset_ids))
            .all()
        )

        # Créer le dictionnaire de mapping pour lookups rapides
        for account, bank, asset_id in account_bank_query:
            account_bank_map[asset_id] = (account, bank)

    # Calcul de la valeur totale pour les pourcentages
    total_value = sum(asset.valeur_actuelle for asset in assets)

    # Pagination
    page_size = 15  # Plus d'éléments car format compact

    # Créer une liste d'indices paginée
    if "assets_compact_page" not in st.session_state:
        st.session_state["assets_compact_page"] = 1

    current_page = st.session_state["assets_compact_page"]
    total_pages = (len(assets) + page_size - 1) // page_size

    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, len(assets))

    # Afficher le nombre total d'éléments et la pagination actuelle
    st.write(f"Affichage de {start_idx + 1}-{end_idx} sur {len(assets)} actifs")

    # Création d'une liste compacte
    for idx in range(start_idx, end_idx):
        asset = assets[idx]
        # Récupérer le compte et la banque depuis le mapping
        account, bank = account_bank_map.get(asset.id, (None, None))

        # Calculer la plus-value
        pv = asset.valeur_actuelle - asset.prix_de_revient
        pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
        pv_class = "positive" if pv >= 0 else "negative"

        # Calculer le pourcentage du portefeuille
        portfolio_percent = (asset.valeur_actuelle / total_value * 100) if total_value > 0 else 0

        # Créer une barre de progression proportionnelle à la valeur
        progress_html = f'<div style="background:#495057;height:4px;width:100%;margin-top:3px;"><div style="background:#4e79a7;height:4px;width:{portfolio_percent}%;"></div></div>'

        # Créer la ligne compacte
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div style="padding:8px 0;border-bottom:1px solid #495057;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <strong style="color:#fff;">{asset.nom}</strong>
                        <span class="badge">{asset.type_produit}</span>
                    </div>
                    <div style="color:#fff;">{asset.valeur_actuelle:,.2f} {asset.devise}</div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:12px;">
                    <div style="color:#adb5bd;">{account.libelle if account else "N/A"} | {bank.nom if bank else "N/A"}</div>
                    <div class="{pv_class}">{pv_percent:+.1f}%</div>
                </div>
                {progress_html}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.button("Détails", key=f"compact_details_{asset.id}"):
                with st.spinner("Chargement des détails..."):
                    st.session_state['view_asset_details'] = asset.id
                    st.success("Détails chargés")

    # Afficher les contrôles de pagination
    render_pagination_controls(total_pages, "assets_compact_page")


def create_allocation_html(allocation):
    """
    Crée une représentation HTML des allocations

    Args:
        allocation: Dictionnaire d'allocations

    Returns:
        Chaîne HTML représentant les allocations
    """
    # Définition des couleurs par catégorie
    category_colors = {
        "actions": "#4e79a7",
        "obligations": "#f28e2c",
        "immobilier": "#e15759",
        "crypto": "#76b7b2",
        "metaux": "#59a14f",
        "cash": "#edc949",
        "autre": "#af7aa1"
    }

    allocation_html = ""
    if allocation:
        for cat, pct in sorted(allocation.items(), key=lambda x: x[1], reverse=True)[:3]:
            color = category_colors.get(cat, "#bab0ab")
            allocation_html += f'<div style="display:inline-block;margin-right:4px;"><span style="background:{color};width:10px;height:10px;display:inline-block;margin-right:2px;"></span><span style="color:#fff;">{cat[:3].capitalize()} {pct}%</span></div>'

    return allocation_html


def apply_table_styling():
    """
    Applique le style CSS pour les tableaux
    Note: Cette fonction sera remplacée par l'utilisation du fichier CSS centralisé
    """
    st.markdown("""
    <style>
    /* Cette fonction est conservée pour compatibilité, mais les styles sont dans main.css */
    </style>
    """, unsafe_allow_html=True)


def paginate_dataframe(df, page_size=10, page_key="pagination_page"):
    """
    Fonction de pagination pour DataFrame - sera remplacée par paginate_query
    pour les requêtes SQLAlchemy
    """
    import math

    # Calculer le nombre total de pages
    total_rows = len(df)
    total_pages = math.ceil(total_rows / page_size) if total_rows > 0 else 1

    # Initialiser la page courante dans session_state si nécessaire
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    # S'assurer que la page courante est valide
    current_page = st.session_state[page_key]
    if current_page > total_pages:
        current_page = total_pages
        st.session_state[page_key] = current_page

    # Calculer les indices de début et de fin
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)

    # Extraire la page courante
    df_paginated = df.iloc[start_idx:end_idx].copy() if not df.empty else df.copy()

    return df_paginated, total_pages, current_page