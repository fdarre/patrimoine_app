"""
Tests pour le service de gestion des actifs
"""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from database.models import Asset, User, Account
from services.asset_service import AssetService, asset_service


class TestAssetService:
    """Tests pour le service de gestion des actifs"""

    def test_get_assets(self, db_session: Session, test_user: User, test_account: Account):
        """Test de récupération des actifs"""
        # Créer un actif directement dans la base pour ce test spécifique
        test_asset_id = str(uuid.uuid4())

        # Créer l'actif test pour ce test spécifique
        new_test_asset = Asset(
            id=test_asset_id,
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Actif Pour Test Get",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 100},
            geo_allocation={"actions": {"amerique_nord": 100}},
            valeur_actuelle=1000.0,
            prix_de_revient=900.0,
            devise="EUR",
            date_maj=datetime.now().strftime("%Y-%m-%d")
        )

        db_session.add(new_test_asset)
        db_session.commit()

        # Vérifier que l'actif est bien dans la base avec une requête directe
        db_asset = db_session.query(Asset).filter(Asset.id == test_asset_id).first()
        assert db_asset is not None, "L'actif n'a pas été correctement ajouté à la base"
        assert db_asset.nom == "Actif Pour Test Get"

        # Exécuter la requête du service pour récupérer les actifs
        assets = asset_service.get_assets(db_session, test_user.id)

        # Vérifier que des actifs ont été récupérés
        assert assets is not None, "Le service ne devrait pas retourner None"
        assert isinstance(assets, list), "Le service devrait retourner une liste"
        assert len(assets) >= 1, f"Il devrait y avoir au moins un actif pour l'utilisateur {test_user.id}"

        # Vérifier que l'actif de test est dans la liste
        found_asset = False
        for asset in assets:
            if asset.id == test_asset_id:
                found_asset = True
                break

        assert found_asset, f"L'actif de test {test_asset_id} n'a pas été trouvé dans la liste des actifs"

    def test_add_asset(self, db_session: Session, test_user: User, test_account: Account):
        """Test d'ajout d'un actif"""
        # Cas 1: Ajout réussi
        asset = asset_service.add_asset(
            db_session,
            test_user.id,
            "Nouvel actif",
            test_account.id,
            "etf",
            {"actions": 80, "obligations": 20},
            {"actions": {"amerique_nord": 50, "europe_zone_euro": 50}, "obligations": {"europe_zone_euro": 100}},
            1500.0,
            1400.0,
            "EUR",
            "Notes de test",
            "Tâche à faire",
            "FR0000000001",
            None
        )
        assert asset is not None
        assert asset.nom == "Nouvel actif"
        assert asset.valeur_actuelle == 1500.0
        assert asset.prix_de_revient == 1400.0
        assert asset.isin == "FR0000000001"

        # Vérifier que l'actif est dans la base
        db_asset = db_session.query(Asset).filter(Asset.id == asset.id).first()
        assert db_asset is not None
        assert db_asset.owner_id == test_user.id
        assert db_asset.account_id == test_account.id

        # Cas 2: Ajout avec prix de revient par défaut
        asset = asset_service.add_asset(
            db_session,
            test_user.id,
            "Actif sans prix de revient",
            test_account.id,
            "etf",
            {"actions": 100},
            {"actions": {"amerique_nord": 100}},
            2000.0,
            None,
            "EUR"
        )
        assert asset is not None
        assert asset.prix_de_revient == 2000.0  # Doit être égal à la valeur actuelle

    def test_update_asset(self, db_session: Session, test_user: User, test_account: Account, test_asset: Asset):
        """Test de mise à jour d'un actif"""
        # Cas 1: Mise à jour réussie
        updated_asset = asset_service.update_asset(
            db_session,
            test_asset.id,
            "Actif mis à jour",
            test_account.id,
            "action",
            {"actions": 100},
            {"actions": {"europe_zone_euro": 100}},
            2500.0,
            2000.0,
            "USD",
            "Notes mises à jour",
            "Nouvelle tâche",
            "US0000000001",
            None
        )
        assert updated_asset is not None
        assert updated_asset.nom == "Actif mis à jour"
        assert updated_asset.type_produit == "action"
        assert updated_asset.valeur_actuelle == 2500.0
        assert updated_asset.prix_de_revient == 2000.0
        assert updated_asset.isin == "US0000000001"

        # Vérifier que les modifications sont dans la base
        db_asset = db_session.query(Asset).filter(Asset.id == test_asset.id).first()
        assert db_asset is not None
        assert db_asset.nom == "Actif mis à jour"
        assert db_asset.devise == "USD"

        # Cas 2: Actif inexistant
        updated_asset = asset_service.update_asset(
            db_session,
            "nonexistent-asset-id",
            "Actif inexistant",
            test_account.id,
            "etf",
            {"actions": 100},
            {"actions": {"amerique_nord": 100}},
            1000.0,
            900.0,
            "EUR"
        )
        assert updated_asset is None

    def test_update_manual_price(self, db_session: Session, test_asset: Asset):
        """Test de mise à jour manuelle du prix"""
        # Cas 1: Mise à jour réussie
        result = asset_service.update_manual_price(db_session, test_asset.id, 3000.0)
        assert result is True

        # Vérifier que le prix a bien été mis à jour
        db_asset = db_session.query(Asset).filter(Asset.id == test_asset.id).first()
        assert db_asset is not None
        assert db_asset.valeur_actuelle == 3000.0

        # Cas 2: Actif inexistant
        result = asset_service.update_manual_price(db_session, "nonexistent-asset-id", 1000.0)
        assert result is False

    def test_clear_todo(self, db_session: Session, test_asset: Asset):
        """Test de suppression de tâche"""
        # Ajouter une tâche d'abord
        test_asset.todo = "Tâche à faire"
        db_session.commit()

        # Cas 1: Suppression réussie
        result = asset_service.clear_todo(db_session, test_asset.id)
        assert result is True

        # Vérifier que la tâche a bien été supprimée
        db_asset = db_session.query(Asset).filter(Asset.id == test_asset.id).first()
        assert db_asset is not None
        assert db_asset.todo == ""

        # Cas 2: Actif inexistant
        result = asset_service.clear_todo(db_session, "nonexistent-asset-id")
        assert result is False

    def test_calculate_performance(self, db_session: Session, test_asset: Asset):
        """Test de calcul de performance"""
        # Mettre à jour les valeurs pour le test
        test_asset.valeur_actuelle = 1100.0
        test_asset.prix_de_revient = 1000.0
        db_session.commit()

        # Calculer la performance
        performance = AssetService.calculate_performance(test_asset)

        assert performance is not None
        assert "value" in performance
        assert "percent" in performance
        assert "is_positive" in performance

        assert performance["value"] == 100.0
        assert performance["percent"] == 10.0
        assert performance["is_positive"] is True

        # Cas de perte
        test_asset.valeur_actuelle = 900.0
        db_session.commit()

        performance = AssetService.calculate_performance(test_asset)

        assert performance["value"] == -100.0
        assert performance["percent"] == -10.0
        assert performance["is_positive"] is False