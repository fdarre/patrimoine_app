"""
Tests pour le service de gestion des modèles (templates)
"""
from sqlalchemy.orm import Session

from database.models import Asset, User, Account
from services.template_service import template_service


class TestTemplateService:
    """Tests pour le service de gestion des modèles (templates)"""

    def test_create_template(self, db_session: Session, test_asset: Asset):
        """Test de création d'un modèle"""
        # Cas 1: Création réussie
        result = template_service.create_template(db_session, test_asset.id, "Modèle Test")
        assert result is True

        # Vérifier que l'actif a bien été marqué comme modèle
        db_asset = db_session.query(Asset).filter(Asset.id == test_asset.id).first()
        assert db_asset is not None
        assert db_asset.is_template is True
        assert db_asset.template_name == "Modèle Test"

        # Cas 2: Actif inexistant
        result = template_service.create_template(db_session, "nonexistent-asset-id", "Modèle Inexistant")
        assert result is False

    def test_link_to_template(self, db_session: Session, test_user: User, test_account: Account, test_asset: Asset):
        """Test de liaison d'un actif à un modèle"""
        # Créer un actif pour le test
        asset_to_link = Asset(
            id="asset-to-link",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Actif à Lier",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 80, "obligations": 20},
            geo_allocation={"actions": {"amerique_nord": 50, "europe_zone_euro": 50}},
            valeur_actuelle=1500.0,
            prix_de_revient=1400.0,
            devise="EUR",
            date_maj="2025-05-19"
        )
        db_session.add(asset_to_link)
        db_session.commit()

        # Marquer l'actif de test comme modèle
        template_service.create_template(db_session, test_asset.id, "Modèle Test")

        # Cas 1: Liaison réussie avec synchronisation
        result = template_service.link_to_template(db_session, "asset-to-link", test_asset.id, True)
        assert result is True

        # Vérifier que l'actif a bien été lié
        db_asset = db_session.query(Asset).filter(Asset.id == "asset-to-link").first()
        assert db_asset is not None
        assert db_asset.template_id == test_asset.id
        assert db_asset.sync_allocations is True
        assert db_asset.allocation == test_asset.allocation
        assert db_asset.geo_allocation == test_asset.geo_allocation

        # Cas 2: Liaison réussie sans synchronisation
        # Créer un autre actif
        asset_to_link2 = Asset(
            id="asset-to-link2",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Actif à Lier 2",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 100},
            geo_allocation={"actions": {"amerique_nord": 100}},
            valeur_actuelle=2000.0,
            prix_de_revient=1900.0,
            devise="EUR",
            date_maj="2025-05-19"
        )
        db_session.add(asset_to_link2)
        db_session.commit()

        result = template_service.link_to_template(db_session, "asset-to-link2", test_asset.id, False)
        assert result is True

        # Vérifier que l'actif a bien été lié mais pas synchronisé
        db_asset = db_session.query(Asset).filter(Asset.id == "asset-to-link2").first()
        assert db_asset is not None
        assert db_asset.template_id == test_asset.id
        assert db_asset.sync_allocations is False
        assert db_asset.allocation != test_asset.allocation  # Pas synchronisé

        # Cas 3: Actif ou modèle inexistant
        result = template_service.link_to_template(db_session, "nonexistent-asset-id", test_asset.id)
        assert result is False

        result = template_service.link_to_template(db_session, "asset-to-link", "nonexistent-template-id")
        assert result is False

    def test_unlink_from_template(self, db_session: Session, test_user: User, test_account: Account, test_asset: Asset):
        """Test de déliaison d'un actif d'un modèle"""
        # Créer un actif pour le test
        asset_to_unlink = Asset(
            id="asset-to-unlink",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Actif à Délier",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 100},
            valeur_actuelle=2000.0,
            prix_de_revient=1900.0,
            devise="EUR",
            date_maj="2025-05-19",
            template_id=test_asset.id,
            sync_allocations=True
        )
        db_session.add(asset_to_unlink)
        db_session.commit()

        # Cas 1: Déliaison réussie
        result = template_service.unlink_from_template(db_session, "asset-to-unlink")
        assert result is True

        # Vérifier que l'actif a bien été délié
        db_asset = db_session.query(Asset).filter(Asset.id == "asset-to-unlink").first()
        assert db_asset is not None
        assert db_asset.template_id is None
        assert db_asset.sync_allocations is False

        # Cas 2: Actif inexistant ou non lié
        result = template_service.unlink_from_template(db_session, "nonexistent-asset-id")
        assert result is False

        result = template_service.unlink_from_template(db_session, test_asset.id)  # Pas lié à un modèle
        assert result is False

    def test_propagate_template_changes(self, db_session: Session, test_user: User, test_account: Account,
                                        test_asset: Asset):
        """Test de propagation des modifications d'un modèle"""
        # Créer un modèle pour le test
        template = Asset(
            id="template-for-propagation",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Modèle pour Propagation",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 70, "obligations": 30},
            geo_allocation={"actions": {"amerique_nord": 70, "europe_zone_euro": 30}},
            valeur_actuelle=1000.0,
            prix_de_revient=900.0,
            devise="EUR",
            date_maj="2025-05-19",
            is_template=True,
            template_name="Modèle de Propagation"
        )
        db_session.add(template)
        db_session.commit()

        # Créer des actifs liés
        asset_linked1 = Asset(
            id="asset-linked1",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Actif Lié 1",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 70, "obligations": 30},
            geo_allocation={"actions": {"amerique_nord": 70, "europe_zone_euro": 30}},
            valeur_actuelle=1500.0,
            prix_de_revient=1400.0,
            devise="EUR",
            date_maj="2025-05-19",
            template_id="template-for-propagation",
            sync_allocations=True
        )

        asset_linked2 = Asset(
            id="asset-linked2",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Actif Lié 2",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 70, "obligations": 30},
            geo_allocation={"actions": {"amerique_nord": 70, "europe_zone_euro": 30}},
            valeur_actuelle=2000.0,
            prix_de_revient=1900.0,
            devise="EUR",
            date_maj="2025-05-19",
            template_id="template-for-propagation",
            sync_allocations=False  # Ne doit pas être synchronisé
        )

        asset_linked3 = Asset(
            id="asset-linked3",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Actif Lié 3",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 70, "obligations": 30},
            geo_allocation={"actions": {"amerique_nord": 70, "europe_zone_euro": 30}},
            valeur_actuelle=2500.0,
            prix_de_revient=2400.0,
            devise="EUR",
            date_maj="2025-05-19",
            template_id="template-for-propagation",
            sync_allocations=True
        )

        db_session.add_all([asset_linked1, asset_linked2, asset_linked3])
        db_session.commit()

        # Modifier le modèle
        template = db_session.query(Asset).filter(Asset.id == "template-for-propagation").first()
        template.allocation = {"actions": 60, "obligations": 20, "cash": 20}
        template.geo_allocation = {"actions": {"amerique_nord": 50, "europe_zone_euro": 50}}
        db_session.commit()

        # Cas 1: Propagation réussie
        count = template_service.propagate_template_changes(db_session, "template-for-propagation")
        assert count == 2  # Seulement les actifs avec sync_allocations=True

        # Vérifier que les actifs ont bien été mis à jour
        asset1 = db_session.query(Asset).filter(Asset.id == "asset-linked1").first()
        assert asset1 is not None
        assert asset1.allocation == template.allocation
        assert asset1.geo_allocation == template.geo_allocation

        asset3 = db_session.query(Asset).filter(Asset.id == "asset-linked3").first()
        assert asset3 is not None
        assert asset3.allocation == template.allocation
        assert asset3.geo_allocation == template.geo_allocation

        # L'actif avec sync_allocations=False ne doit pas être mis à jour
        asset2 = db_session.query(Asset).filter(Asset.id == "asset-linked2").first()
        assert asset2 is not None
        assert asset2.allocation != template.allocation

        # Cas 2: Modèle inexistant
        count = template_service.propagate_template_changes(db_session, "nonexistent-template-id")
        assert count == 0

    def test_get_templates(self, db_session: Session, test_user: User):
        """Test de récupération des modèles"""
        # Créer un modèle pour le test
        template = Asset(
            id="template-for-get",
            owner_id=test_user.id,
            nom="Modèle pour Récupération",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 100},
            valeur_actuelle=1000.0,
            prix_de_revient=900.0,
            devise="EUR",
            date_maj="2025-05-19",
            is_template=True,
            template_name="Modèle de Récupération"
        )
        db_session.add(template)
        db_session.commit()

        # Récupérer les modèles
        templates = template_service.get_templates(db_session, test_user.id)

        # Vérifier que la liste n'est pas vide
        assert len(templates) >= 1

        # Vérifier que le modèle créé est dans la liste
        template_found = False
        for tmpl in templates:
            if tmpl.id == "template-for-get":
                template_found = True
                assert tmpl.template_name == "Modèle de Récupération"
                break

        assert template_found

    def test_get_linked_assets(self, db_session: Session, test_user: User, test_account: Account):
        """Test de récupération des actifs liés à un modèle"""
        # Créer un modèle pour le test
        template = Asset(
            id="template-for-linked",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Modèle pour Actifs Liés",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 100},
            valeur_actuelle=1000.0,
            prix_de_revient=900.0,
            devise="EUR",
            date_maj="2025-05-19",
            is_template=True,
            template_name="Modèle pour Actifs Liés"
        )
        db_session.add(template)

        # Créer des actifs liés
        asset_linked1 = Asset(
            id="asset-linked-test1",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Actif Lié Test 1",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 100},
            valeur_actuelle=1500.0,
            prix_de_revient=1400.0,
            devise="EUR",
            date_maj="2025-05-19",
            template_id="template-for-linked"
        )

        asset_linked2 = Asset(
            id="asset-linked-test2",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Actif Lié Test 2",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 100},
            valeur_actuelle=2000.0,
            prix_de_revient=1900.0,
            devise="EUR",
            date_maj="2025-05-19",
            template_id="template-for-linked"
        )

        db_session.add_all([asset_linked1, asset_linked2])
        db_session.commit()

        # Récupérer les actifs liés
        linked_assets = template_service.get_linked_assets(db_session, "template-for-linked")

        # Vérifier que la liste n'est pas vide
        assert len(linked_assets) == 2

        # Vérifier que les actifs liés sont dans la liste
        assert any(asset.id == "asset-linked-test1" for asset in linked_assets)
        assert any(asset.id == "asset-linked-test2" for asset in linked_assets)

    def test_get_template_candidates(self, db_session: Session, test_user: User, test_account: Account):
        """Test de récupération des candidats pour devenir modèles"""
        # Créer des actifs pour le test
        candidate1 = Asset(
            id="candidate1",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Candidat 1",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 100},
            valeur_actuelle=1500.0,
            prix_de_revient=1400.0,
            devise="EUR",
            date_maj="2025-05-19"
        )

        candidate2 = Asset(
            id="candidate2",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Candidat 2",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 100},
            valeur_actuelle=2000.0,
            prix_de_revient=1900.0,
            devise="EUR",
            date_maj="2025-05-19"
        )

        # Un actif déjà modèle
        template = Asset(
            id="template-candidate",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Modèle Candidat",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 100},
            valeur_actuelle=1000.0,
            prix_de_revient=900.0,
            devise="EUR",
            date_maj="2025-05-19",
            is_template=True,
            template_name="Modèle Candidat"
        )

        # Un actif déjà lié à un modèle
        linked_asset = Asset(
            id="linked-candidate",
            owner_id=test_user.id,
            account_id=test_account.id,
            nom="Actif Lié Candidat",
            type_produit="etf",
            categorie="actions",
            allocation={"actions": 100},
            valeur_actuelle=2500.0,
            prix_de_revient=2400.0,
            devise="EUR",
            date_maj="2025-05-19",
            template_id="template-candidate"
        )

        db_session.add_all([candidate1, candidate2, template, linked_asset])
        db_session.commit()

        # Récupérer les candidats
        candidates = template_service.get_template_candidates(db_session, test_user.id)

        # Vérifier que les candidats valides sont dans la liste
        assert any(asset.id == "candidate1" for asset in candidates)
        assert any(asset.id == "candidate2" for asset in candidates)

        # Vérifier que les actifs déjà modèles ou liés ne sont pas dans la liste
        assert not any(asset.id == "template-candidate" for asset in candidates)
        assert not any(asset.id == "linked-candidate" for asset in candidates)
