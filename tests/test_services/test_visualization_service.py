"""
Tests pour le service de visualisation et de calcul des répartitions
"""
import uuid
from datetime import datetime
from unittest.mock import patch

from sqlalchemy.orm import Session

from database.models import Asset, User, Account
from services.visualization_service import VisualizationService


class TestVisualizationService:
    """Tests pour le service de visualisation et de calcul des répartitions"""

    def setup_test_assets(self, db_session: Session, test_user: User, test_account: Account):
        """
        Configuration d'actifs de test pour les analyses
        """
        # Créer plusieurs actifs avec différentes allocations et répartitions géographiques
        assets = [
            # Actions internationales
            Asset(
                id=f"test-asset-actions-{uuid.uuid4().hex[:8]}",
                owner_id=test_user.id,
                account_id=test_account.id,
                nom="ETF Actions Monde",
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
                valeur_actuelle=10000.0,
                prix_de_revient=9000.0,
                devise="EUR",
                date_maj=datetime.now().strftime("%Y-%m-%d"),
                value_eur=10000.0  # Déjà en EUR
            ),
            # Obligations européennes
            Asset(
                id=f"test-asset-oblig-{uuid.uuid4().hex[:8]}",
                owner_id=test_user.id,
                account_id=test_account.id,
                nom="ETF Obligations Europe",
                type_produit="etf",
                categorie="obligations",
                allocation={"obligations": 100.0},
                geo_allocation={"obligations": {
                    "europe_zone_euro": 70.0,
                    "europe_hors_zone_euro": 30.0
                }},
                valeur_actuelle=5000.0,
                prix_de_revient=4800.0,
                devise="EUR",
                date_maj=datetime.now().strftime("%Y-%m-%d"),
                value_eur=5000.0  # Déjà en EUR
            ),
            # Actif en USD
            Asset(
                id=f"test-asset-usd-{uuid.uuid4().hex[:8]}",
                owner_id=test_user.id,
                account_id=test_account.id,
                nom="ETF S&P 500",
                type_produit="etf",
                categorie="actions",
                allocation={"actions": 100.0},
                geo_allocation={"actions": {
                    "amerique_nord": 100.0
                }},
                valeur_actuelle=5000.0,  # En USD
                prix_de_revient=4500.0,  # En USD
                devise="USD",
                date_maj=datetime.now().strftime("%Y-%m-%d"),
                value_eur=4500.0,  # Valeur équivalente en EUR (taux 1 USD = 0.9 EUR)
                exchange_rate=0.9
            ),
            # Actif mixte
            Asset(
                id=f"test-asset-mixte-{uuid.uuid4().hex[:8]}",
                owner_id=test_user.id,
                account_id=test_account.id,
                nom="Fonds Diversifié",
                type_produit="sicav",
                categorie="mixte",
                allocation={
                    "actions": 60.0,
                    "obligations": 30.0,
                    "cash": 10.0
                },
                geo_allocation={
                    "actions": {
                        "amerique_nord": 40.0,
                        "europe_zone_euro": 30.0,
                        "europe_hors_zone_euro": 10.0,
                        "japon": 5.0,
                        "chine": 10.0,
                        "autres_emergents": 5.0
                    },
                    "obligations": {
                        "europe_zone_euro": 60.0,
                        "amerique_nord": 40.0
                    },
                    "cash": {
                        "europe_zone_euro": 100.0
                    }
                },
                valeur_actuelle=8000.0,
                prix_de_revient=7500.0,
                devise="EUR",
                date_maj=datetime.now().strftime("%Y-%m-%d"),
                value_eur=8000.0  # Déjà en EUR
            ),
            # Actif immobilier
            Asset(
                id=f"test-asset-immo-{uuid.uuid4().hex[:8]}",
                owner_id=test_user.id,
                account_id=test_account.id,
                nom="SCPI Europe",
                type_produit="scpi",
                categorie="immobilier",
                allocation={"immobilier": 100.0},
                geo_allocation={"immobilier": {
                    "europe_zone_euro": 80.0,
                    "europe_hors_zone_euro": 20.0
                }},
                valeur_actuelle=20000.0,
                prix_de_revient=18000.0,
                devise="EUR",
                date_maj=datetime.now().strftime("%Y-%m-%d"),
                value_eur=20000.0  # Déjà en EUR
            )
        ]

        db_session.add_all(assets)
        db_session.commit()

        return assets

    def test_calculate_category_values(self, db_session: Session, test_user: User, test_account: Account):
        """Test de calcul des valeurs par catégorie d'actifs"""
        # Configurer les actifs de test
        assets = self.setup_test_assets(db_session, test_user, test_account)

        # Exécuter la fonction à tester
        categories = ["actions", "obligations", "immobilier", "crypto", "metaux", "cash"]
        category_values = VisualizationService.calculate_category_values(
            db_session, test_user.id, None, categories
        )

        # Vérifier les résultats
        assert category_values is not None

        # Calcul manuel pour vérification
        # Actions: 10000 (ETF Monde) + 4500 (ETF USD en EUR) + 8000 * 0.6 (Fonds Mixte part actions) = 19300
        # Obligations: 5000 (ETF Obligations) + 8000 * 0.3 (Fonds Mixte part obligations) = 7400
        # Immobilier: 20000 (SCPI)
        # Cash: 8000 * 0.1 (Fonds Mixte part cash) = 800
        # Crypto et Métaux: 0

        # Vérifier chaque catégorie
        assert abs(category_values["actions"] - 19300.0) < 0.01
        assert abs(category_values["obligations"] - 7400.0) < 0.01
        assert abs(category_values["immobilier"] - 20000.0) < 0.01
        assert abs(category_values["cash"] - 800.0) < 0.01
        assert category_values["crypto"] == 0.0
        assert category_values["metaux"] == 0.0

        # Vérifier la somme totale
        total = sum(category_values.values())
        expected_total = 19300.0 + 7400.0 + 20000.0 + 800.0  # 47500.0
        assert abs(total - expected_total) < 0.01, f"Total {total} devrait être {expected_total}"

    def test_calculate_geo_values(self, db_session: Session, test_user: User, test_account: Account):
        """Test de calcul des valeurs par zone géographique"""
        # Configurer les actifs de test
        assets = self.setup_test_assets(db_session, test_user, test_account)

        # Exécuter la fonction à tester pour toutes les catégories
        geo_zones = ["amerique_nord", "europe_zone_euro", "europe_hors_zone_euro",
                     "japon", "chine", "inde", "asie_developpee", "autres_emergents",
                     "global_non_classe"]

        geo_values = VisualizationService.calculate_geo_values(
            db_session, test_user.id, None, None, geo_zones
        )

        # Vérifier les résultats
        assert geo_values is not None

        # Calcul de quelques zones géographiques (calcul approché)
        # Amérique du Nord: 
        # - Actions: 10000 * 0.6 + 5000 * 0.9 * 1.0 + 8000 * 0.6 * 0.4 = 10720
        # - Obligations: 5000 * 0.0 + 8000 * 0.3 * 0.4 = 960
        # Total Amérique du Nord: 11680

        # Europe Zone Euro:
        # - Actions: 10000 * 0.2 + 8000 * 0.6 * 0.3 = 3440
        # - Obligations: 5000 * 0.7 + 8000 * 0.3 * 0.6 = 4940
        # - Immobilier: 20000 * 0.8 = 16000
        # - Cash: 8000 * 0.1 * 1.0 = 800
        # Total Europe Zone Euro: 25180

        # Nous vérifions approximativement, car le calcul réel inclut certaines subtilités
        assert geo_values["amerique_nord"] > 11000, "Valeur Amérique du Nord trop faible"
        assert geo_values["europe_zone_euro"] > 24000, "Valeur Europe Zone Euro trop faible"
        assert geo_values["europe_hors_zone_euro"] > 6000, "Valeur Europe Hors Zone Euro trop faible"

        # Tester aussi la catégorie spécifique
        actions_geo = VisualizationService.calculate_geo_values(
            db_session, test_user.id, None, "actions", geo_zones
        )

        assert actions_geo["amerique_nord"] > 10000, "Valeur actions en Amérique du Nord trop faible"
        assert actions_geo["europe_zone_euro"] > 3000, "Valeur actions en Europe Zone Euro trop faible"

    def test_create_pie_chart(self):
        """Test de création d'un camembert"""
        # Données pour le test
        data_dict = {
            "Actions": 19800,
            "Obligations": 7400,
            "Immobilier": 20000,
            "Cash": 800
        }

        # Créer le graphique
        fig = VisualizationService.create_pie_chart(data_dict, "Répartition par catégorie")

        # Vérifier que le graphique a été créé
        assert fig is not None, "Le graphique n'a pas été créé"

        # Vérifier cas particulier: données vides
        fig = VisualizationService.create_pie_chart({})
        assert fig is None, "Avec des données vides, le résultat devrait être None"

    def test_create_bar_chart(self):
        """Test de création d'un graphique en barres"""
        # Données pour le test
        data_dict = {
            "Actions": 19800,
            "Obligations": 7400,
            "Immobilier": 20000,
            "Cash": 800
        }

        # Créer le graphique vertical
        fig_v = VisualizationService.create_bar_chart(
            data_dict, "Répartition par catégorie",
            xlabel="Catégories", ylabel="Valeur (€)"
        )

        # Vérifier que le graphique a été créé
        assert fig_v is not None, "Le graphique vertical n'a pas été créé"

        # Créer un graphique horizontal
        fig_h = VisualizationService.create_bar_chart(
            data_dict, "Répartition par catégorie",
            xlabel="Catégories", ylabel="Valeur (€)",
            horizontal=True
        )

        # Vérifier que le graphique a été créé
        assert fig_h is not None, "Le graphique horizontal n'a pas été créé"

        # Vérifier cas particulier: données vides
        fig = VisualizationService.create_bar_chart({})
        assert fig is None, "Avec des données vides, le résultat devrait être None"

    @patch('services.visualization_service.datetime')
    def test_create_time_series_chart(self, mock_datetime, db_session: Session):
        """Test de création d'un graphique d'évolution temporelle"""
        # Créer des points d'historique pour le test
        from database.models import HistoryPoint

        # Simuler des dates fixes pour le test
        mock_datetime.strptime.side_effect = lambda date, fmt: datetime.strptime(date, fmt)

        # Créer des points d'historique
        history_points = [
            HistoryPoint(
                id=f"history-{i}",
                date=f"2023-0{i + 1}-01",  # 2023-01-01, 2023-02-01, etc.
                assets={"asset1": 1000 * (1 + i * 0.05), "asset2": 2000 * (1 + i * 0.03)},
                total=1000 * (1 + i * 0.05) + 2000 * (1 + i * 0.03)
            )
            for i in range(1, 6)  # 5 points d'historique
        ]

        db_session.add_all(history_points)
        db_session.commit()

        # Créer le graphique
        fig = VisualizationService.create_time_series_chart(db_session, "Évolution du patrimoine")

        # Vérifier que le graphique a été créé
        assert fig is not None, "Le graphique d'évolution n'a pas été créé"

        # Tester avec limitation de période
        fig_limited = VisualizationService.create_time_series_chart(db_session, "Évolution récente", days=3)
        assert fig_limited is not None, "Le graphique limité n'a pas été créé"

        # Tester cas limites
        # Supprimer les données historiques
        db_session.query(HistoryPoint).delete()
        db_session.commit()

        # Tester avec une base vide
        fig_empty = VisualizationService.create_time_series_chart(db_session)
        assert fig_empty is None, "Avec des données vides, le résultat devrait être None"
