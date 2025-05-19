"""
Tests pour le service de devises et de conversion monétaire
"""
import json
import os
import time
from unittest.mock import patch, MagicMock

import requests

from services.currency_service import CurrencyService


class TestCurrencyService:
    """Tests pour le service de devises et conversion monétaire"""

    def setup_method(self):
        """Préparation avant chaque test"""
        # Créer un fichier de cache temporaire pour les tests
        self.original_cache_file = CurrencyService.CACHE_FILE
        CurrencyService.CACHE_FILE = "test_currency_cache.json"

    def teardown_method(self):
        """Nettoyage après chaque test"""
        # Supprimer le fichier de cache temporaire
        if os.path.exists(CurrencyService.CACHE_FILE):
            os.remove(CurrencyService.CACHE_FILE)

        # Restaurer le chemin du fichier de cache
        CurrencyService.CACHE_FILE = self.original_cache_file

    @patch('services.currency_service.requests.get')
    @patch('services.currency_service.CurrencyService._is_cache_valid')
    @patch('services.currency_service.CurrencyService._load_cache')
    @patch('services.currency_service.CurrencyService._save_cache')
    def test_get_exchange_rates(self, mock_save_cache, mock_load_cache, mock_is_cache_valid, mock_get):
        """Test de récupération des taux de change"""
        # Configurer les mocks pour le premier appel (pas de cache valide)
        mock_is_cache_valid.return_value = False
        mock_load_cache.return_value = None

        # Simuler une réponse d'API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "base": "EUR",
            "rates": {
                "USD": 1.12,
                "GBP": 0.85,
                "JPY": 150.23,
                "CHF": 0.98,
                "EUR": 1.0
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Appeler la fonction à tester
        rates = CurrencyService.get_exchange_rates()

        # Vérifier les résultats
        assert rates is not None
        assert isinstance(rates, dict)
        assert "USD" in rates
        assert "GBP" in rates
        assert "JPY" in rates
        assert "CHF" in rates
        assert "EUR" in rates

        assert rates["USD"] == 1.12
        assert rates["EUR"] == 1.0

        # Vérifier que l'API a été appelée
        mock_get.assert_called_once_with(CurrencyService.API_URL, timeout=10)

        # Vérifier que la sauvegarde du cache a été appelée
        mock_save_cache.assert_called_once()

        # Réinitialiser les mocks pour le second test
        mock_get.reset_mock()
        mock_save_cache.reset_mock()

        # Cette fois, simuler un cache valide
        mock_is_cache_valid.return_value = True
        mock_load_cache.return_value = {
            "USD": 1.12,
            "GBP": 0.85,
            "JPY": 150.23,
            "CHF": 0.98,
            "EUR": 1.0
        }

        # Appeler à nouveau pour tester le cache
        rates2 = CurrencyService.get_exchange_rates()

        # L'API ne devrait pas être appelée car le cache est valide
        mock_get.assert_not_called()
        # Et la sauvegarde du cache ne devrait pas non plus être appelée
        mock_save_cache.assert_not_called()

        # Vérifier que nous avons bien récupéré les mêmes taux depuis le cache
        assert rates2["USD"] == 1.12
        assert rates2["EUR"] == 1.0

    @patch('services.currency_service.requests.get')
    def test_get_exchange_rates_api_error(self, mock_get):
        """Test de gestion des erreurs d'API"""
        # Simuler une erreur d'API
        mock_get.side_effect = requests.RequestException("Erreur API")

        # Créer d'abord un cache valide
        with open(CurrencyService.CACHE_FILE, "w") as f:
            json.dump({
                "timestamp": time.time(),
                "rates": {
                    "USD": 1.10,
                    "GBP": 0.84,
                    "EUR": 1.0
                }
            }, f)

        # Appeler la fonction à tester
        rates = CurrencyService.get_exchange_rates()

        # Vérifier que le service utilise le cache en cas d'erreur
        assert rates is not None
        assert "USD" in rates
        assert rates["USD"] == 1.10

        # Supprimons le cache et testons sans cache
        os.remove(CurrencyService.CACHE_FILE)

        # Appeler à nouveau
        rates_no_cache = CurrencyService.get_exchange_rates()

        # Le service devrait retourner des valeurs par défaut
        assert rates_no_cache is not None
        assert "EUR" in rates_no_cache
        assert rates_no_cache["EUR"] == 1.0

    def test_convert_to_eur(self):
        """Test de conversion vers l'euro"""
        # Créer un cache avec des taux connus pour le test
        with open(CurrencyService.CACHE_FILE, "w") as f:
            json.dump({
                "timestamp": time.time(),
                "rates": {
                    "USD": 1.10,  # 1 EUR = 1.10 USD, donc 1 USD = 1/1.10 EUR
                    "GBP": 0.85,  # 1 EUR = 0.85 GBP, donc 1 GBP = 1/0.85 EUR
                    "JPY": 150.0,  # 1 EUR = 150 JPY, donc 1 JPY = 1/150 EUR
                    "EUR": 1.0
                }
            }, f)

        # Tester différentes conversions
        # Pour l'USD: 1 USD = 1/1.10 EUR ≈ 0.909 EUR
        assert abs(CurrencyService.convert_to_eur(100.0, "USD") - 90.91) < 0.01

        # Pour le GBP: 1 GBP = 1/0.85 EUR ≈ 1.176 EUR
        assert abs(CurrencyService.convert_to_eur(100.0, "GBP") - 117.65) < 0.01

        # Pour le JPY: 1 JPY = 1/150 EUR ≈ 0.00667 EUR
        assert abs(CurrencyService.convert_to_eur(10000.0, "JPY") - 66.67) < 0.01

        # Pour l'EUR (aucune conversion)
        assert CurrencyService.convert_to_eur(100.0, "EUR") == 100.0

        # Pour une devise inconnue (devrait utiliser 1.0 par défaut)
        assert CurrencyService.convert_to_eur(100.0, "XYZ") == 100.0

        # Pour un taux de change 0 (devrait être traité comme 1.0 pour éviter division par 0)
        # Modifions le cache pour simuler un taux à 0
        with open(CurrencyService.CACHE_FILE, "w") as f:
            json.dump({
                "timestamp": time.time(),
                "rates": {
                    "ZZZ": 0.0,
                    "EUR": 1.0
                }
            }, f)
        assert CurrencyService.convert_to_eur(100.0, "ZZZ") == 100.0
