"""
Tests pour les calculs de sommes et totaux des actifs
"""
import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import Asset, User, Account, Bank
from services.visualization_service import VisualizationService


class TestAssetTotals:
    """Tests spécifiques pour les calculs de sommes et totaux des actifs"""

    def setup_test_data(self, db_session: Session, test_user: User):
        """
        Configuration de données de test complexes pour vérifier les calculs de sommes
        """
        # Créer deux banques pour tester les sommes par banque
        bank1 = Bank(
            id=f"test-bank1-{uuid.uuid4().hex[:8]}",
            owner_id=test_user.id,
            nom="Banque Test 1",
            notes="Banque principale"
        )

        bank2 = Bank(
            id=f"test-bank2-{uuid.uuid4().hex[:8]}",
            owner_id=test_user.id,
            nom="Banque Test 2",
            notes="Banque secondaire"
        )

        db_session.add_all([bank1, bank2])
        db_session.flush()

        # Créer plusieurs comptes avec différentes caractéristiques
        account1 = Account(
            id=f"test-account1-{uuid.uuid4().hex[:8]}",
            bank_id=bank1.id,
            type="courant",
            libelle="Compte Courant"
        )

        account2 = Account(
            id=f"test-account2-{uuid.uuid4().hex[:8]}",
            bank_id=bank1.id,
            type="titre",
            libelle="Compte Titres"
        )

        account3 = Account(
            id=f"test-account3-{uuid.uuid4().hex[:8]}",
            bank_id=bank2.id,
            type="pea",
            libelle="PEA"
        )

        db_session.add_all([account1, account2, account3])
        db_session.flush()

        # Créer différents actifs avec diverses devises
        # Compte 1: Actifs en EUR
        assets = [
            # Compte 1 - Banque 1
            Asset(
                id=f"test-asset1-eur-{uuid.uuid4().hex[:8]}",
                owner_id=test_user.id,
                account_id=account1.id,
                nom="Livret A",
                type_produit="cash",
                categorie="cash",
                allocation={"cash": 100.0},
                geo_allocation={"cash": {"europe_zone_euro": 100.0}},
                valeur_actuelle=10000.0,
                prix_de_revient=10000.0,
                devise="EUR",
                date_maj=datetime.now().strftime("%Y-%m-%d"),
                value_eur=10000.0  # Déjà en EUR
            ),
            Asset(
                id=f"test-asset2-eur-{uuid.uuid4().hex[:8]}",
                owner_id=test_user.id,
                account_id=account1.id,
                nom="Compte Epargne",
                type_produit="cash",
                categorie="cash",
                allocation={"cash": 100.0},
                geo_allocation={"cash": {"europe_zone_euro": 100.0}},
                valeur_actuelle=5000.0,
                prix_de_revient=5000.0,
                devise="EUR",
                date_maj=datetime.now().strftime("%Y-%m-%d"),
                value_eur=5000.0  # Déjà en EUR
            ),

            # Compte 2 - Banque 1 - Actifs en EUR et USD
            Asset(
                id=f"test-asset3-eur-{uuid.uuid4().hex[:8]}",
                owner_id=test_user.id,
                account_id=account2.id,
                nom="ETF MSCI World",
                type_produit="etf",
                categorie="actions",
                allocation={"actions": 100.0},
                geo_allocation={"actions": {
                    "amerique_nord": 60.0,
                    "europe_zone_euro": 20.0,
                    "europe_hors_zone_euro": 10.0,
                    "japon": 5.0,
                    "chine": 5.0
                }},
                valeur_actuelle=20000.0,
                prix_de_revient=18000.0,
                devise="EUR",
                date_maj=datetime.now().strftime("%Y-%m-%d"),
                value_eur=20000.0  # Déjà en EUR
            ),
            Asset(
                id=f"test-asset4-usd-{uuid.uuid4().hex[:8]}",
                owner_id=test_user.id,
                account_id=account2.id,
                nom="Actions Apple",
                type_produit="action",
                categorie="actions",
                allocation={"actions": 100.0},
                geo_allocation={"actions": {"amerique_nord": 100.0}},
                valeur_actuelle=5000.0,  # En USD
                prix_de_revient=4000.0,  # En USD
                devise="USD",
                date_maj=datetime.now().strftime("%Y-%m-%d"),
                value_eur=4500.0,  # Conversion en EUR (taux USD/EUR = 0.9)
                exchange_rate=0.9
            ),

            # Compte 3 - Banque 2 - Actifs en EUR, GBP
            Asset(
                id=f"test-asset5-eur-{uuid.uuid4().hex[:8]}",
                owner_id=test_user.id,
                account_id=account3.id,
                nom="ETF Eurostoxx 50",
                type_produit="etf",
                categorie="actions",
                allocation={"actions": 100.0},
                geo_allocation={"actions": {"europe_zone_euro": 100.0}},
                valeur_actuelle=15000.0,
                prix_de_revient=14000.0,
                devise="EUR",
                date_maj=datetime.now().strftime("%Y-%m-%d"),
                value_eur=15000.0  # Déjà en EUR
            ),
            Asset(
                id=f"test-asset6-gbp-{uuid.uuid4().hex[:8]}",
                owner_id=test_user.id,
                account_id=account3.id,
                nom="Actions Unilever",
                type_produit="action",
                categorie="actions",
                allocation={"actions": 100.0},
                geo_allocation={"actions": {"europe_hors_zone_euro": 100.0}},
                valeur_actuelle=3000.0,  # En GBP
                prix_de_revient=2800.0,  # En GBP
                devise="GBP",
                date_maj=datetime.now().strftime("%Y-%m-%d"),
                value_eur=3600.0,  # Conversion en EUR (taux GBP/EUR = 1.2)
                exchange_rate=1.2
            )
        ]

        db_session.add_all(assets)
        db_session.commit()

        return {
            "banks": [bank1, bank2],
            "accounts": [account1, account2, account3],
            "assets": assets
        }

    def test_total_assets_value(self, db_session: Session, test_user: User):
        """Test du calcul de la valeur totale des actifs d'un utilisateur"""
        test_data = self.setup_test_data(db_session, test_user)

        # 1. Test du total global de tous les actifs en EUR
        total_eur_query = db_session.query(
            func.sum(Asset.value_eur)
        ).filter(
            Asset.owner_id == test_user.id
        )

        total_eur = total_eur_query.scalar() or 0.0

        # Vérifier que le total correspond à la somme attendue
        # 10000 + 5000 + 20000 + 4500 + 15000 + 3600 = 58100 EUR
        expected_total = 58100.0
        assert abs(total_eur - expected_total) < 0.01, f"Total EUR {total_eur} ≠ {expected_total}"

        # 2. Test des totaux par banque
        bank_totals = db_session.query(
            Account.bank_id,
            func.sum(Asset.value_eur).label('total_eur')
        ).join(
            Asset, Asset.account_id == Account.id
        ).filter(
            Asset.owner_id == test_user.id
        ).group_by(
            Account.bank_id
        ).all()

        bank_totals_dict = {bank_id: total for bank_id, total in bank_totals}

        # Banque 1: 10000 + 5000 + 20000 + 4500 = 39500 EUR
        # Banque 2: 15000 + 3600 = 18600 EUR
        bank1_id = test_data["banks"][0].id
        bank2_id = test_data["banks"][1].id

        assert abs(bank_totals_dict[bank1_id] - 39500) < 0.01, f"Banque 1 total {bank_totals_dict[bank1_id]} ≠ 39500"
        assert abs(bank_totals_dict[bank2_id] - 18600) < 0.01, f"Banque 2 total {bank_totals_dict[bank2_id]} ≠ 18600"

        # 3. Test des totaux par compte
        account_totals = db_session.query(
            Asset.account_id,
            func.sum(Asset.value_eur).label('total_eur')
        ).filter(
            Asset.owner_id == test_user.id
        ).group_by(
            Asset.account_id
        ).all()

        account_totals_dict = {acc_id: total for acc_id, total in account_totals}

        # Compte 1: 10000 + 5000 = 15000 EUR
        # Compte 2: 20000 + 4500 = 24500 EUR
        # Compte 3: 15000 + 3600 = 18600 EUR
        account1_id = test_data["accounts"][0].id
        account2_id = test_data["accounts"][1].id
        account3_id = test_data["accounts"][2].id

        assert abs(account_totals_dict[
                       account1_id] - 15000) < 0.01, f"Compte 1 total {account_totals_dict[account1_id]} ≠ 15000"
        assert abs(account_totals_dict[
                       account2_id] - 24500) < 0.01, f"Compte 2 total {account_totals_dict[account2_id]} ≠ 24500"
        assert abs(account_totals_dict[
                       account3_id] - 18600) < 0.01, f"Compte 3 total {account_totals_dict[account3_id]} ≠ 18600"

        # 4. Test des totaux par devise (valeur actuelle)
        currency_totals = db_session.query(
            Asset.devise,
            func.sum(Asset.valeur_actuelle).label('total_valeur')
        ).filter(
            Asset.owner_id == test_user.id
        ).group_by(
            Asset.devise
        ).all()

        currency_totals_dict = {devise: total for devise, total in currency_totals}

        # EUR: 10000 + 5000 + 20000 + 15000 = 50000 EUR
        # USD: 5000 USD
        # GBP: 3000 GBP
        assert abs(currency_totals_dict["EUR"] - 50000) < 0.01, f"EUR total {currency_totals_dict['EUR']} ≠ 50000"
        assert abs(currency_totals_dict["USD"] - 5000) < 0.01, f"USD total {currency_totals_dict['USD']} ≠ 5000"
        assert abs(currency_totals_dict["GBP"] - 3000) < 0.01, f"GBP total {currency_totals_dict['GBP']} ≠ 3000"

        # 5. Test des totaux par devise (après conversion en EUR)
        # EUR: 50000 EUR (pas de conversion)
        # USD: 5000 USD × 0.9 = 4500 EUR
        # GBP: 3000 GBP × 1.2 = 3600 EUR
        # Total: 58100 EUR
        expected_total_converted = 50000 + 4500 + 3600
        assert abs(
            total_eur - expected_total_converted) < 0.01, f"Total converti {total_eur} ≠ {expected_total_converted}"

    def test_allocation_totals(self, db_session: Session, test_user: User):
        """Test des calculs de sommes d'allocations par catégorie"""
        test_data = self.setup_test_data(db_session, test_user)

        # Utiliser le service de visualisation pour calculer les valeurs par catégorie
        categories = ["actions", "obligations", "immobilier", "crypto", "metaux", "cash"]
        category_values = VisualizationService.calculate_category_values(
            db_session, test_user.id, None, categories
        )

        # Calcul manuel attendu :
        # Actions: 20000 + 4500 + 15000 + 3600 = 43100 EUR
        # Cash: 10000 + 5000 = 15000 EUR
        # Autres catégories: 0
        assert category_values is not None

        assert abs(category_values["actions"] - 43100) < 0.01, f"Actions {category_values['actions']} ≠ 43100"
        assert abs(category_values["cash"] - 15000) < 0.01, f"Cash {category_values['cash']} ≠ 15000"
        assert category_values["obligations"] == 0.0, "Obligations devraient être à 0"
        assert category_values["immobilier"] == 0.0, "Immobilier devrait être à 0"
        assert category_values["crypto"] == 0.0, "Crypto devrait être à 0"
        assert category_values["metaux"] == 0.0, "Métaux devraient être à 0"

        # Vérifier que la somme des catégories correspond au total global
        total_categories = sum(category_values.values())
        expected_total = 58100.0
        assert abs(
            total_categories - expected_total) < 0.01, f"Total des catégories {total_categories} ≠ {expected_total}"

        # Tester le calcul pour un compte spécifique
        account1_id = test_data["accounts"][0].id
        category_values_account1 = VisualizationService.calculate_category_values(
            db_session, test_user.id, account1_id, categories
        )

        # Calcul manuel pour le compte 1:
        # Cash: 10000 + 5000 = 15000 EUR
        # Autres catégories: 0
        assert abs(category_values_account1[
                       "cash"] - 15000) < 0.01, f"Cash compte 1 {category_values_account1['cash']} ≠ 15000"
        assert category_values_account1["actions"] == 0.0, "Actions compte 1 devraient être à 0"

        # Total du compte 1
        total_account1 = sum(category_values_account1.values())
        expected_account1 = 15000.0
        assert abs(total_account1 - expected_account1) < 0.01, f"Total compte 1 {total_account1} ≠ {expected_account1}"

    def test_geo_allocation_totals(self, db_session: Session, test_user: User):
        """Test des calculs de sommes par zones géographiques"""
        test_data = self.setup_test_data(db_session, test_user)

        # Liste des zones géographiques
        geo_zones = ["amerique_nord", "europe_zone_euro", "europe_hors_zone_euro",
                     "japon", "chine", "inde", "asie_developpee", "autres_emergents",
                     "global_non_classe"]

        # Calculer les valeurs par zone géographique pour la catégorie Actions
        geo_values_actions = VisualizationService.calculate_geo_values(
            db_session, test_user.id, None, "actions", geo_zones
        )

        # Calculs attendus pour les actions :
        # Amérique du Nord: 
        # - ETF MSCI World: 20000 × 0.6 = 12000
        # - Actions Apple: 4500 × 1.0 = 4500
        # Total Amérique du Nord: 16500 EUR

        # Europe Zone Euro:
        # - ETF MSCI World: 20000 × 0.2 = 4000
        # - ETF Eurostoxx: 15000 × 1.0 = 15000
        # Total Europe Zone Euro: 19000 EUR

        # Europe Hors Zone Euro:
        # - ETF MSCI World: 20000 × 0.1 = 2000
        # - Actions Unilever: 3600 × 1.0 = 3600
        # Total Europe Hors Zone Euro: 5600 EUR

        # Japon: ETF MSCI World: 20000 × 0.05 = 1000 EUR
        # Chine: ETF MSCI World: 20000 × 0.05 = 1000 EUR

        # Vérifications (avec une marge d'erreur pour les arrondis)
        assert abs(geo_values_actions[
                       "amerique_nord"] - 16500) < 100, f"Amérique du Nord {geo_values_actions['amerique_nord']} ≠ ~16500"
        assert abs(geo_values_actions[
                       "europe_zone_euro"] - 19000) < 100, f"Europe Zone Euro {geo_values_actions['europe_zone_euro']} ≠ ~19000"
        assert abs(geo_values_actions[
                       "europe_hors_zone_euro"] - 5600) < 100, f"Europe Hors Zone Euro {geo_values_actions['europe_hors_zone_euro']} ≠ ~5600"
        assert abs(geo_values_actions["japon"] - 1000) < 100, f"Japon {geo_values_actions['japon']} ≠ ~1000"
        assert abs(geo_values_actions["chine"] - 1000) < 100, f"Chine {geo_values_actions['chine']} ≠ ~1000"

        # Vérifier que la somme correspond au total des actions
        # Total des actions: 43100 EUR
        total_geo_actions = sum(geo_values_actions.values())
        expected_actions_total = 43100.0
        assert abs(
            total_geo_actions - expected_actions_total) < 100, f"Total géo actions {total_geo_actions} ≠ ~{expected_actions_total}"

        # Calculer les valeurs par zone géographique pour la catégorie Cash
        geo_values_cash = VisualizationService.calculate_geo_values(
            db_session, test_user.id, None, "cash", geo_zones
        )

        # Cash est totalement en Europe Zone Euro: 15000 EUR
        assert abs(geo_values_cash[
                       "europe_zone_euro"] - 15000) < 100, f"Europe Zone Euro cash {geo_values_cash['europe_zone_euro']} ≠ ~15000"

        # Vérifier le total global (toutes catégories)
        geo_values_all = {}
        for zone in geo_zones:
            geo_values_all[zone] = 0
            if zone in geo_values_actions:
                geo_values_all[zone] += geo_values_actions[zone]
            if zone in geo_values_cash:
                geo_values_all[zone] += geo_values_cash[zone]

        total_all_zones = sum(geo_values_all.values())
        expected_total = 58100.0
        assert abs(total_all_zones - expected_total) < 100, f"Total toutes zones {total_all_zones} ≠ ~{expected_total}"
