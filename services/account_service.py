"""
Service de gestion des comptes
"""

from typing import Dict, Any, List, Optional
import pandas as pd

from models.account import Account


class AccountService:
    """Service pour la gestion des comptes"""

    @staticmethod
    def add_account(
            accounts: Dict[str, Dict[str, Any]],
            account_id: str,
            bank_id: str,
            account_type: str,
            account_label: str
    ) -> bool:
        """
        Ajoute un nouveau compte

        Args:
            accounts: Dictionnaire des comptes existants
            account_id: Identifiant unique du compte
            bank_id: Identifiant de la banque associée
            account_type: Type de compte
            account_label: Libellé du compte

        Returns:
            True si l'ajout a réussi, False sinon
        """
        if not account_id or not bank_id or not account_type or not account_label:
            return False

        # Nettoyer l'identifiant (pas d'espaces, minuscules)
        account_id = account_id.strip().lower().replace(" ", "_")

        if account_id in accounts:
            return False

        accounts[account_id] = {
            "banque_id": bank_id,
            "type": account_type,
            "libelle": account_label
        }

        return True

    @staticmethod
    def update_account(
            accounts: Dict[str, Dict[str, Any]],
            account_id: str,
            bank_id: str,
            account_type: str,
            account_label: str
    ) -> bool:
        """
        Met à jour un compte existant

        Args:
            accounts: Dictionnaire des comptes existants
            account_id: Identifiant du compte à mettre à jour
            bank_id: Identifiant de la banque associée
            account_type: Type de compte
            account_label: Libellé du compte

        Returns:
            True si la mise à jour a réussi, False sinon
        """
        if account_id not in accounts:
            return False

        accounts[account_id]["banque_id"] = bank_id
        accounts[account_id]["type"] = account_type
        accounts[account_id]["libelle"] = account_label

        return True

    @staticmethod
    def delete_account(
            accounts: Dict[str, Dict[str, Any]],
            assets: List[Any],
            account_id: str
    ) -> bool:
        """
        Supprime un compte s'il n'a pas d'actifs associés

        Args:
            accounts: Dictionnaire des comptes
            assets: Liste des actifs
            account_id: Identifiant du compte à supprimer

        Returns:
            True si la suppression a réussi, False sinon
        """
        if account_id not in accounts:
            return False

        # Vérifier si des actifs sont liés à ce compte
        has_assets = any(asset.compte_id == account_id for asset in assets)

        if has_assets:
            return False

        del accounts[account_id]
        return True

    @staticmethod
    def get_accounts_dataframe(
            accounts: Dict[str, Dict[str, Any]],
            banks: Dict[str, Dict[str, Any]],
            assets: List[Any],
            bank_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Crée un DataFrame Pandas avec les comptes filtrés

        Args:
            accounts: Dictionnaire des comptes
            banks: Dictionnaire des banques
            assets: Liste des actifs
            bank_id: Filtre par ID de banque (optionnel)

        Returns:
            DataFrame Pandas des comptes filtrés
        """
        data = []
        for acc_id, acc in accounts.items():
            if bank_id is None or acc["banque_id"] == bank_id:
                # Calculer la valeur totale des actifs dans ce compte
                total_value = sum(asset.valeur_actuelle for asset in assets if asset.compte_id == acc_id)
                bank_name = banks[acc["banque_id"]]["nom"]
                data.append([acc_id, bank_name, acc["type"], acc["libelle"], f"{total_value:.2f} €"])

        return pd.DataFrame(data, columns=["ID", "Banque", "Type", "Libellé", "Valeur totale"])