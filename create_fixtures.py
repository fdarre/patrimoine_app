"""
Script pour générer des fixtures de test pour l'application de gestion patrimoniale.
Ce script va créer un jeu complet de données de test pour l'utilisateur 'fred'.
"""
import os
import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, List

from database.db_config import get_db, engine, Base
from database.models import User, Bank, Account, Asset
from utils.password import hash_password
from utils.constants import ACCOUNT_TYPES, PRODUCT_TYPES, ASSET_CATEGORIES, GEO_ZONES, CURRENCIES
from utils.calculations import get_default_geo_zones


# Fonction pour obtenir une distribution aléatoire totalisant 100%
def get_random_distribution(categories: List[str], min_pct: int = 5) -> Dict[str, float]:
    """Génère une distribution aléatoire qui totalise 100%"""
    # Sélectionner un nombre aléatoire de catégories (au moins 1, au plus toutes)
    n_categories = random.randint(1, len(categories))
    selected_categories = random.sample(categories, n_categories)

    # Assurer que chaque catégorie a au moins min_pct
    remaining = 100 - (min_pct * n_categories)
    distribution = {cat: min_pct for cat in selected_categories}

    # Distribuer le reste
    for cat in selected_categories:
        if remaining <= 0:
            break
        extra = random.randint(0, remaining)
        distribution[cat] += extra
        remaining -= extra

    # Si on a encore un reste, l'ajouter à la dernière catégorie
    if remaining > 0 and selected_categories:
        distribution[selected_categories[-1]] += remaining

    return distribution


