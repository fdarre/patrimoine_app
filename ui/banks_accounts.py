"""
Interface de gestion des banques et comptes
"""
# Imports de bibliothèques tierces
import pandas as pd
import streamlit as st

# Imports de l'application
from config.app_config import ACCOUNT_TYPES
from database.db_config import get_db_session  # Utilisation du gestionnaire de contexte
from database.models import Bank, Account, Asset
from services.account_service import account_service
from services.bank_service import bank_service
from utils.session_manager import session_manager  # Utilisation du gestionnaire de session


def show_banks_accounts():
    """
    Affiche l'interface de gestion des banques et comptes
    """
    # Récupérer l'ID utilisateur depuis le gestionnaire de session
    user_id = session_manager.get("user_id")

    if not user_id:
        st.error("Utilisateur non authentifié")
        return

    st.header("Banques & Comptes", anchor=False)

    # Onglets pour banques et comptes
    tab1, tab2 = st.tabs(["Banques", "Comptes"])

    # Utiliser le gestionnaire de contexte pour la session DB
    with get_db_session() as db:
        with tab1:
            show_banks_tab(db, user_id)

        with tab2:
            show_accounts_tab(db, user_id)


def show_banks_tab(db, user_id: str):
    """Affiche l'onglet de gestion des banques"""
    st.subheader("Gestion des banques")

    col1, col2 = st.columns([2, 3])

    with col1:
        st.write("Ajouter une banque")
        bank_id = st.text_input("Identifiant unique", key="bank_id_input",
                                help="Ex: boursorama, bnp, etc. (sans espaces)")
        bank_name = st.text_input("Nom de la banque", key="bank_name_input")
        bank_notes = st.text_area("Notes", key="bank_notes_input", height=100)

        if st.button("Ajouter une banque", key="add_bank_btn"):
            if bank_service.add_bank(db, user_id, bank_id, bank_name, bank_notes):
                st.success(f"Banque '{bank_name}' ajoutée avec succès.")
                st.rerun()
            else:
                st.warning(
                    "Veuillez remplir les champs obligatoires ou vérifier que l'identifiant n'existe pas déjà.")

    with col2:
        st.write("Liste des banques")
        # Obtenir toutes les banques de l'utilisateur avec le nombre de comptes en une seule requête
        banks_with_counts = bank_service.get_banks_with_account_counts(db, user_id)

        if banks_with_counts:
            # Créer un DataFrame directement à partir des résultats de la requête
            banks_df = pd.DataFrame(
                [(bank.id, bank.nom, count) for bank, count in banks_with_counts],
                columns=["ID", "Nom", "Nb comptes"]
            )
            st.dataframe(banks_df, use_container_width=True)

            # Sélection d'une banque pour édition
            selected_bank_id = st.selectbox(
                "Sélectionner une banque pour éditer",
                options=[bank.id for bank, _ in banks_with_counts],
                format_func=lambda x: next((f"{bank.nom} ({bank.id})" for bank, _ in banks_with_counts if bank.id == x), ""),
                key="select_bank_edit"
            )

            selected_bank = bank_service.get_bank(db, selected_bank_id)

            if selected_bank:
                show_bank_editor(db, selected_bank)
        else:
            st.info("Aucune banque n'a été ajoutée pour le moment.")


def show_bank_editor(db, bank: Bank):
    """Affiche l'éditeur de banque"""
    with st.expander("Éditer la banque", expanded=True):
        edit_bank_name = st.text_input("Nom", value=bank.nom, key="edit_bank_name")
        edit_bank_notes = st.text_area("Notes", value=bank.notes or "", key="edit_bank_notes")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Mettre à jour", key="update_bank_btn"):
                if bank_service.update_bank(db, bank.id, edit_bank_name, edit_bank_notes):
                    st.success(f"Banque '{edit_bank_name}' mise à jour avec succès.")
                    st.rerun()
                else:
                    st.error("Erreur lors de la mise à jour de la banque.")

        with col2:
            if st.button("Supprimer", key="delete_bank_btn"):
                if bank_service.delete_bank(db, bank.id):
                    st.success("Banque supprimée avec succès.")
                    st.rerun()
                else:
                    st.error("Impossible de supprimer cette banque car elle contient des comptes.")


def show_accounts_tab(db, user_id: str):
    """Affiche l'onglet de gestion des comptes"""
    st.subheader("Gestion des comptes")

    col1, col2 = st.columns([2, 3])

    with col1:
        show_add_account_form(db, user_id)

    with col2:
        show_accounts_list(db, user_id)


def show_add_account_form(db, user_id: str):
    """Affiche le formulaire d'ajout de compte"""
    st.write("Ajouter un compte")

    # Récupérer les banques de l'utilisateur
    banks = bank_service.get_banks(db, user_id)

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
            if account_service.add_account(db, account_id, account_bank, account_type, account_label):
                st.success(f"Compte '{account_label}' ajouté avec succès.")
                st.rerun()
            else:
                st.warning(
                    "Veuillez remplir tous les champs obligatoires ou vérifier que l'identifiant n'existe pas déjà.")


