"""
Service de gestion des devises et de conversion monétaire
"""
import requests
from typing import Dict
import time
import json
import os


class CurrencyService:
    """Service pour la gestion des devises et la conversion monétaire"""

    # URL de l'API de taux de change (Open Exchange Rates, vous devrez vous inscrire pour obtenir une clé)
    API_URL = "https://open.er-api.com/v6/latest/EUR"

    # Durée de validité du cache en secondes (1 heure)
    CACHE_VALIDITY = 3600

    # Chemin du fichier de cache
    CACHE_FILE = "data/currency_rates_cache.json"

    @staticmethod
    def get_exchange_rates() -> Dict[str, float]:
        """
        Récupère les taux de change actuels depuis l'API ou le cache

        Returns:
            Dictionnaire des taux de change par rapport à l'EUR
        """
        # Vérifier si le cache existe et est valide
        if CurrencyService._is_cache_valid():
            return CurrencyService._load_cache()

        # Sinon, appeler l'API
        try:
            response = requests.get(CurrencyService.API_URL, timeout=10)
            response.raise_for_status()

            data = response.json()
            rates = data.get("rates", {})

            # Sauvegarder le cache
            CurrencyService._save_cache(rates)

            return rates
        except requests.RequestException as e:
            # En cas d'erreur, charger le cache même s'il est expiré
            if os.path.exists(CurrencyService.CACHE_FILE):
                return CurrencyService._load_cache()

            # Si pas de cache, retourner un dictionnaire avec EUR = 1
            return {"EUR": 1.0}

    @staticmethod
    def convert_to_eur(amount: float, currency: str) -> float:
        """
        Convertit un montant d'une devise en EUR

        Args:
            amount: Montant à convertir
            currency: Code de la devise source

        Returns:
            Montant converti en EUR
        """
        if currency == "EUR":
            return amount

        rates = CurrencyService.get_exchange_rates()

        # L'API retourne des taux par rapport à l'EUR
        # Si la devise n'est pas trouvée, utiliser 1.0 (pas de conversion)
        exchange_rate = rates.get(currency, 1.0)

        # Si le taux est 0, utiliser 1.0 pour éviter une division par zéro
        if exchange_rate == 0:
            exchange_rate = 1.0

        # Convertir en EUR
        return amount / exchange_rate

    @staticmethod
    def _is_cache_valid() -> bool:
        """
        Vérifie si le cache de taux de change est valide

        Returns:
            True si le cache existe et est valide, False sinon
        """
        if not os.path.exists(CurrencyService.CACHE_FILE):
            return False

        try:
            with open(CurrencyService.CACHE_FILE, "r") as f:
                cache = json.load(f)

            # Vérifier la date de mise à jour
            timestamp = cache.get("timestamp", 0)
            current_time = time.time()

            return (current_time - timestamp) < CurrencyService.CACHE_VALIDITY
        except (json.JSONDecodeError, KeyError, ValueError):
            return False

    @staticmethod
    def _load_cache() -> Dict[str, float]:
        """
        Charge les taux de change depuis le cache

        Returns:
            Dictionnaire des taux de change
        """
        try:
            with open(CurrencyService.CACHE_FILE, "r") as f:
                cache = json.load(f)

            return cache.get("rates", {"EUR": 1.0})
        except (FileNotFoundError, json.JSONDecodeError):
            return {"EUR": 1.0}

    @staticmethod
    def _save_cache(rates: Dict[str, float]) -> None:
        """
        Sauvegarde les taux de change dans le cache

        Args:
            rates: Dictionnaire des taux de change
        """
        try:
            os.makedirs(os.path.dirname(CurrencyService.CACHE_FILE), exist_ok=True)

            cache = {
                "rates": rates,
                "timestamp": time.time()
            }

            with open(CurrencyService.CACHE_FILE, "w") as f:
                json.dump(cache, f)
        except (IOError, OSError):
            # En cas d'erreur, ignorer silencieusement
            pass