# Fonction principale pour créer les fixtures
def create_fixtures():
    """Crée toutes les fixtures pour l'application"""
    # Obtenir une session de base de données
    db = next(get_db())

    try:
        print("Création des fixtures pour la gestion patrimoniale...")

        # 1. Vérifier si l'utilisateur 'fred' existe
        user = db.query(User).filter(User.username == "fred").first()

        if not user:
            # Créer l'utilisateur 'fred'
            user = User(
                id=str(uuid.uuid4()),
                username="fred",
                email="fred@example.com",
                password_hash=hash_password("fred"),
                is_active=True,
                created_at=datetime.now()
            )
            db.add(user)
            db.commit()
            print(f"Utilisateur 'fred' créé avec l'ID: {user.id}")
        else:
            print(f"Utilisateur 'fred' trouvé avec l'ID: {user.id}")

            # Supprimer tous les actifs existants pour cet utilisateur
            assets = db.query(Asset).filter(Asset.owner_id == user.id).all()
            for asset in assets:
                db.delete(asset)

            print(f"{len(assets)} actifs existants supprimés")
            db.commit()

        # 2. Créer ou récupérer les banques pour cet utilisateur
        banks_data = [
            {"id": "boursorama", "nom": "Boursorama Banque", "notes": "Banque en ligne"},
            {"id": "bnp", "nom": "BNP Paribas", "notes": "Banque traditionnelle"},
            {"id": "credit_agricole", "nom": "Crédit Agricole", "notes": "Banque verte"},
            {"id": "lcl", "nom": "LCL", "notes": "Ex Crédit Lyonnais"},
            {"id": "societe_generale", "nom": "Société Générale", "notes": ""}
        ]

        banks = {}
        for bank_data in banks_data:
            bank = db.query(Bank).filter(Bank.id == bank_data["id"], Bank.owner_id == user.id).first()

            if not bank:
                bank = Bank(
                    id=bank_data["id"],
                    owner_id=user.id,
                    nom=bank_data["nom"],
                    notes=bank_data["notes"]
                )
                db.add(bank)
                db.commit()
                print(f"Banque '{bank_data['nom']}' créée avec l'ID: {bank.id}")
            else:
                print(f"Banque '{bank_data['nom']}' déjà existante")

            banks[bank.id] = bank

        # 3. Créer 10 comptes répartis sur ces banques
        accounts_data = [
            {"id": "boursorama_courant", "bank_id": "boursorama", "type": "courant",
             "libelle": "Compte courant Boursorama"},
            {"id": "boursorama_livret", "bank_id": "boursorama", "type": "livret", "libelle": "Livret A Boursorama"},
            {"id": "boursorama_pea", "bank_id": "boursorama", "type": "pea", "libelle": "PEA Boursorama"},
            {"id": "bnp_courant", "bank_id": "bnp", "type": "courant", "libelle": "Compte courant BNP"},
            {"id": "bnp_assurance_vie", "bank_id": "bnp", "type": "assurance_vie", "libelle": "Assurance Vie BNP"},
            {"id": "ca_titre", "bank_id": "credit_agricole", "type": "titre", "libelle": "CTO Crédit Agricole"},
            {"id": "ca_assurance_vie", "bank_id": "credit_agricole", "type": "assurance_vie",
             "libelle": "Assurance Vie CA"},
            {"id": "sg_pea", "bank_id": "societe_generale", "type": "pea", "libelle": "PEA Société Générale"},
            {"id": "sg_livret", "bank_id": "societe_generale", "type": "livret", "libelle": "LDDS Société Générale"},
            {"id": "lcl_titre", "bank_id": "lcl", "type": "titre", "libelle": "CTO LCL"}
        ]

        accounts = {}
        for account_data in accounts_data:
            account = db.query(Account).filter(Account.id == account_data["id"]).first()

            if not account:
                account = Account(
                    id=account_data["id"],
                    bank_id=account_data["bank_id"],
                    type=account_data["type"],
                    libelle=account_data["libelle"]
                )
                db.add(account)
                db.commit()
                print(f"Compte '{account_data['libelle']}' créé avec l'ID: {account.id}")
            else:
                print(f"Compte '{account_data['libelle']}' déjà existant")

            accounts[account.id] = account

        # 4. Créer 100 actifs répartis sur ces comptes
        print("Création de 100 actifs...")

        # Définir des données réalistes pour chaque type d'actif
        product_names = {
            "etf": ["Amundi MSCI World", "Lyxor EURO STOXX 50", "iShares MSCI Emerging Markets",
                    "Vanguard S&P 500", "SPDR Gold", "Xtrackers DAX", "Lyxor NASDAQ-100",
                    "iShares Core Euro Corp Bond", "Amundi ETF Gov Bond EuroMTS", "BNP Paribas Easy CAC 40"],
            "sicav": ["Carmignac Patrimoine", "H2O Multibonds", "DNCA Evolutif",
                      "Comgest Growth Europe", "Fidelity European Growth", "Echiquier Agressor",
                      "Nordea 1 Global Climate", "BlackRock Global Funds", "Pictet Digital", "JPMorgan Global Focus"],
            "action": ["Total Energies", "LVMH", "Apple", "Microsoft", "Amazon", "Google",
                       "Sanofi", "L'Oréal", "AXA", "BNP Paribas", "Airbus", "Carrefour",
                       "Danone", "Air Liquide", "Veolia", "Unilever", "Coca-Cola", "Nestlé"],
            "obligation": ["OAT France 10 ans", "Bund Allemand 5 ans", "US Treasury 30 ans",
                           "Obligation Italie 7 ans", "UK Gilt 15 ans", "Obligation Espagne 10 ans",
                           "Obligation Entreprise A", "Obligation Entreprise B"],
            "scpi": ["Primopierre", "Rivoli Avenir Patrimoine", "Immorente", "PFO2",
                     "Efimmo", "Pierval Santé", "SCPI de Rendement", "SCPI Fiscale"],
            "reits": ["Unibail-Rodamco-Westfield", "Gecina", "Klepierre", "Covivio",
                      "Icade", "Hammerson", "British Land", "Land Securities"],
            "fonds_euro": ["Fonds Euro Assurance A", "Fonds Euro Assurance B", "Fonds Euro Sécurité",
                           "Fonds Euro Croissance", "Fonds Euro Garanti"],
            "crypto": ["Bitcoin", "Ethereum", "Solana", "Ripple", "Cardano",
                       "Polkadot", "Avalanche", "Dogecoin"],
            "metal": ["Or physique", "Argent", "Platine", "Palladium", "Lingot d'or",
                      "Napoléon", "Once d'argent"],
            "cash": ["Compte courant", "Livret A", "LDDS", "Compte sur livret",
                     "Liquidités en attente"],
            "immo_direct": ["Appartement Paris", "Maison Marseille", "Studio locatif Lyon",
                            "Résidence secondaire", "Parking locatif Bordeaux",
                            "Appartement locatif Nantes"],
            "autre": ["Collection de montres", "Œuvre d'art", "Collection de vin",
                      "Véhicule de collection", "Bijoux", "Placement atypique"]
        }

        # Données spécifiques pour chaque type d'actif
        asset_type_configs = {
            "etf": {
                "value_range": (1000, 15000),
                "main_categories": ["actions", "obligations"],
                "isin_possible": True
            },
            "sicav": {
                "value_range": (2000, 25000),
                "main_categories": ["actions", "obligations"],
                "isin_possible": True
            },
            "action": {
                "value_range": (500, 10000),
                "main_categories": ["actions"],
                "isin_possible": True
            },
            "obligation": {
                "value_range": (5000, 30000),
                "main_categories": ["obligations"],
                "isin_possible": True
            },
            "scpi": {
                "value_range": (10000, 50000),
                "main_categories": ["immobilier"],
                "isin_possible": False
            },
            "reits": {
                "value_range": (2000, 20000),
                "main_categories": ["immobilier"],
                "isin_possible": True
            },
            "fonds_euro": {
                "value_range": (5000, 100000),
                "main_categories": ["obligations", "cash"],
                "isin_possible": False
            },
            "crypto": {
                "value_range": (500, 5000),
                "main_categories": ["crypto"],
                "isin_possible": False
            },
            "metal": {
                "value_range": (1000, 20000),
                "main_categories": ["metaux"],
                "isin_possible": False
            },
            "cash": {
                "value_range": (500, 25000),
                "main_categories": ["cash"],
                "isin_possible": False
            },
            "immo_direct": {
                "value_range": (100000, 500000),
                "main_categories": ["immobilier"],
                "isin_possible": False
            },
            "autre": {
                "value_range": (1000, 30000),
                "main_categories": ["autre"],
                "isin_possible": False
            }
        }

        # Générer des ISIN fictifs
        def generate_fake_isin():
            country_code = random.choice(["FR", "US", "DE", "GB", "CH", "JP", "IT", "ES"])
            security_code = ''.join(random.choices('0123456789', k=9))
            check_digit = random.choice('0123456789')
            return f"{country_code}{security_code}{check_digit}"

        # Créer 100 actifs répartis sur les 10 comptes
        for i in range(100):
            # Choisir un compte aléatoirement
            account_id = random.choice(list(accounts.keys()))
            account = accounts[account_id]

            # Choisir un type d'actif adapté au type de compte
            if account.type == "pea":
                # PEA: uniquement actions ou ETF actions européennes
                product_type = random.choice(["etf", "action"])
            elif account.type == "assurance_vie":
                # Assurance vie: fonds euro, SCPI, ETF, SICAV
                product_type = random.choice(["fonds_euro", "scpi", "etf", "sicav"])
            elif account.type == "titre":
                # CTO: tous les produits financiers
                product_type = random.choice(["etf", "action", "obligation", "reits", "sicav"])
            elif account.type == "livret":
                # Livret: uniquement cash
                product_type = "cash"
            elif account.type == "courant":
                # Compte courant: principalement cash, quelques autres
                if random.random() < 0.8:
                    product_type = "cash"
                else:
                    product_type = random.choice(["crypto", "metal", "autre"])
            else:
                # Autre type de compte: n'importe quel produit
                product_type = random.choice(list(product_names.keys()))

            # Choisir un nom d'actif en fonction du type
            asset_name = random.choice(product_names[product_type])

            # Déterminer si cet actif a un ISIN
            has_isin = asset_type_configs[product_type]["isin_possible"] and random.random() < 0.7
            isin = generate_fake_isin() if has_isin else None

            # Déterminer si cet actif a des onces (pour les métaux)
            ounces = None
            if product_type == "metal":
                ounces = round(random.uniform(0.1, 10), 2)

            # Choisir une devise (principalement EUR)
            devise = "EUR" if random.random() < 0.8 else random.choice(["USD", "GBP", "CHF"])

            # Générer une valeur aléatoire en fonction du type d'actif
            min_value, max_value = asset_type_configs[product_type]["value_range"]
            valeur_actuelle = round(random.uniform(min_value, max_value), 2)

            # Générer un prix de revient (légèrement différent de la valeur actuelle)
            variation_pct = random.uniform(-0.15, 0.20)  # -15% à +20%
            prix_de_revient = round(valeur_actuelle / (1 + variation_pct), 2)

            # Générer une allocation par catégorie
            main_categories = asset_type_configs[product_type]["main_categories"]

            # Pour les actifs simples, allocation 100% à la catégorie principale
            if len(main_categories) == 1 or random.random() < 0.7:
                allocation = {main_categories[0]: 100}
            else:
                # Pour les actifs mixtes, répartition entre plusieurs catégories
                possible_categories = main_categories.copy()
                # Ajouter occasionnellement d'autres catégories
                for cat in ASSET_CATEGORIES:
                    if cat not in possible_categories and random.random() < 0.2:
                        possible_categories.append(cat)

                allocation = get_random_distribution(possible_categories)

            # Générer une répartition géographique par catégorie
            geo_allocation = {}
            for category in allocation.keys():
                default_geo = get_default_geo_zones(category)

                # Soit utiliser la répartition par défaut, soit générer une répartition aléatoire
                if random.random() < 0.5:
                    geo_zones = default_geo
                else:
                    geo_zones = get_random_distribution(list(default_geo.keys()))

                geo_allocation[category] = geo_zones

            # Générer des notes aléatoires (optionnel)
            if random.random() < 0.3:
                notes = random.choice([
                    "Bon rendement historique",
                    "À surveiller de près",
                    "Stable sur le long terme",
                    "Diversification intéressante",
                    "Investissement à long terme",
                    "Position stratégique",
                    "Considérer une augmentation",
                    "Considérer une réduction",
                    "Performance décevante",
                    "Excellent rapport risque/rendement"
                ])
            else:
                notes = ""

            # Générer une tâche à faire (optionnel)
            if random.random() < 0.2:
                todo = random.choice([
                    "Vérifier les frais annuels",
                    "Augmenter la position",
                    "Réduire la position",
                    "Surveiller la performance",
                    "Comparer avec des alternatives",
                    "Revoir la stratégie",
                    "Vérifier le dividende",
                    "Mettre à jour le prix",
                    "Analyser les perspectives",
                    "Vendre si dépasse X€"
                ])
            else:
                todo = ""

            # Générer une date de mise à jour (dans les 30 derniers jours)
            days_ago = random.randint(0, 30)
            date_maj = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            # Créer l'actif
            asset = Asset(
                id=str(uuid.uuid4()),
                owner_id=user.id,
                account_id=account_id,
                nom=asset_name,
                type_produit=product_type,
                categorie=list(allocation.keys())[0],  # Catégorie principale
                allocation=allocation,
                geo_allocation=geo_allocation,
                valeur_actuelle=valeur_actuelle,
                prix_de_revient=prix_de_revient,
                devise=devise,
                date_maj=date_maj,
                notes=notes,
                todo=todo,
                isin=isin,
                ounces=ounces
            )

            db.add(asset)

            # Valider la création tous les 10 assets pour améliorer les performances
            if (i + 1) % 10 == 0:
                db.commit()
                print(f"{i + 1} actifs créés...")

        # Valider les derniers ajouts
        db.commit()

        # Mettre à jour l'historique pour le jour courant
        from services.data_service import DataService
        DataService.record_history_entry(db, user.id)

        print("Fixtures créées avec succès!")

    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la création des fixtures: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    create_fixtures()