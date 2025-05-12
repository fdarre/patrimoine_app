"""
Modèle pour les points d'historique
"""

from typing import Dict, Any, List
from datetime import datetime


class HistoryPoint:
    """Classe représentant un point d'historique"""

    def __init__(
            self,
            date: str,
            assets: Dict[str, float],
            total: float
    ):
        """
        Initialise un point d'historique

        Args:
            date: Date du point d'historique (format YYYY-MM-DD)
            assets: Dictionnaire {asset_id: valeur} pour chaque actif
            total: Valeur totale du patrimoine à cette date
        """
        self.date = date
        self.assets = assets
        self.total = total

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryPoint':
        """
        Crée un point d'historique à partir d'un dictionnaire

        Args:
            data: Dictionnaire contenant les données

        Returns:
            Une instance de HistoryPoint
        """
        return cls(
            date=data.get("date", ""),
            assets=data.get("assets", {}),
            total=data.get("total", 0.0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le point d'historique en dictionnaire

        Returns:
            Un dictionnaire représentant le point d'historique
        """
        return {
            "date": self.date,
            "assets": self.assets,
            "total": self.total
        }

    @staticmethod
    def create_today(assets_values: Dict[str, float]) -> 'HistoryPoint':
        """
        Crée un point d'historique pour aujourd'hui

        Args:
            assets_values: Dictionnaire {asset_id: valeur} pour chaque actif

        Returns:
            Un nouveau point d'historique
        """
        return HistoryPoint(
            date=datetime.now().strftime("%Y-%m-%d"),
            assets=assets_values,
            total=sum(assets_values.values())
        )