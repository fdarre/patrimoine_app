"""
Service de chargement et sauvegarde des données
"""

import os
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime

from utils.constants import DATA_DIR, BANKS_FILE, ACCOUNTS_FILE, ASSETS_FILE, HISTORY_FILE
from models.asset import Asset


class DataService:
    """Service de gestion des données persistantes"""

    @staticmethod
    def initialize_data_dir():
        """Crée le répertoire de données s'il n'existe pas"""
        os.makedirs(DATA_DIR, exist_ok=True)

    @staticmethod
    def load_data() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], List[Asset], List[Dict[str, Any]]]:
        """
        Charge les données depuis les fichiers JSON

        Returns:
            Un tuple contenant (banks, accounts, assets, history)
        """
        DataService.initialize_data_dir()

        # Chargement des banques
        if os.path.exists(BANKS_FILE):
            with open(BANKS_FILE, "r", encoding="utf-8") as f:
                banks = json.load(f)
        else:
            banks = {}

        # Chargement des comptes
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                accounts = json.load(f)
        else:
            accounts = {}

        # Chargement des actifs
        if os.path.exists(ASSETS_FILE):
            with open(ASSETS_FILE, "r", encoding="utf-8") as f:
                assets_data = json.load(f)
                # Convertir les dictionnaires en objets Asset
                assets = [Asset.from_dict(asset_data) for asset_data in assets_data]
        else:
            assets = []

        # Chargement de l'historique
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []

        return banks, accounts, assets, history

    @staticmethod
    def save_data(
            banks: Dict[str, Dict[str, Any]],
            accounts: Dict[str, Dict[str, Any]],
            assets: List[Asset],
            history: List[Dict[str, Any]]
    ) -> None:
        """
        Sauvegarde les données dans les fichiers JSON

        Args:
            banks: Dictionnaire des banques
            accounts: Dictionnaire des comptes
            assets: Liste des actifs
            history: Liste des points d'historique
        """
        DataService.initialize_data_dir()

        with open(BANKS_FILE, "w", encoding="utf-8") as f:
            json.dump(banks, f, ensure_ascii=False, indent=2)

        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)

        # Convertir les objets Asset en dictionnaires pour la sérialisation
        assets_data = [asset.to_dict() for asset in assets]
        with open(ASSETS_FILE, "w", encoding="utf-8") as f:
            json.dump(assets_data, f, ensure_ascii=False, indent=2)

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    @staticmethod
    def record_history_entry(assets: List[Asset], history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enregistre un point d'historique pour tous les actifs

        Args:
            assets: Liste des actifs
            history: Liste des points d'historique existants

        Returns:
            Liste mise à jour des points d'historique
        """
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Vérifier si on a déjà un enregistrement pour aujourd'hui
        if history and history[-1]["date"] == current_date:
            # Mettre à jour l'entrée existante
            history[-1]["assets"] = {asset.id: asset.valeur_actuelle for asset in assets}
            history[-1]["total"] = sum(asset.valeur_actuelle for asset in assets)
        else:
            # Créer une nouvelle entrée
            history.append({
                "date": current_date,
                "assets": {asset.id: asset.valeur_actuelle for asset in assets},
                "total": sum(asset.valeur_actuelle for asset in assets)
            })

        return history