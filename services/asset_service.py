"""
Service de gestion des actifs - Responsabilités de base
"""
import uuid
from datetime import datetime
# Imports de la bibliothèque standard
from typing import List, Optional, Dict, Any

from sqlalchemy import func
# Imports de bibliothèques tierces
from sqlalchemy.orm import Session, joinedload

# Imports de l'application
from database.models import Asset, Account
from services.base_service import BaseService
from utils.decorators import handle_exceptions
from utils.logger import get_logger

logger = get_logger(__name__)

class AssetService(BaseService[Asset]):
    """
    Service pour la gestion CRUD des actifs
    """

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
            isin: Code ISIN (optionnel)
            ounces: Nombre d'onces pour les métaux précieux (optionnel)

        Returns:
            Le nouvel actif créé ou None
        """
        if prix_de_revient is None:
            prix_de_revient = valeur_actuelle

        # Déterminer la catégorie principale (celle avec le pourcentage le plus élevé)
        categorie = max(allocation.items(), key=lambda x: x[1])[0] if allocation else "autre"

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
            "exchange_rate": 1.0,  # Default
            "value_eur": valeur_actuelle if devise == "EUR" else None
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
        Met à jour un actif existant (sans synchronisation)

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
            "ounces": ounces
        }

        return self.update(db, asset_id, data)

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

            # Mettre à jour la date de MAJ
            asset.date_maj = datetime.now().strftime("%Y-%m-%d")

            # Mise à jour simple de la valeur en EUR si devise EUR
            if asset.devise == "EUR":
                asset.value_eur = new_price

            # Sauvegarder les modifications
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur lors de la mise à jour manuelle du prix: {str(e)}")
            return False

    @handle_exceptions
    def clear_todo(self, db: Session, asset_id: str) -> bool:
        """
        Vide le champ todo d'un actif existant de manière directe

        Args:
            db: Session de base de données
            asset_id: ID de l'actif à mettre à jour

        Returns:
            True si la mise à jour a réussi, False sinon
        """
        try:
            # Mettre à jour directement le champ todo sans recharger tout l'actif
            result = db.query(Asset).filter(Asset.id == asset_id).update({"todo": ""})
            db.commit()
            logger.info(f"Todo effacé pour l'actif {asset_id}")
            return result > 0
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur lors de l'effacement du todo: {str(e)}")
            return False

    @staticmethod
    def calculate_performance(asset: Asset) -> Dict[str, Any]:
        """
        Calcule la performance d'un actif de manière standardisée

        Args:
            asset: Actif à évaluer

        Returns:
            Dictionnaire contenant la valeur, le pourcentage et le signe de la plus-value
        """
        pv = asset.valeur_actuelle - asset.prix_de_revient
        pv_percent = (pv / asset.prix_de_revient * 100) if asset.prix_de_revient > 0 else 0

        return {
            "value": pv,
            "percent": pv_percent,
            "is_positive": pv_percent >= 0
        }


# Créer une instance singleton du service
asset_service = AssetService()