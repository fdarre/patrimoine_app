# ui/assets/list_view.py
"""
Fonctions d'affichage des actifs sous différentes formes (tableau, cartes, compact)
avec pagination et interface améliorée
"""
# Imports de bibliothèques tierces
import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

# Imports de l'application
from database.models import Asset, Account, Bank
from ui.components import create_asset_card


def change_page(page_key, new_page):
    """
    Change la page dans session_state

    Args:
        page_key: Clé de la page dans session_state
        new_page: Nouvelle valeur de page
    """
    st.session_state[page_key] = new_page


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
            "Performance": f'<span class="{pv_class}">{pv:,.2f} {asset.devise}</span>{perf_indicator}'.replace(",",
                                                                                                               " "),
            "Allocation": allocation_html,
            "Compte": f'<span class="account-name">{account.libelle} ({bank.nom})</span>' if account and bank else "N/A",
            "Dernière MAJ": f'<span class="update-date">{asset.date_maj}</span>'
        })

    # Créer le DataFrame
    df = pd.DataFrame(data)

    # Pagination simplifiée
    page_size = 10

    # Initialiser l'état de la page si nécessaire
    if "assets_table_page" not in st.session_state:
        st.session_state["assets_table_page"] = 0

    # Calculer le nombre total de pages
    n_pages = max(1, (len(df) + page_size - 1) // page_size)

    # Obtenir l'index de la page actuelle
    page_idx = st.session_state["assets_table_page"]

    # S'assurer que page_idx est dans les limites
    page_idx = min(max(0, page_idx), n_pages - 1)
    st.session_state["assets_table_page"] = page_idx

    # Calculer les indices de début et de fin
    start_idx = page_idx * page_size
    end_idx = min(start_idx + page_size, len(df))

    # Extraire la page actuelle
    df_paginated = df.iloc[start_idx:end_idx] if not df.empty else df.copy()

    # Afficher le nombre total d'éléments et la pagination actuelle
    st.write(f"Affichage de {start_idx + 1 if not df.empty else 0}-{end_idx} sur {len(df)} actifs")

    # Afficher le tableau
    st.write(df_paginated.drop(columns=["ID"]).to_html(escape=False, index=False), unsafe_allow_html=True)

    # Contrôles de pagination simplifiés avec callbacks appropriés
    cols = st.columns([1, 3, 1])

    with cols[0]:
        st.button("⏮️ Précédent", key="assets_table_prev",
                  disabled=page_idx == 0,
                  on_click=change_page,
                  args=("assets_table_page", max(0, page_idx - 1)))

    with cols[1]:
        st.write(f"Page {page_idx + 1} sur {n_pages}")

    with cols[2]:
        st.button("Suivant ⏭️", key="assets_table_next",
                  disabled=page_idx >= n_pages - 1,
                  on_click=change_page,
                  args=("assets_table_page", min(n_pages - 1, page_idx + 1)))

    # Section détails: permet de sélectionner un actif pour voir ses détails
    st.markdown("### 🔍 Détails d'un actif")

    # Bouton de rafraîchissement des données
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Rafraîchir", key="refresh_table"):
            pass  # Le bouton va provoquer un rechargement par lui-même

    # Amélioration de la sélection d'actif
    with col1:
        selected_asset_id = st.selectbox(
            "Sélectionner un actif",
            options=[asset["ID"] for asset in data],
            format_func=lambda x: next(
                (a["Nom"].replace('<span class="asset-name">', '').replace('</span>', '') for a in data if
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

    # Pagination simplifiée
    page_size = 9  # 3x3 grille

    # Initialiser l'état de la page si nécessaire
    if "assets_cards_page" not in st.session_state:
        st.session_state["assets_cards_page"] = 0

    # Calculer le nombre total de pages
    n_pages = max(1, (len(assets) + page_size - 1) // page_size)

    # Obtenir l'index de la page actuelle
    page_idx = st.session_state["assets_cards_page"]

    # S'assurer que page_idx est dans les limites
    page_idx = min(max(0, page_idx), n_pages - 1)
    st.session_state["assets_cards_page"] = page_idx

    # Calculer les indices de début et de fin
    start_idx = page_idx * page_size
    end_idx = min(start_idx + page_size, len(assets))

    # Afficher le nombre total d'éléments et la pagination actuelle
    st.write(f"Affichage de {start_idx + 1 if assets else 0}-{end_idx} sur {len(assets)} actifs")

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
            with col2:
                if st.button("Modifier", key=f"edit_{asset.id}"):
                    with st.spinner("Préparation du formulaire..."):
                        st.session_state['edit_asset'] = asset.id

    # Contrôles de pagination avec callbacks appropriés
    cols = st.columns([1, 3, 1])

    with cols[0]:
        st.button("⏮️ Précédent", key="assets_cards_prev",
                  disabled=page_idx == 0,
                  on_click=change_page,
                  args=("assets_cards_page", max(0, page_idx - 1)))

    with cols[1]:
        st.write(f"Page {page_idx + 1} sur {n_pages}")

    with cols[2]:
        st.button("Suivant ⏭️", key="assets_cards_next",
                  disabled=page_idx >= n_pages - 1,
                  on_click=change_page,
                  args=("assets_cards_page", min(n_pages - 1, page_idx + 1)))


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

    # Pagination simplifiée
    page_size = 15  # Plus d'éléments car format compact

    # Initialiser l'état de la page si nécessaire
    if "assets_compact_page" not in st.session_state:
        st.session_state["assets_compact_page"] = 0

    # Calculer le nombre total de pages
    n_pages = max(1, (len(assets) + page_size - 1) // page_size)

    # Obtenir l'index de la page actuelle
    page_idx = st.session_state["assets_compact_page"]

    # S'assurer que page_idx est dans les limites
    page_idx = min(max(0, page_idx), n_pages - 1)
    st.session_state["assets_compact_page"] = page_idx

    # Calculer les indices de début et de fin
    start_idx = page_idx * page_size
    end_idx = min(start_idx + page_size, len(assets))

    # Afficher le nombre total d'éléments et la pagination actuelle
    st.write(f"Affichage de {start_idx + 1 if assets else 0}-{end_idx} sur {len(assets)} actifs")

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

    # Contrôles de pagination avec callbacks appropriés
    cols = st.columns([1, 3, 1])

    with cols[0]:
        st.button("⏮️ Précédent", key="assets_compact_prev",
                  disabled=page_idx == 0,
                  on_click=change_page,
                  args=("assets_compact_page", max(0, page_idx - 1)))

    with cols[1]:
        st.write(f"Page {page_idx + 1} sur {n_pages}")

    with cols[2]:
        st.button("Suivant ⏭️", key="assets_compact_next",
                  disabled=page_idx >= n_pages - 1,
                  on_click=change_page,
                  args=("assets_compact_page", min(n_pages - 1, page_idx + 1)))


def create_allocation_html(allocation):
    """
    Crée une représentation HTML des allocations en utilisant des classes CSS
    """
    allocation_html = ""
    if allocation:
        for cat, pct in sorted(allocation.items(), key=lambda x: x[1], reverse=True)[:3]:
            allocation_html += f'<span class="allocation-pill {cat}">{cat[:3].capitalize()} {pct}%</span>'

    return allocation_html