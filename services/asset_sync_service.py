"""
Service spécialisé pour la synchronisation des prix des actifs
"""
from datetime import datetime
# Imports de la bibliothèque standard
from typing import Optional, Callable

# Imports de bibliothèques tierces
from sqlalchemy.orm import Session

# Imports de l'application
from database.models import Asset
from services.currency_service import CurrencyService
from services.price_service import PriceService
from utils.error_manager import catch_exceptions  # Changé de handle_exceptions
from utils.logger import get_logger

logger = get_logger(__name__)

class AssetSyncService:
    """
    Service spécialisé pour la synchronisation des prix et taux de change des actifs

    Ce service isole les fonctionnalités de synchronisation qui étaient auparavant
    dans AssetService, suivant ainsi le principe de responsabilité unique.
    """
    def __init__(self):
        """Initialise le service avec les dépendances nécessaires"""
        self.price_service = PriceService()
        self.currency_service = CurrencyService()

    @catch_exceptions  # Changé de handle_exceptions
    def _sync_assets(
            self,
            db: Session,
            filter_func: Callable,
            update_func: Callable,
            asset_id: Optional[str] = None
    ) -> int:
        """
        Méthode générique de synchronisation des actifs

        Args:
            db: Session de base de données
            filter_func: Fonction de filtrage pour sélectionner les actifs à synchroniser
            update_func: Fonction de mise à jour d'un actif individuel
            asset_id: ID de l'actif spécifique à synchroniser (tous si None)

        Returns:
            Nombre d'actifs mis à jour
        """
        # Construire la requête de base
        query = db.query(Asset)

        # Appliquer le filtre par ID si spécifié
        if asset_id:
            query = query.filter(Asset.id == asset_id)
        else:
            # Appliquer le filtre spécifique
            query = filter_func(query)

        # Récupérer les actifs
        assets = query.all()
        updated_count = 0
        error_updated = False  # Pour suivre si des erreurs ont été mises à jour

        # Appliquer la fonction de mise à jour à chaque actif
        for asset in assets:
            try:
                if update_func(asset):
                    updated_count += 1
                else:
                    # Une erreur a peut-être été définie, nous devons aussi commit dans ce cas
                    if asset.sync_error is not None:
                        error_updated = True
            except Exception as e:
                logger.error(f"Exception lors de la mise à jour de l'actif {asset.id}: {str(e)}")
                # Définir l'erreur directement ici aussi au cas où
                asset.sync_error = str(e)
                error_updated = True

        # Sauvegarder toutes les modifications en une seule fois
        # Commit si des actifs ont été mis à jour ou si des erreurs ont été définies
        if updated_count > 0 or error_updated:
            db.commit()

        return updated_count

    @catch_exceptions  # Changé de handle_exceptions
    def sync_currency_rates(self, db: Session, asset_id: Optional[str] = None) -> int:
        """
        Synchronise les taux de change pour un actif ou tous les actifs

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à synchroniser (tous les actifs si None)

        Returns:
            Nombre d'actifs mis à jour
        """
        # Récupérer les taux de change une seule fois
        rates = self.currency_service.get_exchange_rates()

        # Définir la fonction de filtrage
        def filter_assets(query):
            return query.filter(Asset.devise != "EUR")

        # Définir la fonction de mise à jour
        def update_asset(asset):
            try:
                if asset.devise == "EUR":
                    # Pour les actifs en EUR, le taux est toujours 1
                    asset.exchange_rate = 1.0
                    asset.value_eur = asset.valeur_actuelle
                    asset.last_rate_sync = datetime.now()
                    asset.sync_error = None
                    return True
                else:
                    # Récupérer le taux de change
                    exchange_rate = rates.get(asset.devise)

                    if exchange_rate and exchange_rate > 0:
                        # Mettre à jour l'actif
                        asset.exchange_rate = exchange_rate
                        # CORRECTION: Division au lieu de multiplication pour convertir en EUR
                        asset.value_eur = asset.valeur_actuelle / exchange_rate
                        asset.last_rate_sync = datetime.now()
                        asset.sync_error = None
                        return True
                    else:
                        asset.sync_error = f"Taux de change non disponible pour {asset.devise}"
                        return False
            except Exception as e:
                asset.sync_error = str(e)  # CORRECTION: Ajout de mise à jour du champ sync_error
                logger.error(f"Erreur lors de la mise à jour du taux de change pour {asset.id}: {str(e)}")
                return False

        # CORRECTION: Ajouter l'appel à _sync_assets qui manquait
        return self._sync_assets(db, filter_assets, update_asset, asset_id)

    @catch_exceptions  # Changé de handle_exceptions
    def sync_price_by_isin(self, db: Session, asset_id: Optional[str] = None) -> int:
        """
        Synchronise les prix à partir des codes ISIN pour un actif ou tous les actifs

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à synchroniser (tous les actifs si None)

        Returns:
            Nombre d'actifs mis à jour
        """

        # Définir la fonction de filtrage
        def filter_assets(query):
            return query.filter(Asset.isin != None, Asset.isin != "")

        # Définir la fonction de mise à jour
        def update_asset(asset):
            if asset.isin:
                try:
                    # Récupérer le prix
                    price = self.price_service.get_price_by_isin(asset.isin)

                    if price and price > 0:
                        # Mettre à jour l'actif
                        asset.valeur_actuelle = price
                        asset.last_price_sync = datetime.now()
                        asset.date_maj = datetime.now().strftime("%Y-%m-%d")
                        asset.sync_error = None

                        # Mettre à jour la valeur en EUR
                        if asset.devise == "EUR":
                            asset.value_eur = price
                        elif asset.exchange_rate and asset.exchange_rate > 0:
                            asset.value_eur = price / asset.exchange_rate

                        return True
                    else:
                        asset.sync_error = f"Prix non disponible pour ISIN {asset.isin}"
                        return False
                except Exception as e:
                    asset.sync_error = str(e)
                    logger.error(f"Erreur lors de la mise à jour du prix par ISIN pour {asset.id}: {str(e)}")
                    return False
            return False

        return self._sync_assets(db, filter_assets, update_asset, asset_id)

    @catch_exceptions  # Changé de handle_exceptions
    def sync_metal_prices(self, db: Session, asset_id: Optional[str] = None) -> int:
        """
        Synchronise les prix des métaux précieux pour un actif ou tous les actifs de type métal

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à synchroniser (tous les actifs métal si None)

        Returns:
            Nombre d'actifs mis à jour
        """

        # Définir la fonction de filtrage
        def filter_assets(query):
            return query.filter(Asset.type_produit == "metal", Asset.ounces != None)

        # Définir la fonction de mise à jour
        def update_asset(asset):
            if asset.type_produit == "metal" and asset.ounces:
                try:
                    # Déterminer le type de métal (or par défaut)
                    metal_type = "gold"  # Par défaut
                    if asset.nom:
                        nom_lower = asset.nom.lower()
                        if "silver" in nom_lower or "argent" in nom_lower:
                            metal_type = "silver"
                        elif "platinum" in nom_lower or "platine" in nom_lower:
                            metal_type = "platinum"
                        elif "palladium" in nom_lower:
                            metal_type = "palladium"

                    # Récupérer le prix par once
                    price_per_ounce = self.price_service.get_metal_price(metal_type)

                    if price_per_ounce and price_per_ounce > 0:
                        # Calculer la valeur totale
                        total_value = price_per_ounce * asset.ounces

                        # Mettre à jour l'actif
                        asset.valeur_actuelle = total_value
                        asset.last_price_sync = datetime.now()
                        asset.date_maj = datetime.now().strftime("%Y-%m-%d")
                        asset.sync_error = None

                        # Mettre à jour la valeur en EUR
                        if asset.devise == "EUR":
                            asset.value_eur = total_value
                        elif asset.exchange_rate and asset.exchange_rate > 0:
                            asset.value_eur = total_value / asset.exchange_rate

                        return True
                    else:
                        asset.sync_error = f"Prix non disponible pour {metal_type}"
                        return False
                except Exception as e:
                    asset.sync_error = str(e)
                    logger.error(f"Erreur lors de la mise à jour du prix du métal pour {asset.id}: {str(e)}")
                    return False
            return False

        return self._sync_assets(db, filter_assets, update_asset, asset_id)

    @catch_exceptions  # Changé de handle_exceptions
    def sync_all(self, db: Session) -> dict:
        """
        Synchronise tous les types d'actifs en une seule opération

        Args:
            db: Session de base de données

        Returns:
            Dictionnaire avec les compteurs par type
        """
        # Effectuer toutes les synchronisations dans l'ordre
        results = {
            "currency_rates": self.sync_currency_rates(db),
            "isin_prices": self.sync_price_by_isin(db),
            "metal_prices": self.sync_metal_prices(db),
        }

        # Déterminer si des actifs ont été mis à jour
        total_updates = sum(results.values())

        return {
            "updated_count": total_updates,
            "details": results
        }


# Créer une instance singleton du service
asset_sync_service = AssetSyncService()