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
from utils.pagination import paginate_query
from utils.ui_components import create_allocation_pills, styled_todo_card, create_asset_card


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
        perf_indicator = f'<span class="{pv_class}-indicator">{pv_percent:+.1f}%</span>'

        # Créer un badge pour le type de produit
        product_type_badge = f'<span class="badge">{asset.type_produit}</span>'

        data.append({
            "ID": asset.id,
            "Nom": f'<span class="asset-name">{asset.nom}</span>',
            "Type": product_type_badge,
            "Valeur": f'<span class="asset-value">{asset.valeur_actuelle:,.2f} {asset.devise}</span>'.replace(",", " "),
            "Performance": f'<span class="{pv_class}">{pv:,.2f} {asset.devise}</span>{perf_indicator}'.replace(",", " "),
            "Allocation": allocation_html,
            "Compte": f'<span class="account-name">{account.libelle} ({bank.nom})</span>' if account and bank else "N/A",
            "Dernière MAJ": f'<span class="update-date">{asset.date_maj}</span>'
        })

    # Créer le DataFrame
    df = pd.DataFrame(data)

    # Pagination
    page_size = 10  # Nombre d'éléments par page
    df_paginated, total_pages, current_page = paginate_dataframe(df, page_size, "assets_table_page")

    # Afficher le nombre total d'éléments et la pagination actuelle
    st.write(
        f"Affichage de {(current_page - 1) * page_size + 1}-{min(current_page * page_size, len(df))} sur {len(df)} actifs")

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
                (a["Nom"].replace('<span class="asset-name">', '').replace('</span>', '') for a in data if a["ID"] == x),
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

            # Utiliser le composant de carte d'actif
            create_asset_card(
                name=asset.nom,
                asset_type=asset.type_produit,
                value=asset.valeur_actuelle,
                currency=asset.devise,
                performance=pv_percent,
                account=account.libelle if account else "N/A",
                bank=bank.nom if bank else "N/A"
            )

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

        # Créer la ligne compacte avec des classes CSS
        st.markdown(f"""
        <div class="asset-compact">
            <div class="asset-compact-header">
                <div class="asset-compact-name">{asset.nom}</div>
                <span class="badge">{asset.type_produit}</span>
                <div class="asset-compact-value">{asset.valeur_actuelle:,.2f} {asset.devise}</div>
            </div>
            <div class="asset-compact-details">
                <div class="asset-compact-account">{account.libelle if account else "N/A"} | {bank.nom if bank else "N/A"}</div>
                <div class="asset-compact-perf {pv_class}">{pv_percent:+.1f}%</div>
            </div>
            <div class="asset-compact-progress-bg">
                <div class="asset-compact-progress" style="width:{portfolio_percent}%;"></div>
            </div>
        </div>
        """.replace(",", " "), unsafe_allow_html=True)

        # Bouton de détails
        if st.button("Détails", key=f"compact_details_{asset.id}"):
            with st.spinner("Chargement des détails..."):
                st.session_state['view_asset_details'] = asset.id
                st.success("Détails chargés")

    # Afficher les contrôles de pagination
    render_pagination_controls(total_pages, "assets_compact_page")


def create_allocation_html(allocation):
    """
    Crée une représentation HTML des allocations en utilisant des classes CSS
    """
    allocation_html = ""
    if allocation:
        for cat, pct in sorted(allocation.items(), key=lambda x: x[1], reverse=True)[:3]:
            allocation_html += f'<span class="allocation-pill {cat}">{cat[:3].capitalize()} {pct}%</span>'

    return allocation_html


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