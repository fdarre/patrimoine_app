"""
Script de création de données de test (fixtures)
"""
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import func

from database.db_config import get_db_session, Base, engine
from database.models import User, Bank, Account, Asset, HistoryPoint
from utils.password import hash_password

# Créer les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

# Configuration des fixtures
USERNAME = "fredo"
PASSWORD = "fredofredo"
EMAIL = "fredo@example.com"

# Données pour les banques
BANKS = [
    {"id": "boursorama", "nom": "Boursorama Banque", "notes": "Banque en ligne principale"},
    {"id": "bnp", "nom": "BNP Paribas", "notes": "Banque physique"}
]

# Données pour les comptes
ACCOUNTS = [
    {"id": "boursorama_courant", "bank_id": "boursorama", "type": "courant", "libelle": "Compte Courant"},
    {"id": "boursorama_livret", "bank_id": "boursorama", "type": "livret", "libelle": "Livret A"},
    {"id": "boursorama_pea", "bank_id": "boursorama", "type": "pea", "libelle": "PEA"},
    {"id": "bnp_courant", "bank_id": "bnp", "type": "courant", "libelle": "Compte Courant"},
    {"id": "bnp_assurance_vie", "bank_id": "bnp", "type": "assurance_vie", "libelle": "Assurance Vie"}
]


