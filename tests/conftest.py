"""
Fixtures partagées pour les tests unitaires
"""
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Redéfinir les constantes de config pour les tests
os.environ["TEST_MODE"] = "True"

# Import après la définition des variables d'environnement
from database.models import Base, User, Bank, Account, Asset
from utils.password import hash_password

# Mock pour Streamlit
try:
    import streamlit as st

    # Remplacer st.secrets par un dictionnaire simple
    st.secrets = {"env": "test"}
except ImportError:
    pass


@pytest.fixture(scope="session")
def test_db_path():
    """
    Crée un fichier temporaire pour la base de données de test
    """
    fd, path = tempfile.mkstemp(suffix=".db")
    yield path
    os.close(fd)
    os.unlink(path)


@pytest.fixture(scope="session")
def test_engine(test_db_path):
    """
    Crée un moteur SQLAlchemy pour les tests
    """
    engine = create_engine(f"sqlite:///{test_db_path}", connect_args={"check_same_thread": False})
    # Créer les tables
    Base.metadata.create_all(engine)
    yield engine
    # Nettoyer après les tests
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Crée une session de base de données pour les tests
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def test_user(db_session) -> User:
    """
    Crée un utilisateur de test
    """
    # Générer un username unique à chaque test pour éviter les violations de contrainte d'unicité
    unique_suffix = str(uuid.uuid4())[:8]
    username = f"testuser_{unique_suffix}"
    email = f"test_{unique_suffix}@example.com"

    user = User(
        id=f"test-user-id-{unique_suffix}",
        username=username,
        email=email,
        password_hash=hash_password("testpassword"),
        is_active=True,
        created_at=datetime.now()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_bank(db_session, test_user) -> Bank:
    """
    Crée une banque de test
    """
    # Générer un ID unique pour la banque
    unique_suffix = str(uuid.uuid4())[:8]
    bank_id = f"test-bank-id-{unique_suffix}"

    bank = Bank(
        id=bank_id,
        owner_id=test_user.id,
        nom="Banque Test",
        notes="Notes de test"
    )
    db_session.add(bank)
    db_session.commit()
    db_session.refresh(bank)
    return bank


@pytest.fixture(scope="function")
def test_account(db_session, test_bank) -> Account:
    """
    Crée un compte de test
    """
    # Générer un ID unique pour le compte
    unique_suffix = str(uuid.uuid4())[:8]
    account_id = f"test-account-id-{unique_suffix}"

    account = Account(
        id=account_id,
        bank_id=test_bank.id,
        type="courant",
        libelle="Compte Test"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(scope="function")
def test_asset(db_session, test_user, test_account) -> Asset:
    """
    Crée un actif de test
    """
    # Générer un ID unique pour l'actif
    unique_suffix = str(uuid.uuid4())[:8]
    asset_id = f"test-asset-id-{unique_suffix}"

    asset = Asset(
        id=asset_id,
        owner_id=test_user.id,
        account_id=test_account.id,
        nom="Actif Test",
        type_produit="etf",
        categorie="actions",
        allocation={"actions": 100, "obligations": 0, "immobilier": 0, "crypto": 0, "metaux": 0, "cash": 0},
        geo_allocation={"actions": {"amerique_nord": 100}},
        valeur_actuelle=1000.0,
        prix_de_revient=900.0,
        devise="EUR",
        date_maj=datetime.now().strftime("%Y-%m-%d"),
        notes="Notes de test",
        todo="",
        isin="FR0000000000",
        value_eur=1000.0
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


@pytest.fixture
def mock_encryption_key(monkeypatch):
    """
    Mock pour la clé de chiffrement
    """
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()

    def mock_get_encryption_key():
        return key

    monkeypatch.setattr('database.db_config.get_encryption_key', mock_get_encryption_key)
    return key


@pytest.fixture
def mock_cipher(mock_encryption_key, monkeypatch):
    """
    Mock pour le chiffrement
    """
    from cryptography.fernet import Fernet
    cipher = Fernet(mock_encryption_key)
    monkeypatch.setattr('database.db_config.cipher', cipher)
    return cipher


@pytest.fixture
def test_dir():
    """
    Crée un répertoire temporaire pour les tests
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)