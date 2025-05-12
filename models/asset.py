"""
Modèle pour les actifs financiers et immobiliers
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, Any


class Asset:
    """Classe représentant un actif financier ou immobilier"""

    def __init__(
            self,
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
            id: Optional[str] = None,
            composants: Optional[List[Dict[str, Union[str, float]]]] = None
    ):
        """
        Initialise un nouvel actif

        Args:
            nom: Nom de l'actif
            compte_id: ID du compte associé
            type_produit: Type de produit (ETF, action, etc.)
            allocation: Répartition par catégorie (ex: {"actions": 80, "obligations": 20})
            geo_allocation: Répartition géographique par catégorie
            valeur_actuelle: Valeur actuelle de l'actif
            prix_de_revient: Prix d'achat de l'actif
            devise: Devise de l'actif (EUR, USD, etc.)
            notes: Notes sur l'actif
            todo: Tâche(s) à faire concernant cet actif
            id: Identifiant unique (généré automatiquement si non fourni)
            composants: Liste des actifs composant cet actif (pour actifs composites)
        """
        self.id = id if id else str(uuid.uuid4())
        self.nom = nom
        self.compte_id = compte_id
        self.type_produit = type_produit
        self.allocation = allocation
        self.geo_allocation = geo_allocation

        # Déterminer la catégorie principale (celle avec le pourcentage le plus élevé)
        if allocation:
            self.categorie = max(allocation.items(), key=lambda x: x[1])[0]
        else:
            self.categorie = "autre"

        self.zone_geographique = geo_allocation.get(self.categorie, {})
        self.valeur_actuelle = float(valeur_actuelle)
        self.prix_de_revient = float(prix_de_revient)
        self.devise = devise
        self.date_maj = datetime.now().strftime("%Y-%m-%d")
        self.notes = notes
        self.todo = todo

        # Composants pour les actifs composites
        self.composants = composants if composants else []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Asset':
        """
        Crée un actif à partir d'un dictionnaire (pour la désérialisation)

        Args:
            data: Dictionnaire contenant les données de l'actif

        Returns:
            Une instance d'Asset
        """
        # Assurer la compatibilité avec les anciens formats de données
        if "allocation" not in data:
            data["allocation"] = {data.get("categorie", "autre"): 100}

        if "geo_allocation" not in data:
            data["geo_allocation"] = {
                data.get("categorie", "autre"): data.get("zone_geographique", {"europe": 100})
            }

        if "composants" not in data:
            data["composants"] = []

        return cls(
            nom=data["nom"],
            compte_id=data["compte_id"],
            type_produit=data["type_produit"],
            allocation=data["allocation"],
            geo_allocation=data["geo_allocation"],
            valeur_actuelle=data["valeur_actuelle"],
            prix_de_revient=data["prix_de_revient"],
            devise=data.get("devise", "EUR"),
            notes=data.get("notes", ""),
            todo=data.get("todo", ""),
            id=data.get("id"),
            composants=data.get("composants", [])
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'actif en dictionnaire (pour la sérialisation)

        Returns:
            Un dictionnaire représentant l'actif
        """
        return {
            "id": self.id,
            "nom": self.nom,
            "compte_id": self.compte_id,
            "type_produit": self.type_produit,
            "categorie": self.categorie,
            "allocation": self.allocation,
            "zone_geographique": self.zone_geographique,
            "geo_allocation": self.geo_allocation,
            "valeur_actuelle": self.valeur_actuelle,
            "prix_de_revient": self.prix_de_revient,
            "devise": self.devise,
            "date_maj": self.date_maj,
            "notes": self.notes,
            "todo": self.todo,
            "composants": self.composants
        }

    def is_composite(self) -> bool:
        """
        Vérifie si l'actif est composite (contient d'autres actifs)

        Returns:
            True si l'actif contient des composants, False sinon
        """
        return len(self.composants) > 0

    def add_component(self, asset_id: str, percentage: float) -> None:
        """
        Ajoute un composant à l'actif

        Args:
            asset_id: ID de l'actif à ajouter comme composant
            percentage: Pourcentage de l'actif alloué à ce composant
        """
        # Vérifier si le composant existe déjà
        for comp in self.composants:
            if comp["asset_id"] == asset_id:
                comp["percentage"] = percentage
                return

        # Ajouter le nouveau composant
        self.composants.append({
            "asset_id": asset_id,
            "percentage": percentage
        })

    def remove_component(self, asset_id: str) -> None:
        """
        Supprime un composant de l'actif

        Args:
            asset_id: ID du composant à supprimer
        """
        self.composants = [comp for comp in self.composants if comp["asset_id"] != asset_id]

    def get_components_total_percentage(self) -> float:
        """
        Calcule le pourcentage total alloué aux composants

        Returns:
            La somme des pourcentages des composants
        """
        return sum(comp["percentage"] for comp in self.composants)