def create_asset_data(idx, compte_id, owner_id):
    """Génère des données aléatoires pour un actif"""
    # Liste d'ETF connus
    etfs = [
        {"nom": "Amundi MSCI World", "isin": "FR0010756098", "type": "etf"},
        {"nom": "Lyxor S&P 500", "isin": "FR0011871128", "type": "etf"},
        {"nom": "iShares Core MSCI Europe", "isin": "IE00B1YZSC51", "type": "etf"},
        {"nom": "Vanguard FTSE All-World", "isin": "IE00BK5BQT80", "type": "etf"},
        {"nom": "Amundi MSCI Emerging Markets", "isin": "LU1681045370", "type": "etf"},
        {"nom": "BNP Paribas Easy CAC 40", "isin": "FR0012739431", "type": "etf"},
        {"nom": "Lyxor EURO STOXX 50", "isin": "FR0007054358", "type": "etf"},
    ]

    # Actions individuelles
    actions = [
        {"nom": "LVMH", "isin": "FR0000121014", "type": "action"},
        {"nom": "Total Energies", "isin": "FR0000120271", "type": "action"},
        {"nom": "BNP Paribas", "isin": "FR0000131104", "type": "action"},
        {"nom": "Air Liquide", "isin": "FR0000120073", "type": "action"},
        {"nom": "Microsoft", "isin": "US5949181045", "type": "action"},
        {"nom": "Apple", "isin": "US0378331005", "type": "action"},
        {"nom": "Amazon", "isin": "US0231351067", "type": "action"},
    ]

    # Fonds Euro
    fonds_euro = [
        {"nom": "Fonds Euro Sécurité", "isin": None, "type": "fonds_euro"},
        {"nom": "Fonds Capital Garanti", "isin": None, "type": "fonds_euro"},
        {"nom": "Fonds Euro Premium", "isin": None, "type": "fonds_euro"},
    ]

    # Métaux précieux
    metaux = [
        {"nom": "Or physique (1oz)", "isin": None, "type": "metal", "ounces": 1.0},
        {"nom": "Argent physique (5oz)", "isin": None, "type": "metal", "ounces": 5.0},
        {"nom": "Or physique (0.5oz)", "isin": None, "type": "metal", "ounces": 0.5},
    ]

    # Crypto
    crypto = [
        {"nom": "Bitcoin", "isin": None, "type": "crypto"},
        {"nom": "Ethereum", "isin": None, "type": "crypto"},
    ]

    # SCPI
    scpi = [
        {"nom": "SCPI Primovie", "isin": None, "type": "scpi"},
        {"nom": "SCPI Rivoli Avenir Patrimoine", "isin": None, "type": "scpi"},
    ]

    # Sélectionner un type d'actif aléatoire
    all_assets = etfs + actions + fonds_euro + metaux + crypto + scpi
    asset_template = random.choice(all_assets)

    # Valeur aléatoire entre 500 et 50000
    value = round(random.uniform(500, 50000), 2)
    cost = round(value * random.uniform(0.8, 1.2), 2)  # +/- 20% de la valeur

    # Devise (90% EUR, 10% USD)
    currency = "EUR" if random.random() < 0.9 else "USD"

    # Allocation par catégorie
    allocation = {}

    if asset_template["type"] in ["etf", "action"]:
        allocation = {"actions": 100}
    elif asset_template["type"] in ["obligation"]:
        allocation = {"obligations": 100}
    elif asset_template["type"] in ["scpi", "reits"]:
        allocation = {"immobilier": 100}
    elif asset_template["type"] == "fonds_euro":
        allocation = {"obligations": 70, "actions": 20, "immobilier": 10}
    elif asset_template["type"] == "metal":
        allocation = {"metaux": 100}
    elif asset_template["type"] == "crypto":
        allocation = {"crypto": 100}
    elif asset_template["type"] == "cash":
        allocation = {"cash": 100}
    else:
        allocation = {"autre": 100}

    # Répartition géographique
    geo_allocation = {}

    if "actions" in allocation:
        geo_allocation["actions"] = {
            "amerique_nord": 50,
            "europe_zone_euro": 30,
            "europe_hors_zone_euro": 10,
            "japon": 5,
            "asie_developpee": 5
        }

    if "obligations" in allocation:
        geo_allocation["obligations"] = {
            "amerique_nord": 30,
            "europe_zone_euro": 50,
            "europe_hors_zone_euro": 20
        }

    if "immobilier" in allocation:
        geo_allocation["immobilier"] = {
            "europe_zone_euro": 80,
            "amerique_nord": 20
        }

    if "metaux" in allocation:
        geo_allocation["metaux"] = {
            "global_non_classe": 100
        }

    if "crypto" in allocation:
        geo_allocation["crypto"] = {
            "global_non_classe": 100
        }

    if "cash" in allocation:
        geo_allocation["cash"] = {
            "europe_zone_euro": 100
        }

    if "autre" in allocation:
        geo_allocation["autre"] = {
            "global_non_classe": 100
        }

    # Notes et todo (aléatoirement)
    notes = ""
    todo = ""

    if random.random() < 0.3:  # 30% de chance d'avoir des notes
        notes = f"Notes pour {asset_template['nom']} - Ajouté le {datetime.now().strftime('%Y-%m-%d')}"

    if random.random() < 0.2:  # 20% de chance d'avoir une tâche
        todos = [
            f"Vérifier le prix actuel de {asset_template['nom']}",
            f"Évaluer si {asset_template['nom']} correspond toujours à ma stratégie",
            f"Envisager de vendre {asset_template['nom']} si le cours monte encore",
            f"Rechercher plus d'informations sur {asset_template['nom']}",
            f"Contacter le conseiller à propos de {asset_template['nom']}"
        ]
        todo = random.choice(todos)

    # Créer les données de l'actif
    asset_data = {
        "id": str(uuid.uuid4()),
        "owner_id": owner_id,
        "account_id": compte_id,
        "nom": asset_template["nom"],
        "type_produit": asset_template["type"],
        "categorie": list(allocation.keys())[0],  # Catégorie principale
        "allocation": allocation,
        "geo_allocation": geo_allocation,
        "valeur_actuelle": value,
        "prix_de_revient": cost,
        "devise": currency,
        "date_maj": datetime.now().strftime("%Y-%m-%d"),
        "notes": notes,
        "todo": todo,
        "isin": asset_template.get("isin"),
        "ounces": asset_template.get("ounces"),
        "exchange_rate": 1.0 if currency == "EUR" else 0.85,
        "value_eur": value if currency == "EUR" else value * 0.85
    }

    return asset_data


