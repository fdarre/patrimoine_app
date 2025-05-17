"""
Modèles SQLAlchemy pour la base de données avec chiffrement au niveau des champs
"""
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Text, Index
from sqlalchemy.ext.mutable import MutableDict, MutableList
import datetime
import uuid

from database.db_config import Base
from utils.crypto import EncryptedJSON, EncryptedString, EncryptedDict, EncryptedList

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(EncryptedString)  # Chiffré
    password_hash = Column(String)   # Déjà haché, pas besoin de chiffrer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now)

    # Indices optimisés
    __table_args__ = (
        Index('idx_users_username', 'username'),
    )

class Bank(Base):
    __tablename__ = "banks"

    id = Column(String, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("users.id"), index=True)  # Index ajouté
    nom = Column(EncryptedString)    # Chiffré
    notes = Column(EncryptedString, nullable=True)  # Chiffré

    # Indices optimisés
    __table_args__ = (
        Index('idx_banks_owner', 'owner_id'),
    )

class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True, index=True)
    bank_id = Column(String, ForeignKey("banks.id"), index=True)  # Index ajouté
    type = Column(String, index=True)  # Index ajouté pour le filtrage par type
    libelle = Column(EncryptedString)  # Chiffré

    # Indices optimisés
    __table_args__ = (
        Index('idx_accounts_bank', 'bank_id'),
        Index('idx_accounts_type', 'type'),
    )

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, ForeignKey("users.id"), index=True)  # Index ajouté
    account_id = Column(String, ForeignKey("accounts.id"), index=True)  # Index ajouté
    nom = Column(EncryptedString)  # Chiffré
    type_produit = Column(String, index=True)  # Index ajouté pour le filtrage
    categorie = Column(String, index=True)  # Index ajouté pour le filtrage
    allocation = Column(EncryptedJSON)  # Chiffré - dict {categorie: pourcentage}
    geo_allocation = Column(EncryptedJSON)  # Chiffré - dict {categorie: {zone: pourcentage}}
    valeur_actuelle = Column(Float)  # Sensible mais besoin de faire des calculs
    prix_de_revient = Column(Float)  # Sensible mais besoin de faire des calculs
    devise = Column(String, default="EUR", index=True)  # Index ajouté pour le filtrage par devise
    date_maj = Column(String)  # Non sensible
    notes = Column(EncryptedString, nullable=True)  # Chiffré
    todo = Column(EncryptedString, nullable=True)  # Chiffré
    isin = Column(String, nullable=True, index=True)  # Code ISIN, index ajouté
    ounces = Column(Float, nullable=True)  # Nombre d'onces pour les métaux précieux
    exchange_rate = Column(Float, default=1.0)  # Taux de change par rapport à l'EUR
    value_eur = Column(Float, nullable=True)  # Valeur en EUR
    last_price_sync = Column(DateTime, nullable=True)  # Date de dernière synchronisation du prix
    last_rate_sync = Column(DateTime, nullable=True)  # Date de dernière synchronisation du taux de change
    sync_error = Column(String, nullable=True)  # Message d'erreur de synchronisation

    # for asset templates
    template_id = Column(String, ForeignKey("assets.id"), nullable=True, index=True)
    is_template = Column(Boolean, default=False)
    template_name = Column(String, nullable=True)
    sync_allocations = Column(Boolean, default=True)  # Si True, synchroniser les allocations depuis le template

    # Indices composites pour les requêtes fréquentes
    __table_args__ = (
        Index('idx_assets_owner_account', 'owner_id', 'account_id'),
        Index('idx_assets_type_owner', 'type_produit', 'owner_id'),
        Index('idx_assets_value_eur', 'value_eur'),  # Pour les agrégations
    )

class HistoryPoint(Base):
    __tablename__ = "history"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    date = Column(String, index=True)  # Index ajouté pour les recherches par date
    assets = Column(EncryptedJSON)  # Chiffré
    total = Column(Float)  # Sensible mais besoin de faire des calculs

    # Indices optimisés
    __table_args__ = (
        Index('idx_history_date', 'date'),
    )