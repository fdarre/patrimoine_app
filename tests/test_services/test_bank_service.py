"""
Tests pour le service de gestion des banques
"""
from sqlalchemy.orm import Session

from database.models import Bank, User, Account
from services.bank_service import bank_service


class TestBankService:
    """Tests pour le service de gestion des banques"""

    def test_get_banks(self, db_session: Session, test_user: User, test_bank: Bank):
        """Test de récupération des banques"""
        # Cas 1: Toutes les banques d'un utilisateur
        banks = bank_service.get_banks(db_session, test_user.id)
        assert len(banks) >= 1
        assert any(bank.id == test_bank.id for bank in banks)

        # Cas 2: Aucune banque pour un utilisateur inexistant
        banks = bank_service.get_banks(db_session, "nonexistent-user-id")
        assert len(banks) == 0

    def test_get_bank(self, db_session: Session, test_bank: Bank):
        """Test de récupération d'une banque par ID"""
        # Cas 1: Banque existante
        bank = bank_service.get_bank(db_session, test_bank.id)
        assert bank is not None
        assert bank.id == test_bank.id
        assert bank.nom == test_bank.nom

        # Cas 2: Banque inexistante
        bank = bank_service.get_bank(db_session, "nonexistent-bank-id")
        assert bank is None

    def test_add_bank(self, db_session: Session, test_user: User):
        """Test d'ajout d'une banque"""
        # Cas 1: Ajout réussi
        bank = bank_service.add_bank(
            db_session,
            test_user.id,
            "new-bank-id",
            "Nouvelle Banque",
            "Notes pour la nouvelle banque"
        )
        assert bank is not None
        assert bank.id == "new-bank-id"
        assert bank.nom == "Nouvelle Banque"
        assert bank.notes == "Notes pour la nouvelle banque"

        # Vérifier que la banque est dans la base
        db_bank = db_session.query(Bank).filter(Bank.id == "new-bank-id").first()
        assert db_bank is not None
        assert db_bank.owner_id == test_user.id

        # Cas 2: ID de banque déjà existant
        bank = bank_service.add_bank(
            db_session,
            test_user.id,
            "new-bank-id",
            "Banque Dupliquée"
        )
        assert bank is None

        # Cas 3: ID ou nom vide
        bank = bank_service.add_bank(
            db_session,
            test_user.id,
            "",
            "Banque Sans ID"
        )
        assert bank is None

        bank = bank_service.add_bank(
            db_session,
            test_user.id,
            "valid-id",
            ""
        )
        assert bank is None

    def test_update_bank(self, db_session: Session, test_bank: Bank):
        """Test de mise à jour d'une banque"""
        # Cas 1: Mise à jour réussie
        updated_bank = bank_service.update_bank(
            db_session,
            test_bank.id,
            "Banque Mise à Jour",
            "Notes mises à jour"
        )
        assert updated_bank is not None
        assert updated_bank.nom == "Banque Mise à Jour"
        assert updated_bank.notes == "Notes mises à jour"

        # Vérifier que les modifications sont dans la base
        db_bank = db_session.query(Bank).filter(Bank.id == test_bank.id).first()
        assert db_bank is not None
        assert db_bank.nom == "Banque Mise à Jour"

        # Cas 2: Banque inexistante
        updated_bank = bank_service.update_bank(
            db_session,
            "nonexistent-bank-id",
            "Banque Inexistante"
        )
        assert updated_bank is None

    def test_delete_bank(self, db_session: Session, test_user: User):
        """Test de suppression d'une banque"""
        # Créer une banque pour le test
        bank = bank_service.add_bank(
            db_session,
            test_user.id,
            "bank-to-delete",
            "Banque à Supprimer"
        )
        assert bank is not None

        # Cas 1: Suppression réussie
        result = bank_service.delete_bank(db_session, "bank-to-delete")
        assert result is True

        # Vérifier que la banque a bien été supprimée
        db_bank = db_session.query(Bank).filter(Bank.id == "bank-to-delete").first()
        assert db_bank is None

        # Cas 2: Banque inexistante
        result = bank_service.delete_bank(db_session, "nonexistent-bank-id")
        assert result is False

        # Cas 3: Banque avec des comptes (ne doit pas être supprimée)
        # Créer une banque avec un compte
        bank = bank_service.add_bank(
            db_session,
            test_user.id,
            "bank-with-account",
            "Banque avec Compte"
        )
        assert bank is not None

        # Ajouter un compte à cette banque
        account = Account(
            id="test-account-for-delete",
            bank_id="bank-with-account",
            type="courant",
            libelle="Compte Test pour Suppression"
        )
        db_session.add(account)
        db_session.commit()

        # Tenter de supprimer la banque
        result = bank_service.delete_bank(db_session, "bank-with-account")
        assert result is False

        # Vérifier que la banque est toujours dans la base
        db_bank = db_session.query(Bank).filter(Bank.id == "bank-with-account").first()
        assert db_bank is not None

    def test_get_banks_dataframe(self, db_session: Session, test_user: User, test_bank: Bank):
        """Test de récupération des banques sous forme de DataFrame"""
        # Récupérer le DataFrame
        df = bank_service.get_banks_dataframe(db_session, test_user.id)

        # Vérifier que le DataFrame n'est pas vide
        assert not df.empty

        # Vérifier les colonnes
        assert "ID" in df.columns
        assert "Nom" in df.columns
        assert "Nb comptes" in df.columns

        # Vérifier que la banque de test est dans le DataFrame
        assert test_bank.id in df["ID"].values
        assert test_bank.nom in df["Nom"].values

    def test_get_banks_with_account_counts(self, db_session: Session, test_user: User, test_bank: Bank):
        """Test de récupération des banques avec le nombre de comptes"""
        # Récupérer les banques avec le nombre de comptes
        banks_with_counts = bank_service.get_banks_with_account_counts(db_session, test_user.id)

        # Vérifier que la liste n'est pas vide
        assert len(banks_with_counts) >= 1

        # Vérifier que la banque de test est dans la liste
        bank_found = False
        for bank, count in banks_with_counts:
            if bank.id == test_bank.id:
                bank_found = True
                # Le compte de test devrait être associé à cette banque
                assert count >= 1
                break

        assert bank_found
