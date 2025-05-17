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
        query = db.query(Asset).filter(Asset.owner_id == user_id)

        if account_id:
            query = query.filter(Asset.account_id == account_id)

        # Récupérer tous les actifs et filtrer par catégorie en Python
        assets = query.all()

        if category:
            # Filtrer les actifs qui ont cette catégorie dans leur allocation
            assets = [asset for asset in assets
                     if asset.allocation and category in asset.allocation]

        return assets

    @handle_exceptions
    def find_asset_by_id(self, db: Session, asset_id: str) -> Optional[Asset]:
        """
        Trouve un actif par son ID

        Args:
            db: Session de base de données
            asset_id: ID de l'actif recherché

        Returns:
            L'actif trouvé ou None
        """
        return self.get_by_id(db, asset_id)

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
                rates = CurrencyService.get_exchange_rates()
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
                rates = CurrencyService.get_exchange_rates()
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
    def delete_asset(self, db: Session, asset_id: str) -> bool:
        """
        Supprime un actif

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à supprimer

        Returns:
            True si l'actif a été supprimé, False sinon
        """
        return self.delete(db, asset_id)

    @handle_exceptions
    def get_assets_dataframe(
            self, db: Session,
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

        # Exécuter la requête
        results = query.all()

        # Post-filtrage pour la catégorie (car c'est un champ JSON)
        if category:
            results = [
                (asset, account, bank) for asset, account, bank in results
                if asset.allocation and category in asset.allocation
            ]

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

            data.append([
                asset.id,
                asset.nom,
                asset.categorie.capitalize(),
                allocation_str,
                asset.type_produit,
                formatted_value,
                f'<span class="{pv_class}">{formatted_pv}</span>',
                bank.nom,
                account.libelle
            ])

        return pd.DataFrame(data, columns=["ID", "Nom", "Catégorie", "Allocation", "Type", "Valeur",
                                          "Plus-value", "Banque", "Compte"])

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
                    rates = CurrencyService.get_exchange_rates()
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
    def update_manual_exchange_rate(self, db: Session, asset_id: str, new_rate: float) -> bool:
        """
        Met à jour manuellement le taux de change d'un actif

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à mettre à jour
            new_rate: Nouveau taux de change

        Returns:
            True si la mise à jour a réussi, False sinon
        """
        asset = self.get_by_id(db, asset_id)
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
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur lors de la mise à jour manuelle du taux de change: {str(e)}")
            return False

    # Méthodes utilitaires pour les actifs composites
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
        asset = self.get_by_id(db, asset_id)
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

        # Ajouter l'allocation des composants
        for comp in composants:
            comp_id = comp.get('asset_id')
            comp_percentage = comp.get('percentage', 0) * normalization_factor / 100.0

            if comp_id:
                # Récupérer l'allocation effective du composant (récursif)
                comp_allocation = self.calculate_effective_allocation(db, comp_id)

                # Ajouter à l'allocation effective en proportion
                for category, percentage in comp_allocation.items():
                    if category not in effective_allocation:
                        effective_allocation[category] = 0.0
                    effective_allocation[category] += percentage * comp_percentage

        return effective_allocation

    @handle_exceptions
    def calculate_effective_geo_allocation(
            self, db: Session,
            asset_id: str,
            category: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcule la répartition géographique effective pour une catégorie

        Args:
            db: Session de base de données
            asset_id: ID de l'actif
            category: Catégorie d'actif

        Returns:
            Dictionnaire de la répartition géographique
        """
        asset = self.get_by_id(db, asset_id)
        if not asset:
            return {}

        # Si l'actif n'a pas de composants, retourner sa répartition géo
        composants = safe_json_loads(getattr(asset, 'composants', '[]'), [])
        if not composants:
            return asset.geo_allocation.get(category, {}).copy() if asset.geo_allocation else {}

        # Initialiser la répartition effective
        effective_geo = {}

        # Calculer l'allocation effective pour obtenir le pourcentage de chaque catégorie
        effective_allocation = self.calculate_effective_allocation(db, asset_id)
        category_percentage = effective_allocation.get(category, 0.0)

        if category_percentage <= 0:
            return {}

        # Récupérer les composants qui contribuent à cette catégorie
        category_components = []

        for comp in composants:
            comp_id = comp.get('asset_id')
            comp_percentage = comp.get('percentage', 0)

            comp_asset = self.get_by_id(db, comp_id)
            if comp_asset and comp_asset.allocation and category in comp_asset.allocation:
                # Calculer la contribution du composant à cette catégorie
                comp_contribution = (
                    comp_percentage *
                    comp_asset.allocation.get(category, 0.0) / 100.0
                )

                if comp_contribution > 0:
                    category_components.append({
                        'asset_id': comp_id,
                        'percentage': comp_contribution
                    })

        # Si aucun composant ne contribue, utiliser la répartition directe
        if not category_components:
            return asset.geo_allocation.get(category, {}).copy() if asset.geo_allocation else {}

        # Calculer la contribution directe
        direct_contribution = category_percentage - sum(comp.get('percentage', 0) for comp in category_components)

        # Ajouter la contribution directe si positive
        if direct_contribution > 0 and asset.geo_allocation and category in asset.geo_allocation:
            direct_geo = asset.geo_allocation.get(category, {})
            for zone, percentage in direct_geo.items():
                effective_geo[zone] = direct_contribution * percentage / 100.0

        # Ajouter les contributions des composants
        for comp in category_components:
            comp_id = comp.get('asset_id')
            comp_percentage = comp.get('percentage', 0)

            if comp_id:
                comp_asset = self.get_by_id(db, comp_id)
                if comp_asset and comp_asset.geo_allocation and category in comp_asset.geo_allocation:
                    comp_geo = comp_asset.geo_allocation.get(category, {})

                    for zone, percentage in comp_geo.items():
                        if zone not in effective_geo:
                            effective_geo[zone] = 0.0
                        effective_geo[zone] += comp_percentage * percentage / 100.0

        # Normaliser à 100%
        total = sum(effective_geo.values())
        if total > 0:
            effective_geo = {zone: (pct / total * 100.0) for zone, pct in effective_geo.items()}

        return {category: effective_geo}

# Créer une instance singleton du service
asset_service = AssetService()