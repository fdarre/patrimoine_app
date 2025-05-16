"""
Service pour la récupération des prix des actifs financiers avec Yahoo Finance
"""
import requests
from typing import Dict, Any, Optional, Union
import json
import os
from datetime import datetime, timedelta
import yfinance as yf
import logging

# Chemins des fichiers cache
ISIN_CACHE_FILE = "data/isin_prices_cache.json"
ISIN_SYMBOL_MAP_FILE = "data/isin_symbol_map.json"
METALS_CACHE_FILE = "data/metals_prices_cache.json"

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PriceService:
    """Service pour la récupération des prix des actifs financiers"""

    @staticmethod
    def get_price_by_isin(isin: str, force_refresh: bool = False) -> Optional[float]:
        """
        Récupère le prix d'un actif via son code ISIN en utilisant Yahoo Finance

        Args:
            isin: Code ISIN de l'actif
            force_refresh: Forcer le rafraîchissement du cache

        Returns:
            Prix de l'actif ou None si non disponible
        """
        # Essayer de charger depuis le cache
        cache_data = PriceService._load_isin_cache()

        # Vérifier si le prix est dans le cache et s'il est valide (moins de 24h)
        if not force_refresh and cache_data and isin in cache_data:
            price_data = cache_data[isin]
            cache_time = datetime.fromisoformat(price_data["timestamp"])
            if datetime.now() - cache_time < timedelta(hours=24):
                return price_data.get("price")

        # Récupérer le symbole Yahoo Finance correspondant à cet ISIN
        symbol = PriceService._get_yahoo_symbol_for_isin(isin)

        if not symbol:
            logger.warning(f"Symbole Yahoo Finance non trouvé pour l'ISIN: {isin}")
            return None

        try:
            # Récupérer les données de Yahoo Finance
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Récupérer le prix actuel
            # Yahoo Finance peut renvoyer différents types de prix selon l'actif
            price = None
            for price_field in ["currentPrice", "regularMarketPrice", "previousClose", "ask", "bid"]:
                if price_field in info and info[price_field] is not None:
                    price = float(info[price_field])
                    break

            if price is None or price <= 0:
                # Si aucun prix n'est trouvé, essayer de récupérer l'historique récent
                hist = ticker.history(period="1d")
                if not hist.empty and "Close" in hist.columns:
                    price = float(hist["Close"].iloc[-1])

            # Si on a un prix valide, mettre à jour le cache
            if price and price > 0:
                if cache_data is None:
                    cache_data = {}

                cache_data[isin] = {
                    "timestamp": datetime.now().isoformat(),
                    "price": price,
                    "symbol": symbol
                }
                PriceService._save_isin_cache(cache_data)

                # Enregistrer le symbole dans la correspondance ISIN-Symbole
                PriceService._save_isin_symbol_mapping(isin, symbol)

                return price

            return None

        except Exception as e:
            logger.error(f"Erreur lors de la récupération du prix pour {isin}: {str(e)}")

            # En cas d'exception, utiliser le cache si disponible
            if cache_data and isin in cache_data:
                return cache_data[isin].get("price")
            return None

    @staticmethod
    def _get_yahoo_symbol_for_isin(isin: str) -> Optional[str]:
        """
        Trouve le symbole Yahoo Finance correspondant à un ISIN

        Args:
            isin: Code ISIN

        Returns:
            Symbole Yahoo Finance ou None si non trouvé
        """
        # Charger la correspondance ISIN-Symbole depuis le fichier
        mapping = PriceService._load_isin_symbol_map()

        # Si l'ISIN est déjà dans la correspondance, utiliser le symbole enregistré
        if mapping and isin in mapping:
            return mapping[isin]

        # Essayer différents suffixes d'exchanges courants pour les actions européennes
        exchanges = ["", ".PA", ".DE", ".L", ".MI", ".AS", ".BR", ".VI", ".MC", ".LS", ".SW", ".ST"]

        for exchange in exchanges:
            try:
                # Essayer avec l'ISIN directement + suffixe exchange
                test_symbol = f"{isin}{exchange}"
                ticker = yf.Ticker(test_symbol)
                info = ticker.info

                # Vérifier si on a récupéré des infos valides
                if "regularMarketPrice" in info or "currentPrice" in info:
                    # Enregistrer la correspondance trouvée
                    PriceService._save_isin_symbol_mapping(isin, test_symbol)
                    return test_symbol
            except:
                continue

        # Si aucun symbole n'est trouvé, rechercher via l'API de recherche de Yahoo Finance
        try:
            search_url = f"https://query2.finance.yahoo.com/v1/finance/search?q={isin}"
            response = requests.get(search_url)
            if response.status_code == 200:
                data = response.json()
                quotes = data.get("quotes", [])

                # Chercher le premier résultat valide
                for quote in quotes:
                    if "symbol" in quote:
                        symbol = quote["symbol"]
                        # Vérifier que le symbole est valide
                        ticker = yf.Ticker(symbol)
                        info = ticker.info
                        if "regularMarketPrice" in info or "currentPrice" in info:
                            # Enregistrer la correspondance trouvée
                            PriceService._save_isin_symbol_mapping(isin, symbol)
                            return symbol
        except:
            pass

        # Aucun symbole trouvé
        return None

    @staticmethod
    def get_metal_price(metal_type: str, force_refresh: bool = False) -> Optional[float]:
        """
        Récupère le prix d'un métal précieux

        Args:
            metal_type: Type de métal (gold, silver, platinum, palladium)
            force_refresh: Forcer le rafraîchissement du cache

        Returns:
            Prix par once en USD ou None si non disponible
        """
        # Correspondance entre métaux et leurs symboles Yahoo Finance
        metals_symbols = {
            "gold": "GC=F",      # Contrat à terme sur l'or
            "silver": "SI=F",    # Contrat à terme sur l'argent
            "platinum": "PL=F",  # Contrat à terme sur le platine
            "palladium": "PA=F"  # Contrat à terme sur le palladium
        }

        symbol = metals_symbols.get(metal_type.lower())
        if not symbol:
            return None

        # Essayer de charger depuis le cache
        cache_data = PriceService._load_metals_cache()

        # Vérifier si le prix est dans le cache et s'il est valide (moins de 1h)
        if not force_refresh and cache_data and metal_type in cache_data:
            price_data = cache_data[metal_type]
            cache_time = datetime.fromisoformat(price_data["timestamp"])
            if datetime.now() - cache_time < timedelta(hours=1):
                return price_data.get("price")

        try:
            # Récupérer les données de Yahoo Finance
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Récupérer le prix actuel
            price = None
            for price_field in ["regularMarketPrice", "previousClose", "ask", "bid"]:
                if price_field in info and info[price_field] is not None:
                    price = float(info[price_field])
                    break

            if price is None or price <= 0:
                # Si aucun prix n'est trouvé, essayer de récupérer l'historique récent
                hist = ticker.history(period="1d")
                if not hist.empty and "Close" in hist.columns:
                    price = float(hist["Close"].iloc[-1])

            # Si on a un prix valide, mettre à jour le cache
            if price and price > 0:
                if cache_data is None:
                    cache_data = {}

                cache_data[metal_type] = {
                    "timestamp": datetime.now().isoformat(),
                    "price": price
                }
                PriceService._save_metals_cache(cache_data)

                return price

            return None

        except Exception as e:
            logger.error(f"Erreur lors de la récupération du prix pour {metal_type}: {str(e)}")

            # En cas d'exception, utiliser le cache si disponible
            if cache_data and metal_type in cache_data:
                return cache_data[metal_type].get("price")
            return None

    @staticmethod
    def _load_isin_cache() -> Optional[Dict[str, Any]]:
        """
        Charge les prix ISIN depuis le cache

        Returns:
            Données du cache ou None si le cache n'existe pas
        """
        try:
            if os.path.exists(ISIN_CACHE_FILE):
                with open(ISIN_CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement du cache ISIN: {str(e)}")
        return None

    @staticmethod
    def _save_isin_cache(data: Dict[str, Any]) -> bool:
        """
        Sauvegarde les prix ISIN dans le cache

        Args:
            data: Données à sauvegarder

        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(ISIN_CACHE_FILE), exist_ok=True)

            with open(ISIN_CACHE_FILE, 'w') as f:
                json.dump(data, f)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du cache ISIN: {str(e)}")
            return False

    @staticmethod
    def _load_metals_cache() -> Optional[Dict[str, Any]]:
        """
        Charge les prix des métaux depuis le cache

        Returns:
            Données du cache ou None si le cache n'existe pas
        """
        try:
            if os.path.exists(METALS_CACHE_FILE):
                with open(METALS_CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement du cache métaux: {str(e)}")
        return None

    @staticmethod
    def _save_metals_cache(data: Dict[str, Any]) -> bool:
        """
        Sauvegarde les prix des métaux dans le cache

        Args:
            data: Données à sauvegarder

        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(METALS_CACHE_FILE), exist_ok=True)

            with open(METALS_CACHE_FILE, 'w') as f:
                json.dump(data, f)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du cache métaux: {str(e)}")
            return False

    @staticmethod
    def _load_isin_symbol_map() -> Optional[Dict[str, str]]:
        """
        Charge la correspondance ISIN-Symbole depuis le fichier

        Returns:
            Correspondance ISIN-Symbole ou None si le fichier n'existe pas
        """
        try:
            if os.path.exists(ISIN_SYMBOL_MAP_FILE):
                with open(ISIN_SYMBOL_MAP_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la correspondance ISIN-Symbole: {str(e)}")
        return {}

    @staticmethod
    def _save_isin_symbol_mapping(isin: str, symbol: str) -> bool:
        """
        Enregistre une correspondance ISIN-Symbole

        Args:
            isin: Code ISIN
            symbol: Symbole Yahoo Finance

        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            # Charger la correspondance existante
            mapping = PriceService._load_isin_symbol_map() or {}

            # Ajouter/mettre à jour la correspondance
            mapping[isin] = symbol

            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(ISIN_SYMBOL_MAP_FILE), exist_ok=True)

            # Enregistrer la correspondance mise à jour
            with open(ISIN_SYMBOL_MAP_FILE, 'w') as f:
                json.dump(mapping, f)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la correspondance ISIN-Symbole: {str(e)}")
            return False