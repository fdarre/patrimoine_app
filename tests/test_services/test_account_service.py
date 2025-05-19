"""
Tests pour le service de gestion des comptes
"""
from sqlalchemy.orm import Session

from database.models import Account, Bank, User, Asset
from services.account_service import account_service


class TestAccountService:
    """Tests pour le service de gestion des comptes"""

    def test_get_accounts(self, db_session: Session, test_user: User, test_bank: Bank, test_account: Account):
        """Test de récupération des comptes"""
        # Cas 1: Tous les comptes d'un utilisateur
        accounts = account_service.get_accounts(db_session, test_user.id)
        assert len(accounts) >= 1
        assert any(account.id == test_account.id for account in accounts)

        # Cas 2: Filtrage par banque
        accounts = account_service.get_accounts(db_session, test_user.id, test_bank.id)
        assert len(accounts) >= 1
        assert all(account.bank_id == test_bank.id for account in accounts)

        # Cas 3: Aucun compte pour un utilisateur inexistant
        accounts = account_service.get_accounts(db_session, "nonexistent-user-id")
        assert len(accounts) == 0

    def test_get_account(self, db_session: Session, test_account: Account):
        """Test de récupération d'un compte par ID"""
        # Cas 1: Compte existant
        account = account_service.get_account(db_session, test_account.id)
        assert account is not None
        assert account.id == test_account.id
        assert account.libelle == test_account.libelle

        # Cas 2: Compte inexistant
        account = account_service.get_account(db_session, "nonexistent-account-id")
        assert account is None

    def test_add_account(self, db_session: Session, test_bank: Bank):
        """Test d'ajout d'un compte"""
        # Cas 1: Ajout réussi
        account = account_service.add_account(
            db_session,
            "new-account-id",
            test_bank.id,
            "livret",
            "Nouveau Compte"
        )
        assert account is not None
        assert account.id == "new-account-id"
        assert account.bank_id == test_bank.id
        assert account.type == "livret"
        assert account.libelle == "Nouveau Compte"

        # Vérifier que le compte est dans la base
        db_account = db_session.query(Account).filter(Account.id == "new-account-id").first()
        assert db_account is not None

        # Cas 2: ID de compte déjà existant
        account = account_service.add_account(
            db_session,
            "new-account-id",
            test_bank.id,
            "courant",
            "Compte Dupliqué"
        )
        assert account is None

        # Cas 3: Paramètres invalides
        account = account_service.add_account(
            db_session,
            "",
            test_bank.id,
            "courant",
            "Compte Sans ID"
        )
        assert account is None

        account = account_service.add_account(
            db_session,
            "valid-id",
            "",
            "courant",
            "Compte Sans Banque"
        )
        assert account is None

    def test_update_account(self, db_session: Session, test_bank: Bank, test_account: Account):
        """Test de mise à jour d'un compte"""
        # Cas 1: Mise à jour réussie
        updated_account = account_service.update_account(
            db_session,
            test_account.id,
            test_bank.id,
            "pea",
            "Compte Mis à Jour"
        )
        assert updated_account is not None
        assert updated_account.type == "pea"
        assert updated_account.libelle == "Compte Mis à Jour"

        # Vérifier que les modifications sont dans la base
        db_account = db_session.query(Account).filter(Account.id == test_account.id).first()
        assert db_account is not None
        assert db_account.type == "pea"

        # Cas 2: Compte inexistant
        updated_account = account_service.update_account(
            db_session,
            "nonexistent-account-id",
            test_bank.id,
            "courant",
            "Compte Inexistant"
        )
        assert updated_account is None

    def test_delete_account(self, db_session: Session, test_bank: Bank):
        """Test de suppression d'un compte"""
        # Créer un compte pour le test
        account = account_service.add_account(
            db_session,
            "account-to-delete",
            test_bank.id,
            "courant",
            "Compte à Supprimer"
        )
        assert account is not None

        # Cas 1: Suppression réussie
        result = account_service.delete_account(db_session, "account-to-delete")
        assert result is True

        # Vérifier que le compte a bien été supprimé
        db_account = db_session.query(Account).filter(Account.id == "account-to-delete").first()
        assert db_account is None

        # Cas 2: Compte inexistant
        result = account_service.delete_account(db_session, "nonexistent-account-id")
        assert result is False

        # Cas 3: Compte avec des actifs (ne doit pas être supprimé)
        # Créer un compte avec un actif
        account = account_service.add_account(
            db_session,
            "account-with-asset",
            test_bank.id,
            "titre",
            "Compte avec Actif"
        )
        assert account is not None

        # Ajouter un actif à ce compte
        asset = Asset(
            id="test-asset-for-delete",
            owner_id=test_bank.owner_id,
            account_id="account-with-asset",
            nom="Actif Test pour Suppression",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 100},
            geo_allocation={},
            valeur_actuelle=1000.0,
            prix_de_revient=900.0,
            devise="EUR",
            date_maj="2025-05-19"
        )
        db_session.add(asset)
        db_session.commit()

        # Tenter de supprimer le compte
        result = account_service.delete_account(db_session, "account-with-asset")
        assert result is False

        # Vérifier que le compte est toujours dans la base
        db_account = db_session.query(Account).filter(Account.id == "account-with-asset").first()
        assert db_account is not None

    def test_get_accounts_dataframe(self, db_session: Session, test_user: User, test_bank: Bank, test_account: Account):
        """Test de récupération des comptes sous forme de DataFrame"""
        # Récupérer le DataFrame
        df = account_service.get_accounts_dataframe(db_session, test_user.id)

        # Vérifier que le DataFrame n'est pas vide
        assert not df.empty

        # Vérifier les colonnes
        assert "ID" in df.columns
        assert "Banque" in df.columns
        assert "Type" in df.columns
        assert "Libellé" in df.columns
        assert "Valeur totale" in df.columns

        # Vérifier que le compte de test est dans le DataFrame
        assert test_account.id in df["ID"].values

        # Cas 2: Filtrage par banque
        df = account_service.get_accounts_dataframe(db_session, test_user.id, test_bank.id)

        # Vérifier que le DataFrame n'est pas vide
        assert not df.empty

        # Vérifier que tous les comptes appartiennent à la banque de test
        assert all(bank == test_bank.nom for bank in df["Banque"])

    def test_get_accounts_with_total_values(self, db_session: Session, test_user: User, test_bank: Bank,
                                            test_account: Account):
        """Test de récupération des comptes avec leurs valeurs totales"""
        # Récupérer les comptes avec leurs valeurs
        accounts_with_values = account_service.get_accounts_with_total_values(db_session, test_user.id)

        # Vérifier que la liste n'est pas vide
        assert len(accounts_with_values) >= 1

        # Vérifier que le compte de test est dans la liste
        account_found = False
        for account, bank, value in accounts_with_values:
            if account.id == test_account.id:
                account_found = True
                assert bank.id == test_bank.id
                # La valeur peut être 0 ou plus
                assert value >= 0
                break

        assert account_found

        # Cas 2: Filtrage par banque
        accounts_with_values = account_service.get_accounts_with_total_values(db_session, test_user.id, test_bank.id)

        # Vérifier que la liste n'est pas vide
        assert len(accounts_with_values) >= 1

        # Vérifier que tous les comptes appartiennent à la banque de test
        assert all(bank.id == test_bank.id for _, bank, _ in accounts_with_values)
