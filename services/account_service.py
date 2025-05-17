from sqlalchemy import func
"""
Service de gestion des comptes avec SQLAlchemy
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import pandas as pd

from database.models import Account, Asset, Bank

class AccountService:
    """Service pour la gestion des comptes avec SQLAlchemy"""

    @staticmethod
    def get_accounts(db: Session, user_id: str, bank_id: Optional[str] = None) -> List[Account]:
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

    @staticmethod
    def get_account(db: Session, account_id: str) -> Optional[Account]:
        """
        Récupère un compte par son ID

        Args:
            db: Session de base de données
            account_id: ID du compte

        Returns:
            Le compte ou None
        """
        return db.query(Account).filter(Account.id == account_id).first()

    @staticmethod
    def add_account(
            db: Session,
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

        # Créer le nouveau compte
        new_account = Account(
            id=account_id,
            bank_id=bank_id,
            type=account_type,
            libelle=account_label
        )

        # Ajouter et valider
        db.add(new_account)
        db.commit()
        db.refresh(new_account)

        return new_account

    @staticmethod
    def update_account(
            db: Session,
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
        # Récupérer le compte
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return None

        # Mettre à jour les champs
        account.bank_id = bank_id
        account.type = account_type
        account.libelle = account_label

        # Valider les modifications
        db.commit()
        db.refresh(account)

        return account

    @staticmethod
    def delete_account(db: Session, account_id: str) -> bool:
        """
        Supprime un compte s'il n'a pas d'actifs associés

        Args:
            db: Session de base de données
            account_id: Identifiant du compte à supprimer

        Returns:
            True si la suppression a réussi, False sinon
        """
        # Récupérer le compte
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return False

        # Vérifier si des actifs sont liés à ce compte
        has_assets = db.query(Asset).filter(Asset.account_id == account_id).first() is not None
        if has_assets:
            return False

        # Supprimer le compte
        db.delete(account)
        db.commit()

        return True

    @staticmethod
    def get_accounts_dataframe(
            db: Session,
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
            # MODIFICATION: Utiliser value_eur au lieu de valeur_actuelle
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