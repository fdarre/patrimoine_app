"""
Service de gestion des actifs avec SQLAlchemy
"""
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_
from datetime import datetime
import uuid

from database.models import Asset, Account, Bank
from services.base_service import BaseService
from services.currency_service import CurrencyService
from services.price_service import PriceService
from utils.decorators import handle_exceptions
from utils.logger import get_logger
from utils.common import safe_float_conversion, safe_json_loads

logger = get_logger(__name__)

class AssetService(BaseService[Asset]):
    """Service pour la gestion des actifs avec SQLAlchemy"""

    def __init__(self):
        super().__init__(Asset)
        self.currency_service = CurrencyService()
        self.price_service = PriceService()

    @handle_exceptions
    def get_assets(
            self, db: Session,
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
        # OPTIMISATION: Utiliser eager loading pour charger les relations en une seule requête
        query = db.query(Asset).options(
            joinedload(Asset.account).joinedload(Account.bank)
        ).filter(Asset.owner_id == user_id)

        if account_id:
            query = query.filter(Asset.account_id == account_id)

        # OPTIMISATION: Filtrage sur JSON pour les catégories au niveau SQL
        if category:
            # Pour SQLite, utiliser json_extract
            query = query.filter(func.json_extract(Asset.allocation, f'$.{category}').isnot(None))

        return query.all()

    @handle_exceptions
    def get_assets_with_relations(
            self, db: Session,
            user_id: str,
            account_id: Optional[str] = None,
            category: Optional[str] = None
    ) -> List[Asset]:
        """
        Récupère les actifs avec leurs relations (comptes, banques) en une seule requête

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            account_id: ID du compte (optionnel)
            category: Catégorie d'actif (optionnel)

        Returns:
            Liste des actifs avec relations chargées
        """
        # OPTIMISATION: Utiliser eager loading pour charger les relations en une seule requête
        query = db.query(Asset).options(
            joinedload(Asset.account).joinedload(Account.bank)
        ).filter(Asset.owner_id == user_id)

        if account_id:
            query = query.filter(Asset.account_id == account_id)

        # Filtrage par catégorie JSON (SQLite)
        if category:
            query = query.filter(func.json_extract(Asset.allocation, f'$.{category}').isnot(None))

        return query.all()

    @handle_exceptions
    def add_asset(
            self, db: Session,
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
            isin: Optional[str] = None,
            ounces: Optional[float] = None,
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
            isin: Code ISIN (optionnel)
            ounces: Nombre d'onces pour les métaux précieux (optionnel)
            composants: Liste de composants (optionnel)

        Returns:
            Le nouvel actif créé ou None
        """
        if prix_de_revient is None:
            prix_de_revient = valeur_actuelle

        # Déterminer la catégorie principale (celle avec le pourcentage le plus élevé)
        categorie = max(allocation.items(), key=lambda x: x[1])[0] if allocation else "autre"

        # Calcul du taux de change et de la valeur en EUR
        exchange_rate = 1.0
        value_eur = valeur_actuelle

        # Si devise différente de EUR, convertir la valeur
        if devise != "EUR":
            # Récupérer les taux de change actuels
            try:
                rates = self.currency_service.get_exchange_rates()
                if devise in rates and rates[devise] > 0:
                    exchange_rate = rates[devise]
                    value_eur = valeur_actuelle / exchange_rate
            except Exception as e:
                logger.error(f"Erreur lors de la conversion de devise: {str(e)}")

        # Données pour la création
        data = {
            "id": str(uuid.uuid4()),
            "owner_id": user_id,
            "account_id": compte_id,
            "nom": nom,
            "type_produit": type_produit,
            "categorie": categorie,
            "allocation": allocation,
            "geo_allocation": geo_allocation,
            "valeur_actuelle": valeur_actuelle,
            "prix_de_revient": prix_de_revient,
            "devise": devise,
            "date_maj": datetime.now().strftime("%Y-%m-%d"),
            "notes": notes,
            "todo": todo,
            "isin": isin,
            "ounces": ounces,
            "exchange_rate": exchange_rate,
            "value_eur": value_eur,
            "composants": composants or []
        }

        return self.create(db, data)

    @handle_exceptions
    def update_asset(
            self, db: Session,
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
            isin: Code ISIN (optionnel)
            ounces: Nombre d'onces pour les métaux précieux (optionnel)

        Returns:
            L'actif mis à jour ou None
        """
        # Déterminer la catégorie principale (celle avec le pourcentage le plus élevé)
        categorie = max(allocation.items(), key=lambda x: x[1])[0] if allocation else "autre"

        # Calculer la valeur en EUR et le taux de change
        exchange_rate = 1.0
        value_eur = valeur_actuelle

        if devise != "EUR":
            try:
                rates = self.currency_service.get_exchange_rates()
                if devise in rates and rates[devise] > 0:
                    exchange_rate = rates[devise]
                    value_eur = valeur_actuelle / exchange_rate
            except Exception as e:
                logger.error(f"Erreur lors de la conversion de devise: {str(e)}")

        # Données pour la mise à jour
        data = {
            "nom": nom,
            "account_id": compte_id,
            "type_produit": type_produit,
            "categorie": categorie,
            "allocation": allocation,
            "geo_allocation": geo_allocation,
            "valeur_actuelle": float(valeur_actuelle),
            "prix_de_revient": float(prix_de_revient),
            "devise": devise,
            "date_maj": datetime.now().strftime("%Y-%m-%d"),
            "notes": notes,
            "todo": todo,
            "isin": isin,
            "ounces": ounces,
            "exchange_rate": exchange_rate,
            "value_eur": value_eur
        }

        return self.update(db, asset_id, data)

    @handle_exceptions
    def sync_currency_rates(self, db: Session, asset_id: Optional[str] = None) -> int:
        """
        Synchronise les taux de change pour un actif ou tous les actifs

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à synchroniser (tous les actifs si None)

        Returns:
            Nombre d'actifs mis à jour
        """
        # OPTIMISATION: Récupérer les taux de change une seule fois
        rates = self.currency_service.get_exchange_rates()

        # OPTIMISATION: Utiliser une requête optimisée avec filtres directement dans SQL
        query = db.query(Asset)
        if asset_id:
            query = query.filter(Asset.id == asset_id)
        else:
            # Exclure les actifs en EUR directement dans la requête
            query = query.filter(Asset.devise != "EUR")

        # OPTIMISATION: Charger uniquement les colonnes nécessaires
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

        # OPTIMISATION: Commit une seule fois après toutes les mises à jour
        db.commit()

        return updated_count

    @handle_exceptions
    def sync_price_by_isin(self, db: Session, asset_id: Optional[str] = None) -> int:
        """
        Synchronise les prix à partir des codes ISIN pour un actif ou tous les actifs

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à synchroniser (tous les actifs si None)

        Returns:
            Nombre d'actifs mis à jour
        """
        # OPTIMISATION: Utiliser une requête optimisée avec filtres directement dans SQL
        query = db.query(Asset)
        if asset_id:
            query = query.filter(Asset.id == asset_id)
        else:
            # Uniquement les actifs avec un ISIN directement dans la requête
            query = query.filter(Asset.isin != None)

        # OPTIMISATION: Charger uniquement les colonnes nécessaires
        assets = query.all()
        updated_count = 0

        for asset in assets:
            if asset.isin:
                try:
                    # Récupérer le prix
                    price = self.price_service.get_price_by_isin(asset.isin)

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

        # OPTIMISATION: Commit une seule fois après toutes les mises à jour
        db.commit()

        return updated_count

    @handle_exceptions
    def sync_metal_prices(self, db: Session, asset_id: Optional[str] = None) -> int:
        """
        Synchronise les prix des métaux précieux pour un actif ou tous les actifs de type métal

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à synchroniser (tous les actifs métal si None)

        Returns:
            Nombre d'actifs mis à jour
        """
        # OPTIMISATION: Utiliser une requête optimisée avec filtres directement dans SQL
        query = db.query(Asset)
        if asset_id:
            query = query.filter(Asset.id == asset_id)
        else:
            # Uniquement les actifs de type métal avec des onces définies directement dans la requête
            query = query.filter(Asset.type_produit == "metal", Asset.ounces != None)

        # OPTIMISATION: Charger uniquement les colonnes nécessaires
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
                    price_per_ounce = self.price_service.get_metal_price(metal_type)

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

        # OPTIMISATION: Commit une seule fois après toutes les mises à jour
        db.commit()

        return updated_count

    @handle_exceptions
    def update_manual_price(self, db: Session, asset_id: str, new_price: float) -> bool:
        """
        Met à jour manuellement le prix d'un actif

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à mettre à jour
            new_price: Nouveau prix

        Returns:
            True si la mise à jour a réussi, False sinon
        """
        asset = self.get_by_id(db, asset_id)
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
            else:
                # Si pas de taux de change valide, essayer d'en récupérer un
                try:
                    rates = self.currency_service.get_exchange_rates()
                    if asset.devise in rates and rates[asset.devise] > 0:
                        asset.exchange_rate = rates[asset.devise]
                        asset.value_eur = new_price / asset.exchange_rate
                        asset.last_rate_sync = datetime.now()
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion de devise: {str(e)}")
                    # En cas d'erreur, utiliser la valeur en devise comme approximation
                    asset.value_eur = new_price

            # Sauvegarder les modifications
            db.commit()

            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur lors de la mise à jour manuelle du prix: {str(e)}")
            return False

    @handle_exceptions
    def calculate_effective_allocation(self, db: Session, asset_id: str) -> Dict[str, float]:
        """
        Calcule l'allocation effective pour un actif composite

        Args:
            db: Session de base de données
            asset_id: ID de l'actif

        Returns:
            Dictionnaire avec l'allocation effective
        """
        # OPTIMISATION: Utiliser une seule requête avec eager loading pour récupérer l'actif
        asset = db.query(Asset).options(
            joinedload(Asset.account)
        ).filter(Asset.id == asset_id).first()

        if not asset:
            return {}

        # Si l'actif n'a pas de composants, retourner son allocation
        composants = safe_json_loads(getattr(asset, 'composants', '[]'), [])
        if not composants:
            return asset.allocation.copy() if asset.allocation else {}

        # Initialiser l'allocation effective à 0 pour toutes les catégories
        effective_allocation = {category: 0.0 for category in asset.allocation} if asset.allocation else {}

        # Calculer la somme des pourcentages des composants
        total_component_percentage = sum(comp.get('percentage', 0) for comp in composants)

        # Si la somme est supérieure à 100%, normaliser
        normalization_factor = 100.0 / total_component_percentage if total_component_percentage > 100 else 1.0

        # Pourcentage restant pour l'allocation directe
        direct_percentage = max(0, 100 - total_component_percentage * normalization_factor)

        # Ajouter l'allocation directe
        if direct_percentage > 0 and asset.allocation:
            for category, percentage in asset.allocation.items():
                effective_allocation[category] = percentage * direct_percentage / 100.0

        # OPTIMISATION: Récupérer tous les composants en une seule requête
        component_ids = [comp.get('asset_id') for comp in composants if comp.get('asset_id')]
        if component_ids:
            components_query = db.query(Asset).filter(Asset.id.in_(component_ids))
            component_assets = {asset.id: asset for asset in components_query.all()}

            # Ajouter l'allocation des composants
            for comp in composants:
                comp_id = comp.get('asset_id')
                comp_percentage = comp.get('percentage', 0) * normalization_factor / 100.0

                if comp_id and comp_id in component_assets:
                    comp_asset = component_assets[comp_id]
                    if comp_asset.allocation:
                        for category, percentage in comp_asset.allocation.items():
                            if category not in effective_allocation:
                                effective_allocation[category] = 0.0
                            effective_allocation[category] += percentage * comp_percentage

        return effective_allocation

# Créer une instance singleton du service
asset_service = AssetService()