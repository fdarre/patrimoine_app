"""
Utilitaires pour les formulaires d'édition et d'ajout d'actifs
"""
import streamlit as st
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from database.models import Bank, Account
from config.app_config import CURRENCIES, PRODUCT_TYPES


def get_banks_and_accounts(db: Session, user_id: str,
                           selected_bank_id: str = None) -> Tuple[List[Bank], List[Account]]:
    """
    Récupère les banques et les comptes associés pour un utilisateur

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
        selected_bank_id: ID de la banque sélectionnée (optionnel)

    Returns:
        Tuple (liste des banques, liste des comptes filtrés)
    """
    banks = db.query(Bank).filter(Bank.owner_id == user_id).all()

    if selected_bank_id:
        # Filtrer les comptes selon la banque sélectionnée
        accounts = db.query(Account).filter(Account.bank_id == selected_bank_id).all()
    else:
        # Si aucune banque sélectionnée et qu'il y a des banques disponibles,
        # utiliser la première banque
        if banks:
            selected_bank_id = banks[0].id
            accounts = db.query(Account).filter(Account.bank_id == selected_bank_id).all()
        else:
            accounts = []

    return banks, accounts


def render_basic_asset_info(
        db: Session,
        user_id: str,
        existing_data: Dict[str, Any] = None,
        key_prefix: str = ""
) -> Dict[str, Any]:
    """
    Affiche les champs communs pour un formulaire d'actif et retourne les valeurs

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
        existing_data: Valeurs existantes pour pré-remplir le formulaire
        key_prefix: Préfixe pour les clés des widgets Streamlit

    Returns:
        Dictionnaire des valeurs saisies
    """
    # Valeurs par défaut
    if existing_data is None:
        existing_data = {}

    col1, col2 = st.columns(2)

    with col1:
        asset_name = st.text_input(
            "Nom de l'actif",
            value=existing_data.get("name", ""),
            key=f"{key_prefix}asset_name"
        )

        asset_type = st.selectbox(
            "Type de produit",
            options=PRODUCT_TYPES,
            index=PRODUCT_TYPES.index(existing_data.get("type", PRODUCT_TYPES[0]))
            if "type" in existing_data else 0,
            key=f"{key_prefix}asset_type",
            help="Type de produit financier (ETF, action individuelle, etc.)"
        )

        asset_isin = st.text_input(
            "Code ISIN (optionnel)",
            value=existing_data.get("isin", ""),
            key=f"{key_prefix}asset_isin",
            help="Pour les ETF, actions et obligations"
        )

        # Champs spécifiques selon le type
        if asset_type == "metal":
            asset_ounces = st.number_input(
                "Quantité (onces)",
                min_value=0.0,
                value=float(existing_data.get("ounces", 1.0)),
                format="%.3f",
                key=f"{key_prefix}asset_ounces"
            )
        else:
            asset_ounces = None

    with col2:
        # Sélection des banques et comptes
        banks, _ = get_banks_and_accounts(db, user_id)

        # Sélection de la banque
        bank_options = [bank.id for bank in banks]
        bank_index = 0

        if "bank_id" in existing_data and existing_data["bank_id"] in bank_options:
            bank_index = bank_options.index(existing_data["bank_id"])

        asset_bank = st.selectbox(
            "Banque",
            options=bank_options,
            index=bank_index,
            format_func=lambda x: next((f"{bank.nom}" for bank in banks if bank.id == x), ""),
            key=f"{key_prefix}asset_bank"
        )

        # Filtrer les comptes selon la banque sélectionnée
        _, bank_accounts = get_banks_and_accounts(db, user_id, asset_bank)

        if bank_accounts:
            account_options = [acc.id for acc in bank_accounts]
            account_index = 0

            if "account_id" in existing_data and existing_data["account_id"] in account_options:
                account_index = account_options.index(existing_data["account_id"])

            asset_account = st.selectbox(
                "Compte",
                options=account_options,
                index=account_index,
                format_func=lambda x: next((f"{acc.libelle}" for acc in bank_accounts if acc.id == x), ""),
                key=f"{key_prefix}asset_account"
            )
        else:
            st.warning(f"Aucun compte disponible pour cette banque.")
            asset_account = None

        asset_value = st.number_input(
            "Valeur actuelle",
            min_value=0.0,
            value=float(existing_data.get("value", 0.0)),
            format="%.2f",
            key=f"{key_prefix}asset_value"
        )

        asset_cost = st.number_input(
            "Prix de revient",
            min_value=0.0,
            value=float(existing_data.get("cost", 0.0)),
            format="%.2f",
            help="Laissez à 0 pour utiliser la valeur actuelle",
            key=f"{key_prefix}asset_cost"
        )

        currency_index = 0
        if "currency" in existing_data and existing_data["currency"] in CURRENCIES:
            currency_index = CURRENCIES.index(existing_data["currency"])

        asset_currency = st.selectbox(
            "Devise",
            options=CURRENCIES,
            index=currency_index,
            key=f"{key_prefix}asset_currency"
        )

    # Champs supplémentaires
    st.subheader("Informations additionnelles")
    asset_notes = st.text_area(
        "Notes",
        value=existing_data.get("notes", ""),
        key=f"{key_prefix}asset_notes",
        help="Notes personnelles sur cet actif"
    )

    asset_todo = st.text_area(
        "Tâche à faire (optionnel)",
        value=existing_data.get("todo", ""),
        key=f"{key_prefix}asset_todo"
    )

    # Retourner les informations collectées
    return {
        "name": asset_name,
        "type": asset_type,
        "account_id": asset_account,
        "bank_id": asset_bank,
        "value": asset_value,
        "cost": asset_cost,
        "currency": asset_currency,
        "notes": asset_notes,
        "todo": asset_todo,
        "isin": asset_isin,
        "ounces": asset_ounces
    }