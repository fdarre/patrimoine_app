#!/usr/bin/env python3
"""
Script de génération de fixtures pour l'application de gestion patrimoniale.
Crée 5 banques, 10 comptes et 500 actifs pour l'utilisateur "fredo".
"""
import random
import uuid
from datetime import datetime
from typing import Dict, List

try:
    import faker
    from faker.providers import bank, company, currency
except ImportError:
    print("Le package faker n'est pas installé. Installation avec pip install faker")
    import subprocess

    subprocess.check_call(["pip", "install", "faker"])
    import faker
    from faker.providers import bank, company, currency

from sqlalchemy.orm import Session

# Importer les modules de l'application
from config.app_config import ACCOUNT_TYPES, ASSET_CATEGORIES, GEO_ZONES
from database.db_config import get_db, engine, Base
from database.models import User, Bank, Account, Asset
from services.bank_service import bank_service
from services.account_service import account_service
from services.asset_service import asset_service
from services.data_service import DataService
from utils.password import hash_password

# Initialiser Faker pour générer des données réalistes
fake = faker.Faker('fr_FR')
fake.add_provider(bank)
fake.add_provider(company)
fake.add_provider(currency)


def create_user(db: Session, username: str, password: str) -> User:
    """Crée un utilisateur avec le nom et mot de passe spécifiés"""
    # Vérifier si l'utilisateur existe déjà
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        print(f"L'utilisateur {username} existe déjà.")
        return existing_user

    # Hacher le mot de passe
    password_hash = hash_password(password)

    # Créer le nouvel utilisateur
    new_user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=f"{username}@example.com",
        password_hash=password_hash,
        is_active=True,
        created_at=datetime.now()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print(f"Utilisateur {username} créé avec succès.")
    return new_user


def create_banks(db: Session, user_id: str, count: int = 5) -> List[Bank]:
    """Crée le nombre spécifié de banques pour l'utilisateur"""
    banks = []

    bank_templates = [
        {
            "id": "boursorama",
            "nom": "Boursorama Banque",
            "notes": "Banque en ligne sans frais"
        },
        {
            "id": "bnp",
            "nom": "BNP Paribas",
            "notes": "Grande banque traditionnelle"
        },
        {
            "id": "societe_generale",
            "nom": "Société Générale",
            "notes": "Banque française historique"
        },
        {
            "id": "ing",
            "nom": "ING Direct",
            "notes": "Banque en ligne néerlandaise"
        },
        {
            "id": "fortuneo",
            "nom": "Fortuneo",
            "notes": "Banque en ligne du groupe Crédit Mutuel Arkéa"
        },
        {
            "id": "credit_agricole",
            "nom": "Crédit Agricole",
            "notes": "Réseau de banques coopératives et mutualistes"
        },
        {
            "id": "credit_mutuel",
            "nom": "Crédit Mutuel",
            "notes": "Banque mutualiste régionale"
        },
        {
            "id": "la_banque_postale",
            "nom": "La Banque Postale",
            "notes": "Filiale bancaire du groupe La Poste"
        }
    ]

    # Sélectionner aléatoirement count banques parmi les templates
    selected_banks = random.sample(bank_templates, min(count, len(bank_templates)))

    for bank_data in selected_banks:
        bank = bank_service.add_bank(
            db=db,
            user_id=user_id,
            bank_id=bank_data["id"],
            nom=bank_data["nom"],
            notes=bank_data["notes"]
        )
        if bank:
            banks.append(bank)
            print(f"Banque {bank_data['nom']} ajoutée.")

    return banks


