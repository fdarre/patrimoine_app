"""
Module pour l'édition d'actifs existants
"""
# Imports de bibliothèques tierces
import streamlit as st
from sqlalchemy.orm import Session

# Imports de l'application
from config.app_config import PRODUCT_TYPES, CURRENCIES
from database.models import Asset, Account, Bank
from services.asset_service import asset_service
from services.data_service import DataService
from ui.components import apply_button_styling
from ui.shared.allocation_forms import edit_allocation_form, edit_geo_allocation_form
from utils.session_manager import session_manager  # Utilisation du gestionnaire de session


def show_edit_asset_form(db: Session, asset_id: str, user_id: str):
    """
    Affiche un formulaire pour l'édition d'un actif existant

    Args:
        db: Session de base de données
        asset_id: ID de l'actif à éditer
        user_id: ID de l'utilisateur propriétaire
    """
    # Récupérer l'actif
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.owner_id == user_id).first()

    if not asset:
        st.error("Actif introuvable.")
        return

    st.subheader(f"Modifier l'actif: {asset.nom}")

    # Interface à onglets pour une édition plus intuitive
    edit_tabs = st.tabs(["📝 Informations de base", "📊 Allocation", "🌍 Répartition géographique"])

    with edit_tabs[0]:
        # Collecter les informations de base
        asset_info = collect_edit_asset_info(db, asset, user_id)

    with edit_tabs[1]:
        # Collecter les informations d'allocation
        new_allocation, allocation_valid = edit_allocation_form(asset, asset_id)

    with edit_tabs[2]:
        # Collecter les informations de répartition géographique
        new_geo_allocation, all_geo_valid = edit_geo_allocation_form(asset, asset_id, new_allocation)

    # Validation globale
    form_valid = (
            asset_info["name"] and
            asset_info["account_id"] and
            asset_info["value"] > 0 and
            allocation_valid and
            all_geo_valid
    )

    # Boutons de validation
    col1, col2 = st.columns(2)

    apply_button_styling(form_valid)

    with col1:
        if st.button("Enregistrer les modifications", key=f"btn_save_asset_{asset_id}", disabled=not form_valid):
            try:
                # Mettre à jour l'actif
                updated_asset = asset_service.update_asset(
                    db=db,
                    asset_id=asset_id,
                    nom=asset_info["name"],
                    compte_id=asset_info["account_id"],
                    type_produit=asset_info["type"],
                    allocation=new_allocation,
                    geo_allocation=new_geo_allocation,
                    valeur_actuelle=asset_info["value"],
                    prix_de_revient=asset_info["cost"],
                    devise=asset_info["currency"],
                    notes=asset_info["notes"],
                    todo=asset_info["todo"],
                    isin=asset_info["isin"],
                    ounces=asset_info["ounces"]
                )

                if updated_asset:
                    # Mettre à jour l'historique
                    DataService.record_history_entry(db, user_id)

                    # Nettoyer la session state
                    session_manager.delete(f'edit_asset_{asset_id}')
                    session_manager.delete('edit_asset')

                    st.success("Actif mis à jour avec succès")
                    st.rerun()
                else:
                    st.error("Erreur lors de la mise à jour de l'actif")
            except ValueError:
                st.error("Valeurs numériques invalides")
            except Exception as e:
                st.error(f"Erreur inattendue: {str(e)}")

    with col2:
        if st.button("Annuler", key=f"btn_cancel_asset_{asset_id}"):
            # Nettoyer la session state
            session_manager.delete(f'edit_asset_{asset_id}')
            session_manager.delete('edit_asset')
            st.rerun()


def collect_edit_asset_info(db, asset, user_id):
    """
    Collecte les informations de base d'un actif pour l'édition

    Args:
        db: Session de base de données
        asset: Actif à éditer
        user_id: ID de l'utilisateur

    Returns:
        Dictionnaire contenant les informations de base de l'actif
    """
    col1, col2 = st.columns(2)

    with col1:
        asset_name = st.text_input("Nom", value=asset.nom, key=f"edit_asset_name_{asset.id}")

        asset_type = st.selectbox(
            "Type de produit",
            options=PRODUCT_TYPES,
            index=PRODUCT_TYPES.index(asset.type_produit) if asset.type_produit in PRODUCT_TYPES else 0,
            key=f"edit_asset_type_{asset.id}"
        )

        asset_isin = st.text_input("Code ISIN (optionnel)", value=asset.isin or "",
                                   key=f"edit_asset_isin_{asset.id}")

        # Champs spécifiques selon le type
        if asset_type == "metal":
            asset_ounces = st.number_input("Quantité (onces)",
                                           min_value=0.0,
                                           value=float(asset.ounces or 0.0),
                                           format="%.3f",
                                           key=f"edit_asset_ounces_{asset.id}")
        else:
            asset_ounces = None

        asset_notes = st.text_area("Notes", value=asset.notes or "",
                                   key=f"edit_asset_notes_{asset.id}")

    with col2:
        # Sélection des banques et comptes
        banks = db.query(Bank).filter(Bank.owner_id == user_id).all()

        # Récupérer le compte actuel et sa banque
        account = db.query(Account).filter(Account.id == asset.account_id).first()
        bank_id = account.bank_id if account else None

        # Sélection de la banque
        asset_bank = st.selectbox(
            "Banque",
            options=[bank.id for bank in banks],
            index=next((i for i, bank in enumerate(banks) if bank.id == bank_id), 0),
            format_func=lambda x: next((bank.nom for bank in banks if bank.id == x), ""),
            key=f"edit_asset_bank_{asset.id}"
        )

        # Filtrer les comptes selon la banque sélectionnée
        bank_accounts = db.query(Account).filter(Account.bank_id == asset_bank).all()

        # Trouver l'index du compte actuel dans la liste filtrée
        account_index = next((i for i, acc in enumerate(bank_accounts) if acc.id == asset.account_id), 0)

        asset_account = st.selectbox(
            "Compte",
            options=[acc.id for acc in bank_accounts],
            index=min(account_index, len(bank_accounts) - 1) if bank_accounts else 0,
            format_func=lambda x: next((acc.libelle for acc in bank_accounts if acc.id == x), ""),
            key=f"edit_asset_account_{asset.id}"
        )

        asset_value = st.number_input("Valeur actuelle",
                                      min_value=0.0,
                                      value=float(asset.valeur_actuelle),
                                      format="%.2f",
                                      key=f"edit_asset_value_{asset.id}")

        asset_cost = st.number_input("Prix de revient",
                                     min_value=0.0,
                                     value=float(asset.prix_de_revient),
                                     format="%.2f",
                                     key=f"edit_asset_cost_{asset.id}")

        asset_currency = st.selectbox(
            "Devise",
            options=CURRENCIES,
            index=CURRENCIES.index(asset.devise) if asset.devise in CURRENCIES else 0,
            key=f"edit_asset_currency_{asset.id}"
        )

        asset_todo = st.text_area("Tâche à faire", value=asset.todo or "",
                                  key=f"edit_asset_todo_{asset.id}")

    # Retourner les informations collectées
    return {
        "name": asset_name,
        "type": asset_type,
        "account_id": asset_account,
        "value": asset_value,
        "cost": asset_cost,
        "currency": asset_currency,
        "notes": asset_notes,
        "todo": asset_todo,
        "isin": asset_isin,
        "ounces": asset_ounces
    }