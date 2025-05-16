"""
Service de gestion des actifs avec SQLAlchemy
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime
import uuid
import json
from services.currency_service import CurrencyService
from services.price_service import PriceService

from database.models import Asset, Account, Bank, User
from sqlalchemy import String

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
            composants: Optional[List[Dict[str, Any]]] = None,
            isin: Optional[str] = None,
            ounces: Optional[float] = None
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
            isin: Code ISIN (optionnel)
            ounces: Nombre d'onces pour les métaux précieux (optionnel)

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
            composants=composants if composants else [],
            isin=isin,
            ounces=ounces,
            exchange_rate=1.0 if devise == "EUR" else None,
            value_eur=valeur_actuelle if devise == "EUR" else None
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
            composants: Optional[List[Dict[str, Any]]] = None,
            isin: Optional[str] = None,
            ounces: Optional[float] = None
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
            isin: Code ISIN (optionnel)
            ounces: Nombre d'onces pour les métaux précieux (optionnel)

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
        asset.isin = isin
        asset.ounces = ounces

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
            Asset.composants.cast(String).contains("%asset_id%")
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
            Asset.composants.cast(String).contains("%asset_id%")
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

    @staticmethod
    def sync_currency_rates(db: Session, asset_id: Optional[str] = None) -> int:
        """
        Synchronise les taux de change pour un actif ou tous les actifs

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à synchroniser (tous les actifs si None)

        Returns:
            Nombre d'actifs mis à jour
        """
        # Récupérer les taux de change actuels
        rates = CurrencyService.get_exchange_rates()

        # Préparer la requête
        query = db.query(Asset)
        if asset_id:
            query = query.filter(Asset.id == asset_id)
        else:
            # Exclure les actifs en EUR
            query = query.filter(Asset.devise != "EUR")

        assets = query.all()
        updated_count = 0

        for asset in assets:
            if asset.devise != "EUR":
                try:
                    # Récupérer le taux de change
                    exchange_rate = rates.get(asset.devise)

                    if exchange_rate and exchange_rate > 0:
                        # Mettre à jour l'actif
                        asset.exchange_rate = exchange_rate
                        asset.value_eur = asset.valeur_actuelle / exchange_rate
                        asset.last_rate_sync = datetime.now()
                        asset.sync_error = None
                        updated_count += 1
                    else:
                        asset.sync_error = f"Taux de change non disponible pour {asset.devise}"
                except Exception as e:
                    asset.sync_error = str(e)
            else:
                # Pour les actifs en EUR, le taux est toujours 1
                asset.exchange_rate = 1.0
                asset.value_eur = asset.valeur_actuelle
                asset.last_rate_sync = datetime.now()
                asset.sync_error = None
                updated_count += 1

        # Sauvegarder les modifications
        db.commit()

        return updated_count

    @staticmethod
    def sync_price_by_isin(db: Session, asset_id: Optional[str] = None) -> int:
        """
        Synchronise les prix à partir des codes ISIN pour un actif ou tous les actifs

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à synchroniser (tous les actifs si None)

        Returns:
            Nombre d'actifs mis à jour
        """
        # Préparer la requête
        query = db.query(Asset)
        if asset_id:
            query = query.filter(Asset.id == asset_id)
        else:
            # Uniquement les actifs avec un ISIN
            query = query.filter(Asset.isin != None)

        assets = query.all()
        updated_count = 0

        for asset in assets:
            if asset.isin:
                try:
                    # Récupérer le prix
                    price = PriceService.get_price_by_isin(asset.isin)

                    if price and price > 0:
                        # Mettre à jour l'actif
                        asset.valeur_actuelle = price
                        asset.last_price_sync = datetime.now()
                        asset.sync_error = None

                        # Mettre à jour la valeur en EUR
                        if asset.devise == "EUR":
                            asset.value_eur = price
                        elif asset.exchange_rate and asset.exchange_rate > 0:
                            asset.value_eur = price / asset.exchange_rate

                        updated_count += 1
                    else:
                        asset.sync_error = f"Prix non disponible pour ISIN {asset.isin}"
                except Exception as e:
                    asset.sync_error = str(e)

        # Sauvegarder les modifications
        db.commit()

        return updated_count

    @staticmethod
    def sync_metal_prices(db: Session, asset_id: Optional[str] = None) -> int:
        """
        Synchronise les prix des métaux précieux pour un actif ou tous les actifs de type métal

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à synchroniser (tous les actifs métal si None)

        Returns:
            Nombre d'actifs mis à jour
        """
        # Préparer la requête
        query = db.query(Asset)
        if asset_id:
            query = query.filter(Asset.id == asset_id)
        else:
            # Uniquement les actifs de type métal avec des onces définies
            query = query.filter(Asset.type_produit == "metal", Asset.ounces != None)

        assets = query.all()
        updated_count = 0

        for asset in assets:
            if asset.type_produit == "metal" and asset.ounces:
                try:
                    # Déterminer le type de métal (or par défaut)
                    metal_type = "gold"  # Par défaut
                    if "silver" in asset.nom.lower():
                        metal_type = "silver"
                    elif "platinum" in asset.nom.lower():
                        metal_type = "platinum"
                    elif "palladium" in asset.nom.lower():
                        metal_type = "palladium"

                    # Récupérer le prix par once
                    price_per_ounce = PriceService.get_metal_price(metal_type)

                    if price_per_ounce and price_per_ounce > 0:
                        # Calculer la valeur totale
                        total_value = price_per_ounce * asset.ounces

                        # Mettre à jour l'actif
                        asset.valeur_actuelle = total_value
                        asset.last_price_sync = datetime.now()
                        asset.sync_error = None

                        # Mettre à jour la valeur en EUR
                        if asset.devise == "EUR":
                            asset.value_eur = total_value
                        elif asset.exchange_rate and asset.exchange_rate > 0:
                            asset.value_eur = total_value / asset.exchange_rate

                        updated_count += 1
                    else:
                        asset.sync_error = f"Prix non disponible pour {metal_type}"
                except Exception as e:
                    asset.sync_error = str(e)

        # Sauvegarder les modifications
        db.commit()

        return updated_count

    @staticmethod
    def update_manual_price(db: Session, asset_id: str, new_price: float) -> bool:
        """
        Met à jour manuellement le prix d'un actif

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à mettre à jour
            new_price: Nouveau prix

        Returns:
            True si la mise à jour a réussi, False sinon
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return False

        try:
            # Mettre à jour le prix
            asset.valeur_actuelle = new_price
            asset.last_price_sync = datetime.now()
            asset.sync_error = None

            # Mettre à jour la valeur en EUR
            if asset.devise == "EUR":
                asset.value_eur = new_price
            elif asset.exchange_rate and asset.exchange_rate > 0:
                asset.value_eur = new_price / asset.exchange_rate

            # Sauvegarder les modifications
            db.commit()

            return True
        except Exception:
            db.rollback()
            return False

    @staticmethod
    def update_manual_exchange_rate(db: Session, asset_id: str, new_rate: float) -> bool:
        """
        Met à jour manuellement le taux de change d'un actif

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à mettre à jour
            new_rate: Nouveau taux de change

        Returns:
            True si la mise à jour a réussi, False sinon
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return False

        try:
            # Mettre à jour le taux de change
            asset.exchange_rate = new_rate
            asset.last_rate_sync = datetime.now()
            asset.sync_error = None

            # Mettre à jour la valeur en EUR
            asset.value_eur = asset.valeur_actuelle / new_rate

            # Sauvegarder les modifications
            db.commit()

            return True
        except Exception:
            db.rollback()
            return False

    @staticmethod
    def add_component(db: Session, asset_id: str, component_id: str, percentage: float) -> bool:
        """
        Ajoute un composant à un actif

        Args:
            db: Session de base de données
            asset_id: ID de l'actif principal
            component_id: ID de l'actif à ajouter comme composant
            percentage: Pourcentage du composant

        Returns:
            True si l'ajout a réussi, False sinon
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return False

        # Vérifier si le composant existe
        component = db.query(Asset).filter(Asset.id == component_id).first()
        if not component:
            return False

        try:
            # Vérifier si le composant existe déjà dans la liste
            if asset.composants is None:
                asset.composants = []

            # Vérifier si le composant existe déjà
            for comp in asset.composants:
                if comp.get("asset_id") == component_id:
                    # Mettre à jour le pourcentage
                    comp["percentage"] = percentage
                    db.commit()
                    return True

            # Ajouter le nouveau composant
            asset.composants.append({
                "asset_id": component_id,
                "percentage": percentage
            })

            # Sauvegarder les modifications
            db.commit()

            return True
        except Exception:
            db.rollback()
            return False

    @staticmethod
    def remove_component(db: Session, asset_id: str, component_id: str) -> bool:
        """
        Supprime un composant d'un actif

        Args:
            db: Session de base de données
            asset_id: ID de l'actif principal
            component_id: ID du composant à supprimer

        Returns:
            True si la suppression a réussi, False sinon
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset or not asset.composants:
            return False

        try:
            # Filtrer les composants pour exclure celui à supprimer
            asset.composants = [comp for comp in asset.composants if comp.get("asset_id") != component_id]

            # Sauvegarder les modifications
            db.commit()

            return True
        except Exception:
            db.rollback()
            return False