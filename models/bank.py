"""
Modèle pour les banques
"""

from typing import Dict, Any, Optional


class Bank:
    """Classe représentant une banque"""

    def __init__(
            self,
            id: str,
            nom: str,
            notes: str = ""
    ):
        """
        Initialise une nouvelle banque

        Args:
            id: Identifiant unique de la banque
            nom: Nom de la banque
            notes: Notes sur la banque
        """
        self.id = id
        self.nom = nom
        self.notes = notes

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> 'Bank':
        """
        Crée une banque à partir d'un dictionnaire

        Args:
            id: Identifiant de la banque
            data: Dictionnaire contenant les données

        Returns:
            Une instance de Bank
        """
        return cls(
            id=id,
            nom=data.get("nom", ""),
            notes=data.get("notes", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit la banque en dictionnaire

        Returns:
            Un dictionnaire représentant la banque
        """
        return {
            "nom": self.nom,
            "notes": self.notes
        }