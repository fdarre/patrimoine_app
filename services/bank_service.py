"""
Service de gestion des banques avec SQLAlchemy
"""
from typing import List, Optional
from sqlalchemy.orm import Session
import pandas as pd

from database.models import Bank, Account, Asset, User

class BankService:
    """Service pour la gestion des banques avec SQLAlchemy"""

    @staticmethod
    def get_banks(db: Session, user_id: str) -> List[Bank]:
        """
        Récupère toutes les banques d'un utilisateur

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur

        Returns:
            Liste des banques
        """
        return db.query(Bank).filter(Bank.owner_id == user_id).all()

    @staticmethod
    def get_bank(db: Session, bank_id: str) -> Optional[Bank]:
        """
        Récupère une banque par son ID

        Args:
            db: Session de base de données
            bank_id: ID de la banque

        Returns:
            La banque ou None
        """
        return db.query(Bank).filter(Bank.id == bank_id).first()

    @staticmethod
    def add_bank(db: Session, user_id: str, bank_id: str, nom: str, notes: str = "") -> Optional[Bank]:
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
        new_bank = Bank(
            id=bank_id,
            owner_id=user_id,
            nom=nom,
            notes=notes or ""
        )

        # Ajouter et valider
        db.add(new_bank)
        db.commit()
        db.refresh(new_bank)

        return new_bank

    @staticmethod
    def update_bank(db: Session, bank_id: str, nom: str, notes: str = "") -> Optional[Bank]:
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
        # Récupérer la banque
        bank = db.query(Bank).filter(Bank.id == bank_id).first()
        if not bank:
            return None

        # Mettre à jour les champs
        bank.nom = nom
        bank.notes = notes

        # Valider les modifications
        db.commit()
        db.refresh(bank)

        return bank

    @staticmethod
    def delete_bank(db: Session, bank_id: str) -> bool:
        """
        Supprime une banque si elle n'a pas de comptes associés

        Args:
            db: Session de base de données
            bank_id: Identifiant de la banque à supprimer

        Returns:
            True si la suppression a réussi, False sinon
        """
        # Récupérer la banque
        bank = db.query(Bank).filter(Bank.id == bank_id).first()
        if not bank:
            return False

        # Vérifier si des comptes sont liés à cette banque
        has_accounts = db.query(Account).filter(Account.bank_id == bank_id).first() is not None
        if has_accounts:
            return False

        # Supprimer la banque
        db.delete(bank)
        db.commit()

        return True

    @staticmethod
    def get_banks_dataframe(db: Session, user_id: str) -> pd.DataFrame:
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
        banks = db.query(Bank).filter(Bank.owner_id == user_id).all()

        for bank in banks:
            # Compter les comptes associés à cette banque
            account_count = db.query(Account).filter(Account.bank_id == bank.id).count()
            data.append([bank.id, bank.nom, account_count])

        return pd.DataFrame(data, columns=["ID", "Nom", "Nb comptes"])