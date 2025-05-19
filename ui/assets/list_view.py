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
from services.asset_service import asset_service
from services.data_service import DataService
from utils.session_manager import session_manager  # Utilisation du gestionnaire de session


def display_assets_table_with_actions(db: Session, assets, user_id):
    """
    Affiche les actifs en mode tableau avec options de modification et suppression

    Args:
        db: Session de base de données
        assets: Liste des actifs à afficher
        user_id: ID de l'utilisateur
    """
    # Préparation des données
    data = []
    assets_map = {}  # Pour stocker les objets asset par ID

    # OPTIMISATION: Récupérer tous les comptes et banques en une seule requête
    asset_ids = [asset.id for asset in assets]
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

    # Créer les données pour le dataframe
    for asset in assets:
        # Stocker l'actif pour référence ultérieure
        assets_map[asset.id] = asset

        # Utiliser le mapping au lieu de faire une requête à chaque itération
        account, bank = account_bank_map.get(asset.id, (None, None))

        # Calculer la plus-value
        pv = asset.valeur_actuelle - asset.prix_de_revient
        pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0

        # Créer une représentation HTML des allocations
        allocation_html = create_allocation_html(asset.allocation)

        data.append({
            "ID": asset.id,
            "Nom": asset.nom,
            "Type": asset.type_produit,
            "Valeur": f"{asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " "),
            "Performance": f"{pv_percent:+.2f}%" if pv_percent != 0 else "0.00%",
            "Allocation": allocation_html,
            "Compte": f"{account.libelle} ({bank.nom})" if account and bank else "N/A",
            "MAJ": asset.date_maj
        })

    # Créer le DataFrame
    df = pd.DataFrame(data)

    # Pagination simplifiée
    page_size = 10

    # Utiliser le gestionnaire de session pour la pagination
    page_idx = session_manager.get_page("assets_table")

    # Calculer le nombre total de pages
    n_pages = max(1, (len(df) + page_size - 1) // page_size)

    # S'assurer que page_idx est dans les limites
    page_idx = min(max(0, page_idx), n_pages - 1)
    session_manager.set_page("assets_table", page_idx)

    # Calculer les indices de début et de fin
    start_idx = page_idx * page_size
    end_idx = min(start_idx + page_size, len(df))

    # Extraire la page actuelle
    df_paginated = df.iloc[start_idx:end_idx] if not df.empty else df.copy()

    # Afficher le nombre total d'éléments et la pagination actuelle
    st.write(f"Affichage de {start_idx + 1 if not df.empty else 0}-{end_idx} sur {len(df)} actifs")

    # Afficher le tableau avec HTML non échappé
    st.markdown(df_paginated.drop(columns=["ID"]).to_html(escape=False, index=False), unsafe_allow_html=True)

    # Section actions sous le tableau
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        paginated_ids = df_paginated["ID"].tolist() if not df_paginated.empty else []

        selected_asset_id = st.selectbox(
            "Sélectionner un actif pour action",
            options=paginated_ids,
            format_func=lambda x: assets_map[x].nom if x in assets_map else ""
        )

    with col2:
        if selected_asset_id and st.button("✏️ Modifier", key=f"edit_{selected_asset_id}"):
            # Utiliser le gestionnaire de session
            session_manager.set("edit_asset", selected_asset_id)
            st.rerun()

    with col3:
        if selected_asset_id and st.button("🗑️ Supprimer", key=f"delete_{selected_asset_id}"):
            # Utiliser le gestionnaire de session
            session_manager.set(f'confirm_delete_{selected_asset_id}', True)
            st.rerun()

    # Confirmation de suppression
    if selected_asset_id and session_manager.get(f'confirm_delete_{selected_asset_id}'):
        selected_asset = assets_map.get(selected_asset_id)

        if selected_asset:
            st.warning(f"Êtes-vous sûr de vouloir supprimer l'actif '{selected_asset.nom}' ?")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Oui, supprimer", key=f"confirm_yes_{selected_asset_id}"):
                    # Utiliser la méthode delete() du service
                    if asset_service.delete(db, selected_asset_id):
                        # Mise à jour de l'historique
                        DataService.record_history_entry(db, user_id)
                        st.success(f"Actif '{selected_asset.nom}' supprimé avec succès.")

                        # Nettoyer la session state
                        session_manager.delete(f'confirm_delete_{selected_asset_id}')

                        st.rerun()
                    else:
                        st.error("Erreur lors de la suppression de l'actif.")

            with col2:
                if st.button("Annuler", key=f"confirm_no_{selected_asset_id}"):
                    # Annuler la suppression
                    session_manager.delete(f'confirm_delete_{selected_asset_id}')
                    st.rerun()

    # Contrôles de pagination
    cols = st.columns([1, 3, 1])

    with cols[0]:
        if st.button("⏮️ Précédent", key="assets_table_prev", disabled=page_idx == 0):
            session_manager.set_page("assets_table", max(0, page_idx - 1))
            st.rerun()

    with cols[1]:
        st.write(f"Page {page_idx + 1} sur {n_pages}")

    with cols[2]:
        if st.button("Suivant ⏭️", key="assets_table_next", disabled=page_idx >= n_pages - 1):
            session_manager.set_page("assets_table", min(n_pages - 1, page_idx + 1))
            st.rerun()


def display_assets_table(db: Session, assets):
    """
    Affiche les actifs en mode tableau amélioré avec pagination

    Args:
        db: Session de base de données
        assets: Liste des actifs à afficher
    """
    # Cette fonction est maintenue pour compatibilité avec les codes existants
    display_assets_table_with_actions(db, assets, None)


def display_assets_cards(db: Session, assets):
    """
    Affiche les actifs sous forme de cartes avec pagination

    Args:
        db: Session de base de données
        assets: Liste des actifs à afficher
    """
    # Cette fonction est maintenue pour compatibilité avec les codes existants
    display_assets_table_with_actions(db, assets, None)


def display_assets_compact(db: Session, assets):
    """
    Affiche les actifs en mode liste compacte avec pagination

    Args:
        db: Session de base de données
        assets: Liste des actifs à afficher
    """
    # Cette fonction est maintenue pour compatibilité avec les codes existants
    display_assets_table_with_actions(db, assets, None)


def create_allocation_html(allocation):
    """
    Crée une représentation HTML des allocations en utilisant des classes CSS
    """
    allocation_html = ""
    if allocation:
        for cat, pct in sorted(allocation.items(), key=lambda x: x[1], reverse=True)[:3]:
            allocation_html += f'<span class="allocation-pill {cat}">{cat[:3].capitalize()} {pct}%</span>'

    return allocation_html