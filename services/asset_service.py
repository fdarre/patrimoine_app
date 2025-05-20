"""
Service for asset management - Core responsibilities
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session, joinedload

from database.models import Asset, Account
from services.base_service import BaseService
from utils.calculations import calculate_asset_performance
from utils.error_manager import catch_exceptions
from utils.logger import get_logger

logger = get_logger(__name__)

class AssetService(BaseService[Asset]):
    """
    Service for CRUD operations on assets
    """

    def __init__(self):
        super().__init__(Asset)

    def get_assets(
            self, db: Session,
            user_id: str,
            account_id: Optional[str] = None,
            category: Optional[str] = None
    ) -> List[Asset]:
        """
        Get all assets for a user with optional filters

        Args:
            db: Database session
            user_id: User ID
            account_id: Account ID (optional)
            category: Asset category (optional)

        Returns:
            List of assets
        """
        try:
            # OPTIMIZATION: Use eager loading to load relations in a single query
            query = db.query(Asset).options(
                joinedload(Asset.account).joinedload(Account.bank)
            ).filter(Asset.owner_id == user_id)

            if account_id:
                query = query.filter(Asset.account_id == account_id)

            # Category filtering with consistent approach
            if category:
                query = query.filter(Asset.allocation.has_key(category))  # Using SQLAlchemy's has_key for JSON

            result = query.all()
            return result if result is not None else []
        except Exception as e:
            logger.error(f"Error getting assets: {str(e)}")
            return []  # Always return a list, even empty, never None

    @catch_exceptions
    @catch_exceptions
    def add_asset(
            self, db: Session,
            user_id: str,
            nom: str,  # Changé de name à nom
            compte_id: str,  # Changé de account_id à compte_id
            type_produit: str,  # Changé de product_type à type_produit
            allocation: Dict[str, float],
            geo_allocation: Dict[str, Dict[str, float]],
            valeur_actuelle: float,  # Changé de current_value à valeur_actuelle
            prix_de_revient: Optional[float] = None,  # Changé de cost_basis à prix_de_revient
            devise: str = "EUR",  # Changé de currency à devise
            notes: str = "",
            todo: str = "",
            isin: Optional[str] = None,
            ounces: Optional[float] = None
    ) -> Optional[Asset]:
        """
        Add a new asset

        Args:
            db: Database session
            user_id: Owner user ID
            nom: Asset name
            compte_id: Associated account ID
            type_produit: Product type
            allocation: Category allocation
            geo_allocation: Geographic allocation by category
            valeur_actuelle: Current value
            prix_de_revient: Cost basis (if None, uses valeur_actuelle)
            devise: Currency
            notes: Notes
            todo: Task(s) to do
            isin: ISIN code (optional)
            ounces: Number of ounces for precious metals (optional)

        Returns:
            The newly created asset or None
        """
        if prix_de_revient is None:
            prix_de_revient = valeur_actuelle

        # Determine main category (the one with the highest percentage)
        category = max(allocation.items(), key=lambda x: x[1])[0] if allocation else "autre"

        # Data for creation
        data = {
            "id": str(uuid.uuid4()),
            "owner_id": user_id,
            "account_id": compte_id,  # Changé pour correspondre au modèle de BDD
            "nom": nom,  # Keep French field names to maintain DB compatibility
            "type_produit": type_produit,
            "categorie": category,
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
            "exchange_rate": 1.0,  # Default
            "value_eur": valeur_actuelle if devise == "EUR" else None
        }

        return self.create(db, data)

    @catch_exceptions
    def update_asset(
            self, db: Session,
            asset_id: str,
            nom: str,  # Changé de name à nom
            compte_id: str,  # Changé de account_id à compte_id
            type_produit: str,  # Changé de product_type à type_produit
            allocation: Dict[str, float],
            geo_allocation: Dict[str, Dict[str, float]],
            valeur_actuelle: float,  # Changé de current_value à valeur_actuelle
            prix_de_revient: float,  # Changé de cost_basis à prix_de_revient
            devise: str = "EUR",  # Changé de currency à devise
            notes: str = "",
            todo: str = "",
            isin: Optional[str] = None,
            ounces: Optional[float] = None
    ) -> Optional[Asset]:
        """
        Update an existing asset (without synchronization)

        Args:
            db: Database session
            asset_id: ID of asset to update
            nom: New name
            compte_id: New account
            type_produit: New type
            allocation: New allocation
            geo_allocation: New geographic allocation
            valeur_actuelle: New value
            prix_de_revient: New cost basis
            devise: New currency
            notes: New notes
            todo: New task(s)
            isin: ISIN code (optional)
            ounces: Number of ounces for precious metals (optional)

        Returns:
            The updated asset or None
        """
        # Determine main category (the one with the highest percentage)
        category = max(allocation.items(), key=lambda x: x[1])[0] if allocation else "autre"

        # Data for update
        data = {
            "nom": nom,
            "account_id": compte_id,  # Assurez-vous que cela correspond à la colonne dans la BDD
            "type_produit": type_produit,
            "categorie": category,
            "allocation": allocation,
            "geo_allocation": geo_allocation,
            "valeur_actuelle": float(valeur_actuelle),
            "prix_de_revient": float(prix_de_revient),
            "devise": devise,
            "date_maj": datetime.now().strftime("%Y-%m-%d"),
            "notes": notes,
            "todo": todo,
            "isin": isin,
            "ounces": ounces
        }

        return self.update(db, asset_id, data)

    @catch_exceptions
    def update_manual_price(self, db: Session, asset_id: str, new_price: float) -> bool:
        """
        Manually update an asset's price

        Args:
            db: Database session
            asset_id: ID of asset to update
            new_price: New price

        Returns:
            True if update was successful, False otherwise
        """
        asset = self.get_by_id(db, asset_id)
        if not asset:
            return False

        try:
            # Update price
            asset.valeur_actuelle = new_price
            asset.last_price_sync = datetime.now()
            asset.sync_error = None

            # Update modification date
            asset.date_maj = datetime.now().strftime("%Y-%m-%d")

            # Simple update of EUR value if EUR currency
            if asset.devise == "EUR":
                asset.value_eur = new_price

            # Save changes
            db.commit()
            logger.info(f"Manual price update for asset {asset_id}: {new_price}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error during manual price update: {str(e)}")
            return False

    @catch_exceptions
    def clear_todo(self, db: Session, asset_id: str) -> bool:
        """
        Clear the todo field of an existing asset directly

        Args:
            db: Database session
            asset_id: ID of asset to update

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Directly update the todo field without reloading the entire asset
            result = db.query(Asset).filter(Asset.id == asset_id).update({"todo": ""})
            db.commit()
            logger.info(f"Todo cleared for asset {asset_id}")
            return result > 0
        except Exception as e:
            db.rollback()
            logger.error(f"Error clearing todo: {str(e)}")
            return False

    @staticmethod
    def calculate_performance(asset: Asset) -> Dict[str, Any]:
        """
        Calculate asset performance in a standardized way

        Args:
            asset: Asset to evaluate

        Returns:
            Dictionary containing value, percentage and sign of the gain/loss
        """
        # Use centralized function
        return calculate_asset_performance(asset.valeur_actuelle, asset.prix_de_revient)


# Create singleton instance of the service
asset_service = AssetService()