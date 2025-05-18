"""
Service de gestion des comptes avec SQLAlchemy
"""
from typing import List, Optional, Tuple

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import Account, Asset, Bank
from services.base_service import BaseService
from utils.decorators import handle_exceptions
from utils.logger import get_logger

logger = get_logger(__name__)


class AccountService(BaseService[Account]):
    """Service pour la gestion des comptes avec SQLAlchemy"""

    def __init__(self):
        super().__init__(Account)

    @handle_exceptions
    def get_accounts(self, db: Session, user_id: str, bank_id: Optional[str] = None) -> List[Account]:
        """
        Récupère tous les comptes d'un utilisateur, optionnellement filtrés par banque

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            bank_id: ID de la banque (optionnel)

        Returns:
            Liste des comptes
        """
        query = db.query(Account).join(Bank).filter(Bank.owner_id == user_id)

        if bank_id:
            query = query.filter(Account.bank_id == bank_id)

        return query.all()

    @handle_exceptions
    def get_account(self, db: Session, account_id: str) -> Optional[Account]:
        """
        Récupère un compte par son ID

        Args:
            db: Session de base de données
            account_id: ID du compte

        Returns:
            Le compte ou None
        """
        return self.get_by_id(db, account_id)

    @handle_exceptions
    def add_account(
            self, db: Session,
            account_id: str,
            bank_id: str,
            account_type: str,
            account_label: str
    ) -> Optional[Account]:
        """
        Ajoute un nouveau compte

        Args:
            db: Session de base de données
            account_id: Identifiant unique du compte
            bank_id: Identifiant de la banque associée
            account_type: Type de compte
            account_label: Libellé du compte

        Returns:
            Le compte créé ou None
        """
        if not account_id or not bank_id or not account_type or not account_label:
            return None

        # Nettoyer l'identifiant (pas d'espaces, minuscules)
        account_id = account_id.strip().lower().replace(" ", "_")

        # Vérifier si le compte existe déjà
        existing_account = db.query(Account).filter(Account.id == account_id).first()
        if existing_account:
            return None

        # Données pour la création
        data = {
            "id": account_id,
            "bank_id": bank_id,
            "type": account_type,
            "libelle": account_label
        }

        return self.create(db, data)

    @handle_exceptions
    def update_account(
            self, db: Session,
            account_id: str,
            bank_id: str,
            account_type: str,
            account_label: str
    ) -> Optional[Account]:
        """
        Met à jour un compte existant

        Args:
            db: Session de base de données
            account_id: Identifiant du compte à mettre à jour
            bank_id: Identifiant de la banque associée
            account_type: Type de compte
            account_label: Libellé du compte

        Returns:
            Le compte mis à jour ou None
        """
        # Données pour la mise à jour
        data = {
            "bank_id": bank_id,
            "type": account_type,
            "libelle": account_label
        }

        return self.update(db, account_id, data)

    @handle_exceptions
    def delete_account(self, db: Session, account_id: str) -> bool:
        """
        Supprime un compte s'il n'a pas d'actifs associés

        Args:
            db: Session de base de données
            account_id: Identifiant du compte à supprimer

        Returns:
            True si la suppression a réussi, False sinon
        """
        # Vérifier si des actifs sont liés à ce compte
        has_assets = db.query(Asset).filter(Asset.account_id == account_id).first() is not None
        if has_assets:
            return False

        # Supprimer le compte
        return self.delete(db, account_id)

    @handle_exceptions
    def get_accounts_dataframe(
            self, db: Session,
            user_id: str,
            bank_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Crée un DataFrame Pandas avec les comptes filtrés

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            bank_id: Filtre par ID de banque (optionnel)

        Returns:
            DataFrame Pandas des comptes filtrés
        """
        data = []

        # Obtenir les comptes et leurs informations associées
        query = db.query(Account, Bank).join(Bank).filter(Bank.owner_id == user_id)

        if bank_id:
            query = query.filter(Account.bank_id == bank_id)

        for account, bank in query.all():
            # Calculer la valeur totale des actifs dans ce compte
            total_value = db.query(Asset).filter(Asset.account_id == account.id).with_entities(
                func.sum(func.coalesce(Asset.value_eur, 0.0))
            ).scalar() or 0.0

            data.append([
                account.id,
                bank.nom,
                account.type,
                account.libelle,
                f"{total_value:.2f} €"
            ])

        return pd.DataFrame(data, columns=["ID", "Banque", "Type", "Libellé", "Valeur totale"])


    @handle_exceptions
    def get_accounts_with_total_values(
            self, db: Session,
            user_id: str,
            bank_id: Optional[str] = None
    ) -> List[Tuple[Account, Bank, float]]:
        """
        Récupère tous les comptes d'un utilisateur avec leur banque et valeur totale en une seule requête

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            bank_id: ID de la banque (optionnel)

        Returns:
            Liste de tuples (compte, banque, valeur_totale)
        """
        query = db.query(
            Account,
            Bank,
            func.coalesce(func.sum(Asset.value_eur), 0).label('total_value')
        ).join(
            Bank, Account.bank_id == Bank.id
        ).outerjoin(
            Asset, Account.id == Asset.account_id
        ).filter(
            Bank.owner_id == user_id
        )

        if bank_id:
            query = query.filter(Account.bank_id == bank_id)

        result = query.group_by(
            Account.id, Bank.id
        ).all()

        return result

# Créer une instance singleton du service
account_service = AccountService()