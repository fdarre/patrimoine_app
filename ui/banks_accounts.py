"""
Interface de gestion des banques et comptes
"""

import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.models import Bank, Account, Asset
from services.bank_service import BankService
from services.account_service import AccountService
from services.data_service import DataService
from utils.constants import ACCOUNT_TYPES

def show_banks_accounts(db: Session, user_id: str):
    """
    Affiche l'interface de gestion des banques et comptes

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.header("Banques & Comptes", anchor=False)

    # Onglets pour banques et comptes
    tab1, tab2 = st.tabs(["Banques", "Comptes"])

    with tab1:
        st.subheader("Gestion des banques")

        col1, col2 = st.columns([2, 3])

        with col1:
            st.write("Ajouter une banque")
            bank_id = st.text_input("Identifiant unique", key="bank_id_input",
                                    help="Ex: boursorama, bnp, etc. (sans espaces)")
            bank_name = st.text_input("Nom de la banque", key="bank_name_input")
            bank_notes = st.text_area("Notes", key="bank_notes_input", height=100)

            if st.button("Ajouter une banque", key="add_bank_btn"):
                if BankService.add_bank(db, user_id, bank_id, bank_name, bank_notes):
                    st.success(f"Banque '{bank_name}' ajoutée avec succès.")
                    st.rerun()
                else:
                    st.warning(
                        "Veuillez remplir les champs obligatoires ou vérifier que l'identifiant n'existe pas déjà.")

        with col2:
            st.write("Liste des banques")
            # Obtenir toutes les banques de l'utilisateur
            banks = BankService.get_banks(db, user_id)

            if banks:
                # Créer un DataFrame avec les banques
                banks_df = BankService.get_banks_dataframe(db, user_id)
                st.dataframe(banks_df, use_container_width=True)

                # Sélection d'une banque pour édition
                selected_bank_id = st.selectbox(
                    "Sélectionner une banque pour éditer",
                    options=[bank.id for bank in banks],
                    format_func=lambda x: next((f"{bank.nom} ({bank.id})" for bank in banks if bank.id == x), ""),
                    key="select_bank_edit"
                )

                selected_bank = BankService.get_bank(db, selected_bank_id)

                if selected_bank:
                    with st.expander("Éditer la banque", expanded=True):
                        edit_bank_name = st.text_input("Nom", value=selected_bank.nom, key="edit_bank_name")
                        edit_bank_notes = st.text_area("Notes", value=selected_bank.notes or "", key="edit_bank_notes")

                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button("Mettre à jour", key="update_bank_btn"):
                                if BankService.update_bank(db, selected_bank_id, edit_bank_name, edit_bank_notes):
                                    st.success(f"Banque '{edit_bank_name}' mise à jour avec succès.")
                                    st.rerun()
                                else:
                                    st.error("Erreur lors de la mise à jour de la banque.")

                        with col2:
                            if st.button("Supprimer", key="delete_bank_btn"):
                                if BankService.delete_bank(db, selected_bank_id):
                                    st.success("Banque supprimée avec succès.")
                                    st.rerun()
                                else:
                                    st.error("Impossible de supprimer cette banque car elle contient des comptes.")
            else:
                st.info("Aucune banque n'a été ajoutée pour le moment.")

    with tab2:
        st.subheader("Gestion des comptes")

        col1, col2 = st.columns([2, 3])

        with col1:
            st.write("Ajouter un compte")

            # Récupérer les banques de l'utilisateur
            banks = BankService.get_banks(db, user_id)

            if not banks:
                st.warning("Veuillez d'abord ajouter une banque.")
            else:
                account_id = st.text_input("Identifiant unique", key="account_id_input",
                                           help="Ex: pea_boursorama, livret_bnp, etc. (sans espaces)")

                account_bank = st.selectbox(
                    "Banque",
                    options=[bank.id for bank in banks],
                    format_func=lambda x: next((f"{bank.nom} ({bank.id})" for bank in banks if bank.id == x), ""),
                    key="account_bank_input"
                )

                account_type = st.selectbox(
                    "Type de compte",
                    options=ACCOUNT_TYPES,
                    key="account_type_input"
                )

                account_label = st.text_input("Libellé", key="account_label_input",
                                              help="Ex: PEA, Livret A, Compte courant, etc.")

                if st.button("Ajouter un compte", key="add_account_btn"):
                    if AccountService.add_account(db, account_id, account_bank, account_type, account_label):
                        st.success(f"Compte '{account_label}' ajouté avec succès.")
                        st.rerun()
                    else:
                        st.warning(
                            "Veuillez remplir tous les champs obligatoires ou vérifier que l'identifiant n'existe pas déjà.")

        with col2:
            st.write("Liste des comptes")

            # Récupérer les banques de l'utilisateur
            banks = BankService.get_banks(db, user_id)

            if banks:
                # Filtre par banque optionnel
                filter_bank = st.selectbox(
                    "Filtrer par banque",
                    options=["Toutes les banques"] + [bank.id for bank in banks],
                    format_func=lambda x: "Toutes les banques" if x == "Toutes les banques" else
                               next((f"{bank.nom} ({bank.id})" for bank in banks if bank.id == x), ""),
                    key="filter_bank_select"
                )

                # Obtenir les comptes selon le filtre
                if filter_bank == "Toutes les banques":
                    accounts = AccountService.get_accounts(db, user_id)
                    accounts_df = AccountService.get_accounts_dataframe(db, user_id)
                else:
                    accounts = AccountService.get_accounts(db, user_id, filter_bank)
                    accounts_df = AccountService.get_accounts_dataframe(db, user_id, filter_bank)

                if accounts:
                    st.dataframe(accounts_df, use_container_width=True)

                    # Sélection d'un compte pour édition
                    account_options = [acc.id for acc in accounts]

                    if account_options:
                        selected_account_id = st.selectbox(
                            "Sélectionner un compte pour éditer",
                            options=account_options,
                            format_func=lambda x: next((f"{acc.libelle} ({acc.id})" for acc in accounts if acc.id == x), ""),
                            key="select_account_edit"
                        )

                        selected_account = AccountService.get_account(db, selected_account_id)

                        if selected_account:
                            with st.expander("Éditer le compte", expanded=True):
                                edit_account_bank = st.selectbox(
                                    "Banque",
                                    options=[bank.id for bank in banks],
                                    format_func=lambda x: next((f"{bank.nom} ({bank.id})" for bank in banks if bank.id == x), ""),
                                    index=[bank.id for bank in banks].index(selected_account.bank_id) if selected_account.bank_id in [bank.id for bank in banks] else 0,
                                    key="edit_account_bank"
                                )

                                edit_account_type = st.selectbox(
                                    "Type de compte",
                                    options=ACCOUNT_TYPES,
                                    index=ACCOUNT_TYPES.index(selected_account.type) if selected_account.type in ACCOUNT_TYPES else 0,
                                    key="edit_account_type"
                                )

                                edit_account_label = st.text_input("Libellé", value=selected_account.libelle,
                                                                   key="edit_account_label")

                                col1, col2 = st.columns(2)

                                with col1:
                                    if st.button("Mettre à jour", key="update_account_btn"):
                                        if AccountService.update_account(
                                                db,
                                                selected_account_id,
                                                edit_account_bank,
                                                edit_account_type,
                                                edit_account_label
                                        ):
                                            st.success(f"Compte '{edit_account_label}' mis à jour avec succès.")
                                            st.rerun()
                                        else:
                                            st.error("Erreur lors de la mise à jour du compte.")

                                with col2:
                                    if st.button("Supprimer", key="delete_account_btn"):
                                        if AccountService.delete_account(db, selected_account_id):
                                            st.success("Compte supprimé avec succès.")
                                            st.rerun()
                                        else:
                                            st.error("Impossible de supprimer ce compte car il contient des actifs.")

                            # Afficher les actifs de ce compte
                            account_assets = db.query(Asset).filter(
                                Asset.owner_id == user_id,
                                Asset.account_id == selected_account_id
                            ).all()

                            if account_assets:
                                st.subheader(f"Actifs dans ce compte ({len(account_assets)})")

                                # Calculer la valeur totale du compte
                                account_value = sum(asset.valeur_actuelle for asset in account_assets)
                                st.info(f"Valeur totale du compte: {account_value:,.2f} €".replace(",", " "))

                                # Créer le DataFrame des actifs
                                data = []
                                for asset in account_assets:
                                    pv = asset.valeur_actuelle - asset.prix_de_revient
                                    pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0

                                    # Afficher la répartition des allocations
                                    allocation_display = " / ".join(
                                        f"{cat.capitalize()} {pct}%" for cat, pct in asset.allocation.items())

                                    # Suppression de la référence à asset.composants
                                    # Cette ligne a été supprimée: composite_indicator = "✓" if asset.composants else ""

                                    data.append([
                                        asset.nom,
                                        allocation_display,
                                        asset.type_produit,
                                        f"{asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " "),
                                        f"{pv:,.2f} {asset.devise} ({pv_percent:.2f}%)".replace(",", " "),
                                        # Suppression de composite_indicator de cette liste
                                    ])

                                df = pd.DataFrame(data, columns=["Nom", "Allocation", "Type", "Valeur", "Plus-value"])
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.info("Aucun actif dans ce compte.")
                        else:
                            st.error("Compte introuvable.")
                    else:
                        st.info(f"Aucun compte pour la banque sélectionnée.")
                else:
                    st.info("Aucun compte n'a encore été ajouté.")
            else:
                st.info("Aucune banque n'a encore été ajoutée.")