def create_fixtures():
    """Crée les données de test"""
    with get_db_session() as db:
        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(User).filter(User.username == USERNAME).first()

        if existing_user:
            print(f"L'utilisateur {USERNAME} existe déjà.")
            user_id = existing_user.id
        else:
            # Créer l'utilisateur
            user = User(
                id=str(uuid.uuid4()),
                username=USERNAME,
                email=EMAIL,
                password_hash=hash_password(PASSWORD),
                is_active=True,
                created_at=datetime.now()
            )
            db.add(user)
            db.flush()  # Pour obtenir l'ID généré
            user_id = user.id
            print(f"Utilisateur {USERNAME} créé avec l'ID {user_id}")

        # Créer les banques
        bank_ids = []
        for bank_data in BANKS:
            existing_bank = db.query(Bank).filter(Bank.id == bank_data["id"]).first()

            if existing_bank:
                print(f"La banque {bank_data['nom']} existe déjà.")
            else:
                bank = Bank(
                    id=bank_data["id"],
                    owner_id=user_id,
                    nom=bank_data["nom"],
                    notes=bank_data["notes"]
                )
                db.add(bank)
                print(f"Banque {bank_data['nom']} créée.")

            bank_ids.append(bank_data["id"])

        # Créer les comptes
        account_ids = []
        for account_data in ACCOUNTS:
            existing_account = db.query(Account).filter(Account.id == account_data["id"]).first()

            if existing_account:
                print(f"Le compte {account_data['libelle']} existe déjà.")
            else:
                account = Account(
                    id=account_data["id"],
                    bank_id=account_data["bank_id"],
                    type=account_data["type"],
                    libelle=account_data["libelle"]
                )
                db.add(account)
                print(f"Compte {account_data['libelle']} créé.")

            account_ids.append(account_data["id"])

        # Valider les changements jusqu'ici
        db.commit()

        # Créer les actifs (30 actifs)
        asset_count = db.query(Asset).filter(Asset.owner_id == user_id).count()

        if asset_count >= 30:
            print(f"L'utilisateur a déjà {asset_count} actifs. Aucun nouvel actif créé.")
        else:
            assets_to_create = 30 - asset_count
            print(f"Création de {assets_to_create} nouveaux actifs...")

            for i in range(assets_to_create):
                # Sélectionner un compte aléatoire
                compte_id = random.choice(account_ids)

                # Générer des données pour l'actif
                asset_data = create_asset_data(i, compte_id, user_id)

                # Créer l'actif
                asset = Asset(**asset_data)
                db.add(asset)

                print(f"Actif {i + 1}/{assets_to_create}: {asset_data['nom']}")

        # Créer un point d'historique
        total_value = db.query(Asset).filter(Asset.owner_id == user_id).with_entities(
            func.sum(func.coalesce(Asset.value_eur, 0.0))
        ).scalar() or 0.0

        # Créer plusieurs points d'historique sur les 12 derniers mois
        for i in range(12):
            date = (datetime.now() - timedelta(days=30 * i)).strftime("%Y-%m-%d")

            # Vérifier si un point existe déjà pour cette date
            existing_point = db.query(HistoryPoint).filter(HistoryPoint.date == date).first()

            if not existing_point:
                # Calculer une valeur historique simulée (variation de +/- 3%)
                historic_value = total_value * (1 + random.uniform(-0.03, 0.03) * i)

                # Créer le point d'historique
                history_point = HistoryPoint(
                    id=str(uuid.uuid4()),
                    date=date,
                    assets={},  # Simplifié pour les fixtures
                    total=historic_value
                )
                db.add(history_point)
                print(f"Point d'historique créé pour {date}: {historic_value:.2f} €")

        # Valider tous les changements
        db.commit()
        print("Fixtures créées avec succès!")


if __name__ == "__main__":
    create_fixtures()