def show_accounts_list(db, user_id: str):
    """Affiche la liste des comptes avec filtre par banque"""
    st.write("Liste des comptes")

    # Récupérer les banques de l'utilisateur
    banks = bank_service.get_banks(db, user_id)

    if banks:
        # Filtre par banque optionnel
        filter_bank = st.selectbox(
            "Filtrer par banque",
            options=["Toutes les banques"] + [bank.id for bank in banks],
            format_func=lambda x: "Toutes les banques" if x == "Toutes les banques" else
                    next((f"{bank.nom} ({bank.id})" for bank in banks if bank.id == x), ""),
            key="filter_bank_select"
        )

        # Obtenir les comptes selon le filtre - en une seule requête avec la somme des valeurs des actifs
        # CORRECTION: Passage de None au lieu de "Toutes les banques" quand aucun filtre
        filter_bank_id = None if filter_bank == "Toutes les banques" else filter_bank
        accounts_with_values = account_service.get_accounts_with_total_values(db, user_id, filter_bank_id)

        if accounts_with_values:
            # Créer directement un DataFrame avec les données
            accounts_df = pd.DataFrame(
                [(acc.id, bank.nom, acc.type, acc.libelle, f"{total_value:.2f} €")
                for acc, bank, total_value in accounts_with_values],
                columns=["ID", "Banque", "Type", "Libellé", "Valeur totale"]
            )
            st.dataframe(accounts_df, use_container_width=True)

            # Sélection d'un compte pour édition
            account_options = [acc.id for acc, _, _ in accounts_with_values]

            if account_options:
                selected_account_id = st.selectbox(
                    "Sélectionner un compte pour éditer",
                    options=account_options,
                    format_func=lambda x: next((f"{acc.libelle} ({acc.id})" for acc, _, _ in accounts_with_values if acc.id == x), ""),
                    key="select_account_edit"
                )

                # Récupérer le compte sélectionné
                selected_account = next((acc for acc, _, _ in accounts_with_values if acc.id == selected_account_id), None)

                if selected_account:
                    show_account_editor(db, selected_account, banks, user_id)
        else:
            st.info("Aucun compte n'a encore été ajouté.")
    else:
        st.info("Aucune banque n'a encore été ajoutée.")


def show_account_editor(db, account: Account, banks: list, user_id: str):
    """Affiche l'éditeur de compte et la liste des actifs associés"""
    with st.expander("Éditer le compte", expanded=True):
        edit_account_bank = st.selectbox(
            "Banque",
            options=[bank.id for bank in banks],
            format_func=lambda x: next((f"{bank.nom} ({bank.id})" for bank in banks if bank.id == x), ""),
            index=[bank.id for bank in banks].index(account.bank_id) if account.bank_id in [bank.id for bank in banks] else 0,
            key="edit_account_bank"
        )

        edit_account_type = st.selectbox(
            "Type de compte",
            options=ACCOUNT_TYPES,
            index=ACCOUNT_TYPES.index(account.type) if account.type in ACCOUNT_TYPES else 0,
            key="edit_account_type"
        )

        edit_account_label = st.text_input("Libellé", value=account.libelle,
                                           key="edit_account_label")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Mettre à jour", key="update_account_btn"):
                if account_service.update_account(
                        db,
                        account.id,
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
                if account_service.delete_account(db, account.id):
                    st.success("Compte supprimé avec succès.")
                    st.rerun()
                else:
                    st.error("Impossible de supprimer ce compte car il contient des actifs.")

    # Récupérer et afficher les actifs de ce compte avec tous les détails en une seule requête
    assets_with_details = db.query(Asset).filter(
        Asset.owner_id == user_id,
        Asset.account_id == account.id
    ).all()

    show_account_assets(assets_with_details)


def show_account_assets(assets: list):
    """Affiche les actifs d'un compte"""
    if assets:
        st.subheader(f"Actifs dans ce compte ({len(assets)})")

        # Calculer la valeur totale du compte
        account_value = sum(asset.valeur_actuelle for asset in assets)
        st.info(f"Valeur totale du compte: {account_value:,.2f} €".replace(",", " "))

        # Créer le DataFrame des actifs
        data = []
        for asset in assets:
            pv = asset.valeur_actuelle - asset.prix_de_revient
            pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0

            # Afficher la répartition des allocations
            allocation_display = " / ".join(
                f"{cat.capitalize()} {pct}%" for cat, pct in asset.allocation.items())

            data.append([
                asset.nom,
                allocation_display,
                asset.type_produit,
                f"{asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " "),
                f"{pv:,.2f} {asset.devise} ({pv_percent:.2f}%)".replace(",", " "),
            ])

        df = pd.DataFrame(data, columns=["Nom", "Allocation", "Type", "Valeur", "Plus-value"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucun actif dans ce compte.")