"""
Service de gestion des banques
"""

from typing import Dict, Any, List, Optional
import pandas as pd

from models.bank import Bank


class BankService:
    """Service pour la gestion des banques"""

    @staticmethod
    def add_bank(banks: Dict[str, Dict[str, Any]], bank_id: str, nom: str, notes: str = "") -> bool:
        """
        Ajoute une nouvelle banque

        Args:
            banks: Dictionnaire des banques existantes
            bank_id: Identifiant unique de la banque
            nom: Nom de la banque
            notes: Notes sur la banque

        Returns:
            True si l'ajout a réussi, False sinon
        """
        if not bank_id or not nom:
            return False

        # Nettoyer l'identifiant (pas d'espaces, minuscules)
        bank_id = bank_id.strip().lower().replace(" ", "_")

        if bank_id in banks:
            return False

        banks[bank_id] = {
            "nom": nom,
            "notes": notes or ""
        }

        return True

    @staticmethod
    def update_bank(banks: Dict[str, Dict[str, Any]], bank_id: str, nom: str, notes: str = "") -> bool:
        """
        Met à jour une banque existante

        Args:
            banks: Dictionnaire des banques existantes
            bank_id: Identifiant de la banque à mettre à jour
            nom: Nouveau nom
            notes: Nouvelles notes

        Returns:
            True si la mise à jour a réussi, False sinon
        """
        if bank_id not in banks:
            return False

        banks[bank_id]["nom"] = nom
        banks[bank_id]["notes"] = notes

        return True

    @staticmethod
    def delete_bank(
            banks: Dict[str, Dict[str, Any]],
            accounts: Dict[str, Dict[str, Any]],
            bank_id: str
    ) -> bool:
        """
        Supprime une banque si elle n'a pas de comptes associés

        Args:
            banks: Dictionnaire des banques
            accounts: Dictionnaire des comptes
            bank_id: Identifiant de la banque à supprimer

        Returns:
            True si la suppression a réussi, False sinon
        """
        if bank_id not in banks:
            return False

        # Vérifier si des comptes sont liés à cette banque
        has_accounts = any(acc["banque_id"] == bank_id for acc in accounts.values())

        if has_accounts:
            return False

        del banks[bank_id]
        return True

    @staticmethod
    def get_banks_dataframe(banks: Dict[str, Dict[str, Any]], accounts: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """
        Crée un DataFrame Pandas avec les banques

        Args:
            banks: Dictionnaire des banques
            accounts: Dictionnaire des comptes

        Returns:
            DataFrame Pandas des banques
        """
        data = []
        for bank_id, bank in banks.items():
            # Compter les comptes associés à cette banque
            account_count = sum(1 for acc in accounts.values() if acc["banque_id"] == bank_id)
            data.append([bank_id, bank["nom"], account_count])

        return pd.DataFrame(data, columns=["ID", "Nom", "Nb comptes"])