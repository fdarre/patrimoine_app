"""
Modèle pour les comptes
"""

from typing import Dict, Any, Optional


class Account:
    """Classe représentant un compte bancaire"""

    def __init__(
            self,
            id: str,
            banque_id: str,
            type: str,
            libelle: str
    ):
        """
        Initialise un nouveau compte

        Args:
            id: Identifiant unique du compte
            banque_id: Identifiant de la banque associée
            type: Type de compte (courant, livret, etc.)
            libelle: Libellé du compte
        """
        self.id = id
        self.banque_id = banque_id
        self.type = type
        self.libelle = libelle

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> 'Account':
        """
        Crée un compte à partir d'un dictionnaire

        Args:
            id: Identifiant du compte
            data: Dictionnaire contenant les données

        Returns:
            Une instance de Account
        """
        return cls(
            id=id,
            banque_id=data.get("banque_id", ""),
            type=data.get("type", ""),
            libelle=data.get("libelle", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le compte en dictionnaire

        Returns:
            Un dictionnaire représentant le compte
        """
        return {
            "banque_id": self.banque_id,
            "type": self.type,
            "libelle": self.libelle
        }