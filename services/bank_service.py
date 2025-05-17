"""
Service de gestion des banques avec SQLAlchemy
"""
from typing import List, Optional
from sqlalchemy.orm import Session
import pandas as pd

from database.models import Bank, Account, Asset, User
from services.base_service import BaseService
from utils.decorators import handle_exceptions
from utils.logger import get_logger

logger = get_logger(__name__)

class BankService(BaseService[Bank]):
    """Service pour la gestion des banques avec SQLAlchemy"""

    def __init__(self):
        super().__init__(Bank)

    @handle_exceptions
    def get_banks(self, db: Session, user_id: str) -> List[Bank]:
        """
        Récupère toutes les banques d'un utilisateur

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur

        Returns:
            Liste des banques
        """
        return self.get_all(db, owner_id=user_id)

    @handle_exceptions
    def get_bank(self, db: Session, bank_id: str) -> Optional[Bank]:
        """
        Récupère une banque par son ID

        Args:
            db: Session de base de données
            bank_id: ID de la banque

        Returns:
            La banque ou None
        """
        return self.get_by_id(db, bank_id)

    @handle_exceptions
    def add_bank(self, db: Session, user_id: str, bank_id: str, nom: str, notes: str = "") -> Optional[Bank]:
        """
        Ajoute une nouvelle banque

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur propriétaire
            bank_id: Identifiant unique de la banque
            nom: Nom de la banque
            notes: Notes sur la banque

        Returns:
            La banque créée ou None
        """
        if not bank_id or not nom:
            return None

        # Nettoyer l'identifiant (pas d'espaces, minuscules)
        bank_id = bank_id.strip().lower().replace(" ", "_")

        # Vérifier si la banque existe déjà
        existing_bank = db.query(Bank).filter(Bank.id == bank_id).first()
        if existing_bank:
            return None

        # Créer la nouvelle banque
        data = {
            "id": bank_id,
            "owner_id": user_id,
            "nom": nom,
            "notes": notes or ""
        }

        return self.create(db, data)

    @handle_exceptions
    def update_bank(self, db: Session, bank_id: str, nom: str, notes: str = "") -> Optional[Bank]:
        """
        Met à jour une banque existante

        Args:
            db: Session de base de données
            bank_id: Identifiant de la banque à mettre à jour
            nom: Nouveau nom
            notes: Nouvelles notes

        Returns:
            La banque mise à jour ou None
        """
        # Données pour la mise à jour
        data = {
            "nom": nom,
            "notes": notes
        }

        return self.update(db, bank_id, data)

    @handle_exceptions
    def delete_bank(self, db: Session, bank_id: str) -> bool:
        """
        Supprime une banque si elle n'a pas de comptes associés

        Args:
            db: Session de base de données
            bank_id: Identifiant de la banque à supprimer

        Returns:
            True si la suppression a réussi, False sinon
        """
        # Vérifier si des comptes sont liés à cette banque
        has_accounts = db.query(Account).filter(Account.bank_id == bank_id).first() is not None
        if has_accounts:
            return False

        # Supprimer la banque
        return self.delete(db, bank_id)

    @handle_exceptions
    def get_banks_dataframe(self, db: Session, user_id: str) -> pd.DataFrame:
        """
        Crée un DataFrame Pandas avec les banques d'un utilisateur

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur

        Returns:
            DataFrame Pandas des banques
        """
        data = []

        # Récupérer les banques de l'utilisateur
        banks = self.get_banks(db, user_id)

        for bank in banks:
            # Compter les comptes associés à cette banque
            account_count = db.query(Account).filter(Account.bank_id == bank.id).count()
            data.append([bank.id, bank.nom, account_count])

        return pd.DataFrame(data, columns=["ID", "Nom", "Nb comptes"])

    @handle_exceptions
    def get_banks_with_account_counts(self, db: Session, user_id: str) -> List[Tuple[Bank, int]]:
        """
        Récupère toutes les banques d'un utilisateur avec le nombre de comptes pour chacune

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur

        Returns:
            Liste de tuples (banque, nombre de comptes)
        """
        result = db.query(
            Bank,
            func.count(Account.id).label('account_count')
        ).outerjoin(
            Account, Bank.id == Account.bank_id
        ).filter(
            Bank.owner_id == user_id
        ).group_by(
            Bank.id
        ).all()

        return result

# Créer une instance singleton du service
bank_service = BankService()