def create_accounts(db: Session, banks: List[Bank], count: int = 10) -> List[Account]:
    """Crée le nombre spécifié de comptes répartis entre les banques"""
    accounts = []

    # Répartir équitablement le nombre de comptes par banque
    accounts_per_bank = {bank.id: count // len(banks) for bank in banks}

    # Ajouter les comptes restants aux premières banques
    remaining = count % len(banks)
    for i in range(remaining):
        accounts_per_bank[banks[i].id] += 1

    account_types_by_bank = {
        "boursorama": ["courant", "livret", "pea", "titre", "assurance_vie"],
        "bnp": ["courant", "livret", "pea", "assurance_vie"],
        "societe_generale": ["courant", "livret", "titre", "assurance_vie"],
        "ing": ["courant", "livret", "assurance_vie"],
        "fortuneo": ["courant", "livret", "pea", "titre"],
        "credit_agricole": ["courant", "livret", "assurance_vie"],
        "credit_mutuel": ["courant", "livret", "titre", "assurance_vie"],
        "la_banque_postale": ["courant", "livret", "pea"]
    }

    account_type_labels = {
        "courant": ["Compte courant", "Compte chèque", "Compte principal"],
        "livret": ["Livret A", "LDDS", "LEP", "Livret Jeune"],
        "pea": ["PEA", "PEA-PME"],
        "titre": ["Compte titre", "CTO"],
        "assurance_vie": ["Assurance Vie", "Contrat AV", "Vie Plus", "Spirica"],
        "autre": ["Compte spécial", "Compte projet", "Compte divers"]
    }

    for bank in banks:
        bank_account_types = account_types_by_bank.get(bank.id, ACCOUNT_TYPES)

        for i in range(accounts_per_bank[bank.id]):
            # Sélectionner un type de compte disponible pour cette banque
            account_type = random.choice(bank_account_types)

            # Générer un identifiant unique pour le compte
            account_id = f"{account_type}_{bank.id}_{i}"

            # Sélectionner un libellé pour ce type de compte
            account_label = random.choice(account_type_labels[account_type])

            # Si plusieurs comptes du même type, ajouter un numéro
            if accounts_per_bank[bank.id] > 1:
                account_label = f"{account_label} {i + 1}"

            # Créer le compte
            account = account_service.add_account(
                db=db,
                account_id=account_id,
                bank_id=bank.id,
                account_type=account_type,
                account_label=account_label
            )

            if account:
                accounts.append(account)
                print(f"Compte {account_label} ajouté pour la banque {bank.id}.")

    return accounts


def generate_allocation() -> Dict[str, float]:
    """Génère une allocation aléatoire pour un actif"""
    # Sélectionner aléatoirement entre 1 et 4 catégories
    num_categories = random.randint(1, 4)
    categories = random.sample(ASSET_CATEGORIES, num_categories)

    # Allocation aléatoire
    allocation = {}
    remaining = 100.0

    for i, category in enumerate(categories):
        if i == len(categories) - 1:
            # Dernière catégorie prend le restant
            allocation[category] = remaining
        else:
            # Allocation aléatoire entre 10% et le restant
            value = round(random.uniform(10.0, min(90.0, remaining - 10.0 * (len(categories) - i - 1))), 1)
            allocation[category] = value
            remaining -= value

    return allocation


def generate_geo_allocation(allocation: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """Génère une répartition géographique pour chaque catégorie d'allocation"""
    geo_allocation = {}

    for category, percentage in allocation.items():
        # Ignorer les catégories avec 0%
        if percentage <= 0:
            continue

        # Répartition géographique pour cette catégorie
        geo_zones = {}
        remaining = 100.0

        # Sélectionner entre 1 et 5 zones géographiques
        num_zones = random.randint(1, min(5, len(GEO_ZONES)))
        selected_zones = random.sample(GEO_ZONES, num_zones)

        for i, zone in enumerate(selected_zones):
            if i == len(selected_zones) - 1:
                # Dernière zone prend le restant
                geo_zones[zone] = remaining
            else:
                # Allocation aléatoire entre 5% et le restant
                value = round(random.uniform(5.0, min(80.0, remaining - 5.0 * (len(selected_zones) - i - 1))), 1)
                geo_zones[zone] = value
                remaining -= value

        geo_allocation[category] = geo_zones

    return geo_allocation


def create_assets(db: Session, user_id: str, accounts: List[Account], count: int = 500) -> List[Asset]:
    """Crée le nombre spécifié d'actifs répartis entre les comptes"""
    assets = []

    # Répartir les actifs entre les comptes selon leur type
    assets_by_account_type = {
        "courant": count * 0.05,  # 5% des actifs
        "livret": count * 0.1,  # 10% des actifs
        "pea": count * 0.3,  # 30% des actifs
        "titre": count * 0.3,  # 30% des actifs
        "assurance_vie": count * 0.2,  # 20% des actifs
        "autre": count * 0.05  # 5% des actifs
    }

    # Compter le nombre de comptes par type
    account_type_counts = {}
    for account in accounts:
        if account.type not in account_type_counts:
            account_type_counts[account.type] = 0
        account_type_counts[account.type] += 1

    # Calculer le nombre d'actifs par compte pour chaque type
    assets_per_account = {}
    for account_type, asset_count in assets_by_account_type.items():
        if account_type in account_type_counts and account_type_counts[account_type] > 0:
            assets_per_account[account_type] = int(asset_count / account_type_counts[account_type])
        else:
            # Redistribuer aux autres types
            for other_type in account_type_counts.keys():
                if account_type_counts[other_type] > 0:
                    assets_by_account_type[other_type] += asset_count / len(account_type_counts)

    # Types de produits par type de compte
    product_types_by_account = {
        "courant": ["cash"],
        "livret": ["cash"],
        "pea": ["etf", "action", "sicav"],
        "titre": ["etf", "action", "obligation", "sicav", "reits", "crypto", "metal"],
        "assurance_vie": ["fonds_euro", "etf", "sicav", "scpi"],
        "autre": ["autre", "immo_direct"]
    }

    # Dénominations, descriptions et ISINs pour les types de produits
    product_templates = {
        "etf": [
            {"name": "MSCI World", "isin": "IE00B4L5Y983"},
            {"name": "S&P 500", "isin": "IE00B5BMR087"},
            {"name": "NASDAQ 100", "isin": "IE00B53SZB19"},
            {"name": "FTSE All-World", "isin": "IE00B3RBWM25"},
            {"name": "Euro Stoxx 50", "isin": "FR0007054358"},
            {"name": "MSCI Emerging Markets", "isin": "IE00B4L5YC18"},
            {"name": "MSCI Europe", "isin": "IE00B60SWY32"},
            {"name": "Nikkei 225", "isin": "FR0010245514"},
            {"name": "Russell 2000", "isin": "IE00B3VWLG82"},
            {"name": "FTSE 100", "isin": "IE00B810Q511"}
        ],
        "action": [
            {"name": "Apple Inc.", "isin": "US0378331005"},
            {"name": "Microsoft", "isin": "US5949181045"},
            {"name": "Amazon", "isin": "US0231351067"},
            {"name": "Alphabet (Google)", "isin": "US02079K1079"},
            {"name": "LVMH", "isin": "FR0000121014"},
            {"name": "TotalEnergies", "isin": "FR0000120271"},
            {"name": "BNP Paribas", "isin": "FR0000131104"},
            {"name": "Sanofi", "isin": "FR0000120578"},
            {"name": "L'Oréal", "isin": "FR0000120321"},
            {"name": "Air Liquide", "isin": "FR0000120073"}
        ],
        "obligation": [
            {"name": "OAT 10 ans", "isin": "FR0010809996"},
            {"name": "Bund allemand", "isin": "DE0001102580"},
            {"name": "Treasury US 10 ans", "isin": "US912810SP45"},
            {"name": "Obligation d'entreprise EUR", "isin": "IE00B3F81R35"},
            {"name": "Obligation High Yield", "isin": "IE00B66F4759"}
        ],
        "sicav": [
            {"name": "Carmignac Patrimoine", "isin": "FR0010135103"},
            {"name": "Amundi Patrimoine", "isin": "FR0011199371"},
            {"name": "H2O Multibonds", "isin": "FR0010923375"},
            {"name": "CPR Croissance Réactive", "isin": "FR0010097683"}
        ],
        "scpi": [
            {"name": "Primopierre", "isin": None},
            {"name": "Rivoli Avenir Patrimoine", "isin": None},
            {"name": "PFO2", "isin": None},
            {"name": "Efimmo", "isin": None}
        ],
        "reits": [
            {"name": "Unibail-Rodamco-Westfield", "isin": "FR0013326246"},
            {"name": "Vonovia", "isin": "DE000A1ML7J1"},
            {"name": "Simon Property Group", "isin": "US8288061091"}
        ],
        "fonds_euro": [
            {"name": "Fonds Euro Sécurité", "isin": None},
            {"name": "Eurocit'", "isin": None},
            {"name": "Netissima", "isin": None}
        ],
        "crypto": [
            {"name": "Bitcoin", "isin": None},
            {"name": "Ethereum", "isin": None},
            {"name": "Ripple", "isin": None},
            {"name": "Cardano", "isin": None}
        ],
        "metal": [
            {"name": "Or physique", "isin": None, "ounces": lambda: round(random.uniform(1.0, 50.0), 2)},
            {"name": "Argent physique", "isin": None, "ounces": lambda: round(random.uniform(10.0, 500.0), 2)},
            {"name": "Platine", "isin": None, "ounces": lambda: round(random.uniform(0.5, 10.0), 2)}
        ],
        "cash": [
            {"name": "Liquidités", "isin": None},
            {"name": "Épargne de précaution", "isin": None},
            {"name": "Compte sur livret", "isin": None}
        ],
        "immo_direct": [
            {"name": "Appartement Paris", "isin": None},
            {"name": "Maison Bordeaux", "isin": None},
            {"name": "Studio Lyon", "isin": None},
            {"name": "Parking Marseille", "isin": None}
        ],
        "autre": [
            {"name": "Tableau d'art", "isin": None},
            {"name": "Collection de montres", "isin": None},
            {"name": "Cave à vin", "isin": None}
        ]
    }

    # Devises par type de produit
    currencies_by_product = {
        "etf": ["EUR", "USD"],
        "action": ["EUR", "USD"],
        "obligation": ["EUR", "USD"],
        "sicav": ["EUR"],
        "scpi": ["EUR"],
        "reits": ["EUR", "USD"],
        "fonds_euro": ["EUR"],
        "crypto": ["USD"],
        "metal": ["USD"],
        "cash": ["EUR"],
        "immo_direct": ["EUR"],
        "autre": ["EUR"]
    }

    # Créer les actifs pour chaque compte
    for account in accounts:
        # Déterminer le nombre d'actifs pour ce compte
        num_assets = assets_per_account.get(account.type, 0)
        if num_assets <= 0:
            continue

        # Types de produits disponibles pour ce type de compte
        available_product_types = product_types_by_account.get(account.type, ["autre"])

        for i in range(num_assets):
            # Sélectionner aléatoirement un type de produit
            product_type = random.choice(available_product_types)

            # Sélectionner un template pour ce type de produit
            product_templates_for_type = product_templates.get(product_type, [{"name": "Actif divers", "isin": None}])
            product_template = random.choice(product_templates_for_type)

            # Générer un nom avec suffixe si nécessaire pour éviter les doublons
            asset_name = product_template["name"]
            if random.random() < 0.3:  # 30% de chance d'ajouter un suffixe
                asset_name += f" {fake.word().capitalize()}"

            # Devises disponibles pour ce type de produit
            available_currencies = currencies_by_product.get(product_type, ["EUR"])
            currency = random.choice(available_currencies)

            # Générer des valeurs monétaires
            value = round(random.uniform(100.0, 100000.0), 2)

            # Le prix de revient est soit égal, soit légèrement différent
            if random.random() < 0.7:  # 70% de chance d'avoir une plus-value ou moins-value
                cost = round(value * random.uniform(0.7, 1.3), 2)  # ±30%
            else:
                cost = value

            # Génération des allocations
            allocation = generate_allocation()
            geo_allocation = generate_geo_allocation(allocation)

            # Notes et todo aléatoires
            notes = ""
            if random.random() < 0.3:  # 30% de chance d'avoir des notes
                notes = fake.paragraph(nb_sentences=2)

            todo = ""
            if random.random() < 0.1:  # 10% de chance d'avoir une tâche
                todo = fake.sentence()

            # Données spécifiques selon le type de produit
            isin = product_template.get("isin")
            ounces = None
            if product_type == "metal" and "ounces" in product_template:
                ounces = product_template["ounces"]()

            # Créer l'actif
            new_asset = asset_service.add_asset(
                db=db,
                user_id=user_id,
                nom=asset_name,
                compte_id=account.id,
                type_produit=product_type,
                allocation=allocation,
                geo_allocation=geo_allocation,
                valeur_actuelle=value,
                prix_de_revient=cost,
                devise=currency,
                notes=notes,
                todo=todo,
                isin=isin,
                ounces=ounces
            )

            if new_asset:
                assets.append(new_asset)
                if i % 50 == 0:  # Afficher progression
                    print(f"Progrès: {len(assets)} actifs créés sur {count}...")

    return assets


def create_history_entry(db: Session, user_id: str):
    """Crée un point d'historique pour tous les actifs de l'utilisateur"""
    history_point = DataService.record_history_entry(db, user_id)
    if history_point:
        print(f"Point d'historique créé pour la date {history_point.date}")
    return history_point


def main():
    """Fonction principale pour la création des fixtures"""
    print("Création des fixtures pour l'application de gestion patrimoniale")
    print("==============================================================")

    # Initialiser la connexion à la base de données
    db = next(get_db())

    try:
        # Créer les tables si elles n'existent pas
        Base.metadata.create_all(bind=engine)

        # Paramètres
        username = "fredo"
        password = "fredo"
        num_banks = 5
        num_accounts = 10
        num_assets = 500

        # Créer l'utilisateur
        user = create_user(db, username, password)

        # Créer les banques pour l'utilisateur
        banks = create_banks(db, user.id, num_banks)

        # Créer les comptes répartis entre les banques
        accounts = create_accounts(db, banks, num_accounts)

        # Créer les actifs répartis entre les comptes
        assets = create_assets(db, user.id, accounts, num_assets)

        # Créer un point d'historique
        history_point = create_history_entry(db, user.id)

        print(f"\nRésumé des fixtures créées:")
        print(f"- Utilisateur: {username}")
        print(f"- Nombre de banques: {len(banks)}")
        print(f"- Nombre de comptes: {len(accounts)}")
        print(f"- Nombre d'actifs: {len(assets)}")
        print(f"- Point d'historique créé le: {history_point.date if history_point else 'Aucun'}")
        print("\nVous pouvez maintenant vous connecter avec:")
        print(f"  - Nom d'utilisateur: {username}")
        print(f"  - Mot de passe: {password}")

    except Exception as e:
        print(f"Erreur pendant la création des fixtures: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
