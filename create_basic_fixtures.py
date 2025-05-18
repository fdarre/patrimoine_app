#!/usr/bin/env python
"""
Script de création de fixtures pour l'utilisateur 'fredfred' avec banques et comptes
"""
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from database.db_config import get_db, engine, Base
from database.models import User, Bank, Account
from utils.password import hash_password


def create_user_fixtures():
    """Crée un utilisateur avec banques et comptes, sans actifs"""

    # Obtenir une session de base de données
    db = next(get_db())

    try:
        print("Création des fixtures pour l'utilisateur fredfred...")

        # 1. Créer l'utilisateur 'fredfred' ou le récupérer s'il existe déjà
        user = db.query(User).filter(User.username == "fredfred").first()

        if user:
            print(f"Utilisateur 'fredfred' déjà existant: {user.id}")
        else:
            # Créer le nouvel utilisateur
            user = User(
                id=str(uuid.uuid4()),
                username="fredfred",
                email="fred@example.com",
                password_hash=hash_password("FredFred"),
                is_active=True,
                created_at=datetime.now()
            )

            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Utilisateur créé: fredfred (ID: {user.id})")

        # 2. Créer les trois banques demandées
        banks = {
            "bourso": create_bank(db, user.id, "bourso", "Boursorama Banque",
                                  "Banque en ligne du groupe Société Générale"),
            "fortuneo": create_bank(db, user.id, "fortuneo", "Fortuneo", "Banque en ligne du Crédit Mutuel Arkéa"),
            "cmutuel": create_bank(db, user.id, "cmutuel", "Crédit Mutuel", "Banque traditionnelle avec agences")
        }

        # 3. Créer les comptes demandés
        accounts = {
            "pea_bourso": create_account(db, "pea_bourso", banks["bourso"].id, "pea", "PEA Boursorama"),
            "titre_fortuneo": create_account(db, "titre_fortuneo", banks["fortuneo"].id, "titre",
                                             "Compte-Titre Fortuneo"),
            "courant_bourso": create_account(db, "courant_bourso", banks["bourso"].id, "courant",
                                             "Compte Courant Boursorama"),
            "courant_cmutuel": create_account(db, "courant_cmutuel", banks["cmutuel"].id, "courant",
                                              "Compte Courant Crédit Mutuel")
        }

        print("\nFIXTURES CRÉÉES AVEC SUCCÈS")
        print("---------------------------")
        print(f"Utilisateur: fredfred (mot de passe: FredFred)")
        print("\nBanques:")
        for bank_id, bank in banks.items():
            print(f"- {bank.nom} (ID: {bank_id})")

        print("\nComptes:")
        for account_id, account in accounts.items():
            bank = next((b for b_id, b in banks.items() if b.id == account.bank_id), None)
            print(f"- {account.libelle} (ID: {account_id}) chez {bank.nom if bank else 'N/A'}")

        print("\nVous pouvez maintenant vous connecter et ajouter vos actifs.")

    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la création des fixtures: {str(e)}")
    finally:
        db.close()


def create_bank(db: Session, user_id: str, bank_id: str, name: str, notes: str = "") -> Bank:
    """Crée une banque ou récupère une banque existante"""

    # Vérifier si la banque existe déjà
    bank = db.query(Bank).filter(Bank.id == bank_id, Bank.owner_id == user_id).first()

    if bank:
        print(f"Banque '{name}' déjà existante")
        return bank

    # Créer la nouvelle banque
    bank = Bank(
        id=bank_id,
        owner_id=user_id,
        nom=name,
        notes=notes
    )

    db.add(bank)
    db.commit()
    db.refresh(bank)

    print(f"Banque créée: {name}")
    return bank


def create_account(db: Session, account_id: str, bank_id: str, account_type: str, label: str) -> Account:
    """Crée un compte bancaire ou récupère un compte existant"""

    # Vérifier si le compte existe déjà
    account = db.query(Account).filter(Account.id == account_id).first()

    if account:
        print(f"Compte '{label}' déjà existant")
        return account

    # Créer le nouveau compte
    account = Account(
        id=account_id,
        bank_id=bank_id,
        type=account_type,
        libelle=label
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    print(f"Compte créé: {label}")
    return account


if __name__ == "__main__":
    # S'assurer que les tables existent
    Base.metadata.create_all(bind=engine)
    create_user_fixtures()