"""
Interface de gestion des banques et comptes
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any

from models.asset import Asset
from services.bank_service import BankService
from services.account_service import AccountService
from services.data_service import DataService
from utils.constants import ACCOUNT_TYPES


def show_banks_accounts(
        banks: Dict[str, Dict[str, Any]],
        accounts: Dict[str, Dict[str, Any]],
        assets: List[Asset],
        history: List[Dict[str, Any]]
):
    """
    Affiche l'interface de gestion des banques et comptes

    Args:
        banks: Dictionnaire des banques
        accounts: Dictionnaire des comptes
        assets: Liste des actifs
        history: Liste des points d'historique
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
                if BankService.add_bank(banks, bank_id, bank_name, bank_notes):
                    # Sauvegarder les données
                    DataService.save_data(banks, accounts, assets, history)
                    st.success(f"Banque '{bank_name}' ajoutée avec succès.")
                    st.rerun()
                else:
                    st.warning(
                        "Veuillez remplir les champs obligatoires ou vérifier que l'identifiant n'existe pas déjà.")

        with col2:
            st.write("Liste des banques")
            banks_df = BankService.get_banks_dataframe(banks, accounts)
            st.dataframe(banks_df, use_container_width=True)

            if len(banks) > 0:
                # Sélection d'une banque pour édition
                selected_bank_id = st.selectbox(
                    "Sélectionner une banque pour éditer",
                    options=list(banks.keys()),
                    format_func=lambda x: f"{banks[x]['nom']} ({x})",
                    key="select_bank_edit"
                )

                bank = banks[selected_bank_id]

                with st.expander("Éditer la banque", expanded=True):
                    edit_bank_name = st.text_input("Nom", value=bank["nom"], key="edit_bank_name")
                    edit_bank_notes = st.text_area("Notes", value=bank["notes"], key="edit_bank_notes")

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("Mettre à jour", key="update_bank_btn"):
                            if BankService.update_bank(banks, selected_bank_id, edit_bank_name, edit_bank_notes):
                                DataService.save_data(banks, accounts, assets, history)
                                st.success(f"Banque '{edit_bank_name}' mise à jour avec succès.")
                                st.rerun()
                            else:
                                st.error("Erreur lors de la mise à jour de la banque.")

                    with col2:
                        if st.button("Supprimer", key="delete_bank_btn"):
                            if BankService.delete_bank(banks, accounts, selected_bank_id):
                                DataService.save_data(banks, accounts, assets, history)
                                st.success("Banque supprimée avec succès.")
                                st.rerun()
                            else:
                                st.error("Impossible de supprimer cette banque car elle contient des comptes.")

    with tab2:
        st.subheader("Gestion des comptes")

        col1, col2 = st.columns([2, 3])

        with col1:
            st.write("Ajouter un compte")

            if not banks:
                st.warning("Veuillez d'abord ajouter une banque.")
            else:
                account_id = st.text_input("Identifiant unique", key="account_id_input",
                                           help="Ex: pea_boursorama, livret_bnp, etc. (sans espaces)")

                account_bank = st.selectbox(
                    "Banque",
                    options=list(banks.keys()),
                    format_func=lambda x: f"{banks[x]['nom']} ({x})",
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
                    if AccountService.add_account(accounts, account_id, account_bank, account_type, account_label):
                        DataService.save_data(banks, accounts, assets, history)
                        st.success(f"Compte '{account_label}' ajouté avec succès.")
                        st.rerun()
                    else:
                        st.warning(
                            "Veuillez remplir tous les champs obligatoires ou vérifier que l'identifiant n'existe pas déjà.")

        with col2:
            st.write("Liste des comptes")

            # Filtre par banque optionnel
            if banks:
                filter_bank = st.selectbox(
                    "Filtrer par banque",
                    options=["Toutes les banques"] + list(banks.keys()),
                    format_func=lambda x: "Toutes les banques" if x == "Toutes les banques"
                    else f"{banks[x]['nom']} ({x})",
                    key="filter_bank_select"
                )

                if filter_bank == "Toutes les banques":
                    accounts_df = AccountService.get_accounts_dataframe(accounts, banks, assets)
                else:
                    accounts_df = AccountService.get_accounts_dataframe(accounts, banks, assets, filter_bank)

                st.dataframe(accounts_df, use_container_width=True)

                if accounts:
                    # Sélection d'un compte pour édition
                    account_options = [acc_id for acc_id in accounts.keys()
                                       if filter_bank == "Toutes les banques"
                                       or accounts[acc_id]["banque_id"] == filter_bank]

                    if account_options:
                        selected_account_id = st.selectbox(
                            "Sélectionner un compte pour éditer",
                            options=account_options,
                            format_func=lambda x: f"{accounts[x]['libelle']} ({x})",
                            key="select_account_edit"
                        )

                        account = accounts[selected_account_id]

                        with st.expander("Éditer le compte", expanded=True):
                            edit_account_bank = st.selectbox(
                                "Banque",
                                options=list(banks.keys()),
                                format_func=lambda x: f"{banks[x]['nom']} ({x})",
                                index=list(banks.keys()).index(account["banque_id"]),
                                key="edit_account_bank"
                            )

                            edit_account_type = st.selectbox(
                                "Type de compte",
                                options=ACCOUNT_TYPES,
                                index=ACCOUNT_TYPES.index(account["type"]),
                                key="edit_account_type"
                            )

                            edit_account_label = st.text_input("Libellé", value=account["libelle"],
                                                               key="edit_account_label")

                            col1, col2 = st.columns(2)

                            with col1:
                                if st.button("Mettre à jour", key="update_account_btn"):
                                    if AccountService.update_account(accounts, selected_account_id, edit_account_bank,
                                                                     edit_account_type, edit_account_label):
                                        DataService.save_data(banks, accounts, assets, history)
                                        st.success(f"Compte '{edit_account_label}' mis à jour avec succès.")
                                        st.rerun()
                                    else:
                                        st.error("Erreur lors de la mise à jour du compte.")

                            with col2:
                                if st.button("Supprimer", key="delete_account_btn"):
                                    if AccountService.delete_account(accounts, assets, selected_account_id):
                                        DataService.save_data(banks, accounts, assets, history)
                                        st.success("Compte supprimé avec succès.")
                                        st.rerun()
                                    else:
                                        st.error("Impossible de supprimer ce compte car il contient des actifs.")

                        # Afficher les actifs de ce compte
                        account_assets = [asset for asset in assets if asset.compte_id == selected_account_id]
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

                                composite_indicator = "✓" if asset.is_composite() else ""

                                data.append([
                                    asset.nom,
                                    allocation_display,
                                    asset.type_produit,
                                    f"{asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " "),
                                    f"{pv:,.2f} {asset.devise} ({pv_percent:.2f}%)".replace(",", " "),
                                    composite_indicator
                                ])

                            df = pd.DataFrame(data, columns=["Nom", "Allocation", "Type", "Valeur", "Plus-value",
                                                             "Composite"])
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("Aucun actif dans ce compte.")
                    else:
                        st.info(f"Aucun compte pour la banque sélectionnée.")
            else:
                st.info("Aucune banque n'a encore été ajoutée.")