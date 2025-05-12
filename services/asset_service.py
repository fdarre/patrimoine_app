"""
Service de gestion des actifs
"""

from typing import Dict, List, Optional, Union, Any
import pandas as pd

from models.asset import Asset


class AssetService:
    """Service pour la gestion des actifs"""

    @staticmethod
    def add_asset(
            assets: List[Asset],
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
            composants: Optional[List[Dict[str, Union[str, float]]]] = None
    ) -> Asset:
        """
        Ajoute un nouvel actif

        Args:
            assets: Liste des actifs existants
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
            Le nouvel actif créé
        """
        if prix_de_revient is None:
            prix_de_revient = valeur_actuelle

        new_asset = Asset(
            nom=nom,
            compte_id=compte_id,
            type_produit=type_produit,
            allocation=allocation,
            geo_allocation=geo_allocation,
            valeur_actuelle=valeur_actuelle,
            prix_de_revient=prix_de_revient,
            devise=devise,
            notes=notes,
            todo=todo,
            composants=composants if composants else []
        )

        assets.append(new_asset)
        return new_asset

    @staticmethod
    def update_asset(
            assets: List[Asset],
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
            composants: Optional[List[Dict[str, Union[str, float]]]] = None
    ) -> Optional[Asset]:
        """
        Met à jour un actif existant

        Args:
            assets: Liste des actifs existants
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
            L'actif mis à jour ou None si non trouvé
        """
        asset = AssetService.find_asset_by_id(assets, asset_id)
        if not asset:
            return None

        asset.nom = nom
        asset.compte_id = compte_id
        asset.type_produit = type_produit
        asset.allocation = allocation
        asset.geo_allocation = geo_allocation
        asset.categorie = max(allocation.items(), key=lambda x: x[1])[0]
        asset.zone_geographique = geo_allocation.get(asset.categorie, {})
        asset.valeur_actuelle = float(valeur_actuelle)
        asset.prix_de_revient = float(prix_de_revient)
        asset.devise = devise
        asset.notes = notes
        asset.todo = todo

        if composants is not None:
            asset.composants = composants

        return asset

    @staticmethod
    def delete_asset(assets: List[Asset], asset_id: str) -> bool:
        """
        Supprime un actif

        Args:
            assets: Liste des actifs existants
            asset_id: ID de l'actif à supprimer

        Returns:
            True si l'actif a été supprimé, False sinon
        """
        # Vérifier si l'actif est un composant d'autres actifs
        for asset in assets:
            if any(comp["asset_id"] == asset_id for comp in asset.composants):
                # Ne pas supprimer un actif utilisé comme composant
                return False

        initial_length = len(assets)
        assets[:] = [asset for asset in assets if asset.id != asset_id]
        return len(assets) < initial_length

    @staticmethod
    def find_asset_by_id(assets: List[Asset], asset_id: str) -> Optional[Asset]:
        """
        Trouve un actif par son ID

        Args:
            assets: Liste des actifs
            asset_id: ID de l'actif recherché

        Returns:
            L'actif trouvé ou None
        """
        for asset in assets:
            if asset.id == asset_id:
                return asset
        return None

    @staticmethod
    def is_used_as_component(assets: List[Asset], asset_id: str) -> bool:
        """
        Vérifie si un actif est utilisé comme composant dans d'autres actifs

        Args:
            assets: Liste de tous les actifs
            asset_id: ID de l'actif à vérifier

        Returns:
            True si l'actif est utilisé comme composant, False sinon
        """
        for asset in assets:
            if any(comp["asset_id"] == asset_id for comp in asset.composants):
                return True
        return False

    @staticmethod
    def get_assets_dataframe(
            assets: List[Asset],
            accounts: Dict[str, Dict[str, Any]],
            banks: Dict[str, Dict[str, Any]],
            account_id: Optional[str] = None,
            category: Optional[str] = None,
            bank_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Crée un DataFrame Pandas avec les actifs filtrés

        Args:
            assets: Liste des actifs
            accounts: Dictionnaire des comptes
            banks: Dictionnaire des banques
            account_id: Filtre par ID de compte (optionnel)
            category: Filtre par catégorie (optionnel)
            bank_id: Filtre par ID de banque (optionnel)

        Returns:
            DataFrame Pandas des actifs filtrés
        """
        data = []

        for asset in assets:
            # Appliquer les filtres
            if account_id and asset.compte_id != account_id:
                continue

            if category and category not in asset.allocation:
                continue

            if bank_id and accounts[asset.compte_id]["banque_id"] != bank_id:
                continue

            account = accounts[asset.compte_id]
            bank_name = banks[account["banque_id"]]["nom"]

            # Calculer la plus-value
            pv = asset.valeur_actuelle - asset.prix_de_revient
            pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
            pv_class = "positive" if pv >= 0 else "negative"

            # Formatter les valeurs avec séparateurs de milliers
            formatted_value = f"{asset.valeur_actuelle:,.2f} {asset.devise}".replace(",", " ")
            formatted_pv = f"{pv:,.2f} {asset.devise} ({pv_percent:.2f}%)".replace(",", " ")

            # Déterminer la catégorie principale
            main_category = asset.categorie

            # Créer une représentation des allocations (ex: "Actions 60% / Obligations 40%")
            allocation_str = " / ".join(f"{cat.capitalize()} {pct}%" for cat, pct in asset.allocation.items())

            # Indicateur d'actif composite
            composite_indicator = "✓" if asset.is_composite() else ""

            data.append([
                asset.id,
                asset.nom,
                main_category,
                allocation_str,
                asset.type_produit,
                formatted_value,
                f'<span class="{pv_class}">{formatted_pv}</span>',
                bank_name,
                account["libelle"],
                composite_indicator
            ])

        df = pd.DataFrame(data, columns=["ID", "Nom", "Catégorie", "Allocation", "Type", "Valeur",
                                         "Plus-value", "Banque", "Compte", "Composite"])
        return df

    @staticmethod
    def calculate_effective_allocation(
            assets: List[Asset],
            target_asset: Asset
    ) -> Dict[str, float]:
        """
        Calcule l'allocation effective d'un actif composite en tenant compte de ses composants

        Args:
            assets: Liste de tous les actifs
            target_asset: Actif pour lequel calculer l'allocation effective

        Returns:
            Dictionnaire avec les allocations effectives par catégorie
        """
        if not target_asset.composants:
            return target_asset.allocation

        effective_allocation = {cat: 0.0 for cat in target_asset.allocation.keys()}

        # D'abord, ajouter l'allocation directe de l'actif principal
        direct_percentage = 100 - target_asset.get_components_total_percentage()
        for category, percentage in target_asset.allocation.items():
            effective_allocation[category] += (percentage * direct_percentage / 100)

        # Ensuite, ajouter les allocations des composants
        for component in target_asset.composants:
            component_asset = AssetService.find_asset_by_id(assets, component["asset_id"])
            if not component_asset:
                continue

            component_percentage = component["percentage"]
            component_allocation = AssetService.calculate_effective_allocation(assets, component_asset)

            for category, percentage in component_allocation.items():
                if category not in effective_allocation:
                    effective_allocation[category] = 0.0
                effective_allocation[category] += (percentage * component_percentage / 100)

        return effective_allocation

    @staticmethod
    def calculate_effective_geo_allocation(
            assets: List[Asset],
            target_asset: Asset,
            category: Optional[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcule la répartition géographique effective d'un actif composite

        Args:
            assets: Liste de tous les actifs
            target_asset: Actif pour lequel calculer la répartition
            category: Catégorie spécifique à calculer (optionnel)

        Returns:
            Dictionnaire avec les répartitions géographiques effectives par catégorie
        """
        if not target_asset.composants:
            if category:
                return {category: target_asset.geo_allocation.get(category, {})}
            return target_asset.geo_allocation

        # Initialiser avec les catégories d'allocation de l'actif
        effective_geo = {}
        categories = [category] if category else target_asset.allocation.keys()

        for cat in categories:
            if cat not in effective_geo:
                effective_geo[cat] = {zone: 0.0 for zone in target_asset.geo_allocation.get(cat, {}).keys()}

        # D'abord, ajouter la répartition directe de l'actif principal
        direct_percentage = 100 - target_asset.get_components_total_percentage()
        for cat in categories:
            cat_percentage = target_asset.allocation.get(cat, 0) * direct_percentage / 100
            if cat_percentage > 0:
                for zone, zone_pct in target_asset.geo_allocation.get(cat, {}).items():
                    if zone not in effective_geo[cat]:
                        effective_geo[cat][zone] = 0.0
                    effective_geo[cat][zone] += (zone_pct * cat_percentage / 100)

        # Ensuite, ajouter les répartitions des composants
        for component in target_asset.composants:
            component_asset = AssetService.find_asset_by_id(assets, component["asset_id"])
            if not component_asset:
                continue

            component_percentage = component["percentage"]
            component_geo = AssetService.calculate_effective_geo_allocation(assets, component_asset)

            for cat in categories:
                if cat not in component_asset.allocation:
                    continue

                cat_component_percentage = component_asset.allocation[cat] * component_percentage / 100

                for zone, zone_pct in component_geo.get(cat, {}).items():
                    if cat not in effective_geo:
                        effective_geo[cat] = {}
                    if zone not in effective_geo[cat]:
                        effective_geo[cat][zone] = 0.0
                    effective_geo[cat][zone] += (zone_pct * cat_component_percentage / 100)

        return effective_geo