"""
Service de gestion des actifs avec SQLAlchemy
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime
import uuid
import json

from database.models import Asset, Account, Bank, User

class AssetService:
    """Service pour la gestion des actifs avec SQLAlchemy"""

    @staticmethod
    def get_assets(
            db: Session,
            user_id: str,
            account_id: Optional[str] = None,
            category: Optional[str] = None
    ) -> List[Asset]:
        """
        Récupère tous les actifs d'un utilisateur avec filtres optionnels

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            account_id: ID du compte (optionnel)
            category: Catégorie d'actif (optionnel)

        Returns:
            Liste des actifs
        """
        query = db.query(Asset).filter(Asset.owner_id == user_id)

        if account_id:
            query = query.filter(Asset.account_id == account_id)

        if category:
            # Filtrer par catégorie (nécessite une analyse JSON)
            # Note: Cette implémentation peut varier selon la base de données
            query = query.filter(Asset.allocation.contains({category: {"$exists": True}}))

        return query.all()

    @staticmethod
    def find_asset_by_id(db: Session, asset_id: str) -> Optional[Asset]:
        """
        Trouve un actif par son ID

        Args:
            db: Session de base de données
            asset_id: ID de l'actif recherché

        Returns:
            L'actif trouvé ou None
        """
        return db.query(Asset).filter(Asset.id == asset_id).first()

    @staticmethod
    def add_asset(
            db: Session,
            user_id: str,
            nom: str,
            compte_id: str,
            type_produit: str,
            allocation: Dict[str, float],
            geo_allocation: Dict[str, Dict[str, float]],
            valeur_actuelle: float,
            prix_de_revient: Optional[float] = None,
            devise: str = "EUR",
            notes: str = "",
            todo: str = "",
            composants: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Asset]:
        """
        Ajoute un nouvel actif

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur propriétaire
            nom: Nom de l'actif
            compte_id: ID du compte associé
            type_produit: Type de produit
            allocation: Répartition par catégorie
            geo_allocation: Répartition géographique par catégorie
            valeur_actuelle: Valeur actuelle
            prix_de_revient: Prix de revient (si None, utilise valeur_actuelle)
            devise: Devise
            notes: Notes
            todo: Tâche(s) à faire
            composants: Liste des composants (pour actifs composites)

        Returns:
            Le nouvel actif créé ou None
        """
        if prix_de_revient is None:
            prix_de_revient = valeur_actuelle

        # Déterminer la catégorie principale (celle avec le pourcentage le plus élevé)
        categorie = max(allocation.items(), key=lambda x: x[1])[0] if allocation else "autre"

        # Créer le nouvel actif
        new_asset = Asset(
            id=str(uuid.uuid4()),
            owner_id=user_id,
            account_id=compte_id,
            nom=nom,
            type_produit=type_produit,
            categorie=categorie,
            allocation=allocation,
            geo_allocation=geo_allocation,
            valeur_actuelle=valeur_actuelle,
            prix_de_revient=prix_de_revient,
            devise=devise,
            date_maj=datetime.now().strftime("%Y-%m-%d"),
            notes=notes,
            todo=todo,
            composants=composants if composants else []
        )

        # Ajouter et valider
        db.add(new_asset)
        db.commit()
        db.refresh(new_asset)

        return new_asset

    @staticmethod
    def update_asset(
            db: Session,
            asset_id: str,
            nom: str,
            compte_id: str,
            type_produit: str,
            allocation: Dict[str, float],
            geo_allocation: Dict[str, Dict[str, float]],
            valeur_actuelle: float,
            prix_de_revient: float,
            devise: str = "EUR",
            notes: str = "",
            todo: str = "",
            composants: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Asset]:
        """
        Met à jour un actif existant

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à mettre à jour
            nom: Nouveau nom
            compte_id: Nouveau compte
            type_produit: Nouveau type
            allocation: Nouvelle allocation
            geo_allocation: Nouvelle répartition géographique
            valeur_actuelle: Nouvelle valeur
            prix_de_revient: Nouveau prix de revient
            devise: Nouvelle devise
            notes: Nouvelles notes
            todo: Nouvelle(s) tâche(s)
            composants: Nouveaux composants

        Returns:
            L'actif mis à jour ou None
        """
        # Récupérer l'actif
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return None

        # Déterminer la catégorie principale (celle avec le pourcentage le plus élevé)
        categorie = max(allocation.items(), key=lambda x: x[1])[0] if allocation else "autre"

        # Mettre à jour les champs
        asset.nom = nom
        asset.account_id = compte_id
        asset.type_produit = type_produit
        asset.categorie = categorie
        asset.allocation = allocation
        asset.geo_allocation = geo_allocation
        asset.valeur_actuelle = float(valeur_actuelle)
        asset.prix_de_revient = float(prix_de_revient)
        asset.devise = devise
        asset.date_maj = datetime.now().strftime("%Y-%m-%d")
        asset.notes = notes
        asset.todo = todo

        if composants is not None:
            asset.composants = composants

        # Valider les modifications
        db.commit()
        db.refresh(asset)

        return asset

    @staticmethod
    def delete_asset(db: Session, asset_id: str) -> bool:
        """
        Supprime un actif

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à supprimer

        Returns:
            True si l'actif a été supprimé, False sinon
        """
        # Récupérer l'actif
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return False

        # Vérifier si l'actif est un composant d'autres actifs
        assets_with_component = db.query(Asset).filter(
            Asset.composants.contains([{"asset_id": asset_id}])
        ).first()

        if assets_with_component:
            # Ne pas supprimer un actif utilisé comme composant
            return False

        # Supprimer l'actif
        db.delete(asset)
        db.commit()

        return True

    @staticmethod
    def is_used_as_component(db: Session, asset_id: str) -> bool:
        """
        Vérifie si un actif est utilisé comme composant dans d'autres actifs

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à vérifier

        Returns:
            True si l'actif est utilisé comme composant, False sinon
        """
        # Rechercher les actifs qui contiennent cet ID dans leurs composants
        assets_with_component = db.query(Asset).filter(
            Asset.composants.contains([{"asset_id": asset_id}])
        ).first()

        return assets_with_component is not None

    @staticmethod
    def get_assets_dataframe(
            db: Session,
            user_id: str,
            account_id: Optional[str] = None,
            category: Optional[str] = None,
            bank_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Crée un DataFrame Pandas avec les actifs filtrés

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            account_id: Filtre par ID de compte (optionnel)
            category: Filtre par catégorie (optionnel)
            bank_id: Filtre par ID de banque (optionnel)

        Returns:
            DataFrame Pandas des actifs filtrés
        """
        data = []

        # Construire la requête avec les jointures appropriées
        query = db.query(Asset, Account, Bank).join(
            Account, Asset.account_id == Account.id
        ).join(
            Bank, Account.bank_id == Bank.id
        ).filter(
            Asset.owner_id == user_id
        )

        # Appliquer les filtres
        if account_id:
            query = query.filter(Asset.account_id == account_id)

        if bank_id:
            query = query.filter(Account.bank_id == bank_id)

        if category:
            # Filtrer par catégorie (nécessite une analyse JSON)
            query = query.filter(Asset.allocation.contains({category: {"$exists": True}}))

        # Exécuter la requête
        results = query.all()

        for asset, account, bank in results:
            # Calculer la plus-value
            pv = asset.valeur_actuelle - asset.prix_de_revient
            pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
            pv_class = "positive" if pv >= 0 else "negative"

            # Formatter les valeurs avec séparateurs de milliers
            formatted_value = f"{asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " ")
            formatted_pv = f"{pv:,.2f} {asset.devise} ({pv_percent:.2f}%)".replace(",", " ")

            # Créer une représentation des allocations (ex: "Actions 60% / Obligations 40%")
            allocation_str = " / ".join(f"{cat.capitalize()} {pct}%" for cat, pct in asset.allocation.items())

            # Indicateur d'actif composite
            is_composite = len(asset.composants) > 0
            composite_indicator = "✓" if is_composite else ""

            data.append([
                asset.id,
                asset.nom,
                asset.categorie.capitalize(),
                allocation_str,
                asset.type_produit,
                formatted_value,
                f'<span class="{pv_class}">{formatted_pv}</span>',
                bank.nom,
                account.libelle,
                composite_indicator
            ])

        return pd.DataFrame(data, columns=["ID", "Nom", "Catégorie", "Allocation", "Type", "Valeur",
                                          "Plus-value", "Banque", "Compte", "Composite"])

    @staticmethod
    def calculate_effective_allocation(db: Session, asset_id: str) -> Dict[str, float]:
        """
        Calcule l'allocation effective d'un actif composite en tenant compte de ses composants

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à analyser

        Returns:
            Dictionnaire avec les allocations effectives par catégorie
        """
        # Récupérer l'actif
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset or not asset.composants:
            return asset.allocation if asset else {}

        # Initialiser avec l'allocation directe
        effective_allocation = {cat: 0.0 for cat in asset.allocation.keys()}

        # Calculer le pourcentage direct
        direct_percentage = 100 - sum(comp.get("percentage", 0) for comp in asset.composants)

        # Ajouter l'allocation directe
        for category, percentage in asset.allocation.items():
            effective_allocation[category] += (percentage * direct_percentage / 100)

        # Ajouter les allocations des composants
        for component in asset.composants:
            component_id = component.get("asset_id")
            component_percentage = component.get("percentage", 0)

            # Récupérer l'actif composant
            component_asset = db.query(Asset).filter(Asset.id == component_id).first()
            if not component_asset:
                continue

            # Calculer l'allocation effective du composant (récursion)
            component_allocation = AssetService.calculate_effective_allocation(db, component_id)

            # Ajouter à l'allocation effective
            for category, percentage in component_allocation.items():
                if category not in effective_allocation:
                    effective_allocation[category] = 0.0
                effective_allocation[category] += (percentage * component_percentage / 100)

        return effective_allocation

    @staticmethod
    def calculate_effective_geo_allocation(
            db: Session,
            asset_id: str,
            category: Optional[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcule la répartition géographique effective d'un actif composite

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à analyser
            category: Catégorie spécifique à calculer (optionnel)

        Returns:
            Dictionnaire avec les répartitions géographiques effectives par catégorie
        """
        # Récupérer l'actif
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset or not asset.composants:
            if category and asset:
                return {category: asset.geo_allocation.get(category, {})}
            return asset.geo_allocation if asset else {}

        # Initialiser avec les catégories d'allocation de l'actif
        effective_geo = {}
        categories = [category] if category else asset.allocation.keys()

        for cat in categories:
            if cat not in effective_geo:
                effective_geo[cat] = {zone: 0.0 for zone in asset.geo_allocation.get(cat, {}).keys()}

        # D'abord, ajouter la répartition directe de l'actif principal
        direct_percentage = 100 - sum(comp.get("percentage", 0) for comp in asset.composants)

        for cat in categories:
            cat_percentage = asset.allocation.get(cat, 0) * direct_percentage / 100
            if cat_percentage > 0:
                for zone, zone_pct in asset.geo_allocation.get(cat, {}).items():
                    if zone not in effective_geo[cat]:
                        effective_geo[cat][zone] = 0.0
                    effective_geo[cat][zone] += (zone_pct * cat_percentage / 100)

        # Ensuite, ajouter les répartitions des composants
        for component in asset.composants:
            component_id = component.get("asset_id")
            component_percentage = component.get("percentage", 0)

            # Récupérer l'actif composant
            component_asset = db.query(Asset).filter(Asset.id == component_id).first()
            if not component_asset:
                continue

            # Calculer la répartition géographique effective du composant (récursion)
            component_geo = AssetService.calculate_effective_geo_allocation(db, component_id)

            for cat in categories:
                if cat not in component_asset.allocation:
                    continue

                cat_component_percentage = component_asset.allocation.get(cat, 0) * component_percentage / 100

                for zone, zone_pct in component_geo.get(cat, {}).items():
                    if cat not in effective_geo:
                        effective_geo[cat] = {}
                    if zone not in effective_geo[cat]:
                        effective_geo[cat][zone] = 0.0
                    effective_geo[cat][zone] += (zone_pct * cat_component_percentage / 100)

        return effective_geo