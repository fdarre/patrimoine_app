# ui/assets/add_form.py
"""
Module contenant le formulaire d'ajout d'actifs
"""
import streamlit as st
from sqlalchemy.orm import Session

from database.models import Bank, Account, Asset
from services.asset_service import asset_service

from services.data_service import DataService
from config.app_config import ASSET_CATEGORIES, PRODUCT_TYPES, CURRENCIES
from utils.calculations import get_default_geo_zones
from .allocation_form import create_allocation_form
from .geo_allocation_form import create_geo_allocation_form
from .components import apply_button_styling


def show_add_asset_form(db: Session, user_id: str):
    """
    Affiche un formulaire amélioré pour l'ajout d'actifs

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.subheader("Ajouter un nouvel actif")

    # Récupérer les comptes disponibles
    accounts = db.query(Account).join(Bank).filter(Bank.owner_id == user_id).all()

    if not accounts:
        st.warning("Veuillez d'abord ajouter des comptes avant d'ajouter des actifs.")
    else:
        # Interface à onglets pour un ajout plus intuitif
        form_tabs = st.tabs(["📝 Informations de base", "📊 Allocation", "🌍 Répartition géographique"])

        with form_tabs[0]:
            # Collecter les informations de base
            asset_info = collect_basic_asset_info(db, user_id)

        with form_tabs[1]:
            # Collecter les informations d'allocation
            allocation = create_allocation_form("new_asset")

        with form_tabs[2]:
            # Si aucune catégorie n'a été sélectionnée, afficher un message
            if not allocation:
                st.warning(
                    "Veuillez d'abord spécifier au moins une catégorie d'actif avec un pourcentage supérieur à 0%.")
                geo_allocation = {}
                all_geo_valid = False
            else:
                # Collecter les informations de répartition géographique
                geo_allocation, all_geo_valid = create_geo_allocation_form(allocation, "new_asset")

        # Bouton d'ajout d'actif
        st.subheader("Validation")

        # Vérifier si toutes les conditions sont remplies
        form_valid = (
                asset_info["name"] and
                asset_info["account_id"] and
                asset_info["value"] > 0 and
                sum(allocation.values()) == 100 and
                all_geo_valid
        )

        # Afficher un message récapitulatif avant validation
        if form_valid:
            st.success("Toutes les informations sont valides. Vous pouvez ajouter l'actif.")
        else:
            display_form_validation_errors(asset_info, allocation)

        # Styliser le bouton selon l'état de validité du formulaire
        apply_button_styling(form_valid)

        # Bouton d'ajout d'actif
        submit_button = st.button("Ajouter l'actif", key="btn_add_asset", disabled=not form_valid)

        if submit_button:
            try:
                # Utiliser le prix de revient si spécifié, sinon utiliser la valeur actuelle
                prix_de_revient = asset_info["cost"] if asset_info["cost"] > 0 else asset_info["value"]

                # Ajouter l'actif
                new_asset = asset_service.add_asset(
                    db=db,  # Ajout du paramètre db
                    user_id=user_id,
                    nom=asset_info["name"],
                    compte_id=asset_info["account_id"],
                    type_produit=asset_info["type"],
                    allocation=allocation,
                    geo_allocation=geo_allocation,
                    valeur_actuelle=asset_info["value"],
                    prix_de_revient=prix_de_revient,
                    devise=asset_info["currency"],
                    notes=asset_info["notes"],
                    todo=asset_info["todo"],
                    isin=asset_info["isin"] if asset_info["isin"] else None,
                    ounces=asset_info["ounces"] if asset_info["type"] == "metal" else None
                )

                if new_asset:
                    # Mettre à jour l'historique
                    DataService.record_history_entry(db, user_id)
                    st.success(f"Actif '{asset_info['name']}' ajouté avec succès.")
                    st.rerun()
                else:
                    st.error("Erreur lors de l'ajout de l'actif.")
            except ValueError as e:
                st.error(f"Les valeurs numériques sont invalides: {str(e)}")
            except Exception as e:
                st.error(f"Erreur inattendue: {str(e)}")


def collect_basic_asset_info(db, user_id):
    """
    Collecte les informations de base d'un actif

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur

    Returns:
        Dictionnaire contenant les informations de base de l'actif
    """
    col1, col2 = st.columns(2)

    with col1:
        asset_name = st.text_input("Nom de l'actif", key="new_asset_name")
        asset_type = st.selectbox(
            "Type de produit",
            options=PRODUCT_TYPES,
            key="new_asset_type",
            help="Type de produit financier (ETF, action individuelle, etc.)"
        )
        asset_isin = st.text_input("Code ISIN (optionnel)",
                                   key="new_asset_isin",
                                   help="Pour les ETF, actions et obligations")

        # Champs spécifiques selon le type
        if asset_type == "metal":
            asset_ounces = st.number_input("Quantité (onces)", min_value=0.0, value=1.0, format="%.3f")
        else:
            asset_ounces = None

    with col2:
        # Sélection de banque et compte avec interface améliorée
        banks = db.query(Bank).filter(Bank.owner_id == user_id).all()

        asset_bank = st.selectbox(
            "Banque",
            options=[bank.id for bank in banks],
            format_func=lambda x: next((f"{bank.nom}" for bank in banks if bank.id == x), ""),
            key="new_asset_bank"
        )

        # Filtrer les comptes selon la banque sélectionnée
        bank_accounts = db.query(Account).filter(Account.bank_id == asset_bank).all()

        if bank_accounts:
            asset_account = st.selectbox(
                "Compte",
                options=[acc.id for acc in bank_accounts],
                format_func=lambda x: next((f"{acc.libelle}" for acc in bank_accounts if acc.id == x), ""),
                key="new_asset_account"
            )
        else:
            st.warning(f"Aucun compte disponible pour cette banque.")
            asset_account = None

        asset_value = st.number_input("Valeur actuelle",
                                      min_value=0.0,
                                      value=0.0,
                                      format="%.2f",
                                      key="new_asset_value")

        asset_cost = st.number_input("Prix de revient",
                                     min_value=0.0,
                                     value=0.0,
                                     format="%.2f",
                                     help="Laissez à 0 pour utiliser la valeur actuelle",
                                     key="new_asset_cost")

        asset_currency = st.selectbox(
            "Devise",
            options=CURRENCIES,
            index=0,
            key="new_asset_currency"
        )

    # Champs supplémentaires
    st.subheader("Informations additionnelles")
    asset_notes = st.text_area("Notes", key="new_asset_notes",
                               help="Notes personnelles sur cet actif")
    asset_todo = st.text_area("Tâche à faire (optionnel)", key="new_asset_todo")

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


def display_form_validation_errors(asset_info, allocation):
    """
    Affiche les erreurs de validation du formulaire

    Args:
        asset_info: Informations de base de l'actif
        allocation: Dictionnaire d'allocation par catégorie
    """
    if not asset_info["name"]:
        st.warning("Le nom de l'actif est obligatoire.")
    if not asset_info["account_id"]:
        st.warning("Veuillez sélectionner un compte.")
    if asset_info["value"] <= 0:
        st.warning("La valeur actuelle doit être supérieure à 0.")

    allocation_total = sum(allocation.values()) if allocation else 0
    if allocation_total != 100:
        st.warning(f"Le total des allocations doit être de 100% (actuellement: {allocation_total}%).")