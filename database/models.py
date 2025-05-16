"""
Modèles SQLAlchemy pour la base de données avec chiffrement au niveau des champs
"""
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Text
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

class Bank(Base):
    __tablename__ = "banks"

    id = Column(String, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("users.id"))
    nom = Column(EncryptedString)    # Chiffré
    notes = Column(EncryptedString, nullable=True)  # Chiffré

class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True, index=True)
    bank_id = Column(String, ForeignKey("banks.id"))
    type = Column(String)  # Non sensible, pas besoin de chiffrer
    libelle = Column(EncryptedString)  # Chiffré

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, ForeignKey("users.id"))
    account_id = Column(String, ForeignKey("accounts.id"))
    nom = Column(EncryptedString)  # Chiffré
    type_produit = Column(String)  # Non sensible, pas besoin de chiffrer
    categorie = Column(String)  # Non sensible, pas besoin de chiffrer
    allocation = Column(EncryptedJSON)  # Chiffré
    geo_allocation = Column(EncryptedJSON)  # Chiffré
    valeur_actuelle = Column(Float)  # Sensible mais besoin de faire des calculs
    prix_de_revient = Column(Float)  # Sensible mais besoin de faire des calculs
    devise = Column(String, default="EUR")  # Non sensible
    date_maj = Column(String)  # Non sensible
    notes = Column(EncryptedString, nullable=True)  # Chiffré
    todo = Column(EncryptedString, nullable=True)  # Chiffré
    composants = Column(EncryptedJSON, nullable=True)  # Chiffré
    isin = Column(String, nullable=True)  # Code ISIN
    ounces = Column(Float, nullable=True)  # Nombre d'onces pour les métaux précieux
    exchange_rate = Column(Float, default=1.0)  # Taux de change par rapport à l'EUR
    value_eur = Column(Float, nullable=True)  # Valeur en EUR
    last_price_sync = Column(DateTime, nullable=True)  # Date de dernière synchronisation du prix
    last_rate_sync = Column(DateTime, nullable=True)  # Date de dernière synchronisation du taux de change
    sync_error = Column(String, nullable=True)  # Message d'erreur de synchronisation

class HistoryPoint(Base):
    __tablename__ = "history"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    date = Column(String)  # Non sensible
    assets = Column(EncryptedJSON)  # Chiffré
    total = Column(Float)  # Sensible mais besoin de faire des calculs