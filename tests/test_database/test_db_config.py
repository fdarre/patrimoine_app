"""
Tests pour la configuration de la base de données
"""
from unittest.mock import patch

import pytest

from database.db_config import encrypt_data, decrypt_data, encrypt_json, decrypt_json, DataCorruptionError


class TestDbConfig:
    """Tests pour les fonctions de chiffrement et déchiffrement"""

    def test_encrypt_decrypt_data(self, mock_cipher):
        """Test du chiffrement et déchiffrement de données textuelles"""
        # Cas 1: Données valides
        original_data = "Données sensibles"
        encrypted = encrypt_data(original_data)
        decrypted = decrypt_data(encrypted)

        assert encrypted is not None
        assert encrypted != original_data
        assert decrypted == original_data

        # Cas 2: Données None
        assert encrypt_data(None) is None
        assert decrypt_data(None) is None

    def test_encrypt_decrypt_json(self, mock_cipher):
        """Test du chiffrement et déchiffrement de données JSON"""
        # Cas 1: Dictionnaire valide
        original_data = {"name": "Test", "value": 123}
        encrypted = encrypt_json(original_data)
        decrypted = decrypt_json(encrypted, silent_errors=True)

        assert encrypted is not None
        assert decrypted == original_data

        # Cas 2: Données None
        assert encrypt_json(None) is None
        assert decrypt_json(None) == {}

    def test_decrypt_json_corruption(self, mock_cipher):
        """Test de détection de corruption dans le déchiffrement JSON"""
        # Simuler des données corrompues
        with patch('database.db_config.decrypt_data', return_value="[Decryption Error]"):
            # Vérifier que l'exception est levée en mode normal
            with pytest.raises(DataCorruptionError):
                decrypt_json("corrupted_data")

            # Vérifier qu'un dict vide est retourné en mode silencieux
            result = decrypt_json("corrupted_data", silent_errors=True)
            assert result == {}

        # Simuler un JSON malformé
        with patch('database.db_config.decrypt_data', return_value="not a json"):
            # Vérifier que l'exception est levée en mode normal
            with pytest.raises(DataCorruptionError):
                decrypt_json("invalid_json")

            # Vérifier qu'un dict vide est retourné en mode silencieux
            result = decrypt_json("invalid_json", silent_errors=True)
            assert result == {}

        # Simuler un JSON qui n'est pas un dictionnaire
        with patch('database.db_config.decrypt_data', return_value='"just a string"'):
            # Vérifier que l'exception est levée en mode normal
            with pytest.raises(DataCorruptionError):
                decrypt_json("non_dict_json")

            # Vérifier qu'un dict vide est retourné en mode silencieux
            result = decrypt_json("non_dict_json", silent_errors=True)
            assert result == {}
