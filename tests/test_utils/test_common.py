"""
Tests pour les utilitaires communs
"""

import pandas as pd
import pytest

from utils.common import (
    generate_uuid,
    validate_required_fields,
    safe_float_conversion,
    safe_json_loads,
    format_currency,
    format_percentage,
    chunks,
    merge_dicts,
    df_to_dict_list,
    dict_list_to_df
)
from utils.exceptions import ValidationError


class TestCommon:
    """Tests pour les utilitaires communs"""

    def test_generate_uuid(self):
        """Test de génération d'UUID"""
        # Cas 1: Génération réussie
        result = generate_uuid()

        assert result is not None
        assert isinstance(result, str)
        assert len(result) == 36  # Format UUID standard

        # Cas 2: Unicité
        result2 = generate_uuid()
        assert result != result2

    def test_validate_required_fields(self):
        """Test de validation des champs requis"""
        # Cas 1: Validation réussie
        data = {"name": "Test", "age": 30, "email": "test@example.com"}
        required_fields = ["name", "email"]

        assert validate_required_fields(data, required_fields) is True

        # Cas 2: Champ manquant
        data = {"name": "Test"}

        with pytest.raises(ValidationError):
            validate_required_fields(data, required_fields)

        # Cas 3: Champ vide
        data = {"name": "Test", "email": ""}

        with pytest.raises(ValidationError):
            validate_required_fields(data, required_fields)

        # Cas 4: Champ None
        data = {"name": "Test", "email": None}

        with pytest.raises(ValidationError):
            validate_required_fields(data, required_fields)

        # Cas 5: Champ avec espaces uniquement
        data = {"name": "Test", "email": "   "}

        with pytest.raises(ValidationError):
            validate_required_fields(data, required_fields)

    def test_safe_float_conversion(self):
        """Test de conversion sécurisée en float"""
        # Cas 1: Valeur numérique
        assert safe_float_conversion(10) == 10.0
        assert safe_float_conversion(10.5) == 10.5

        # Cas 2: Chaîne numérique
        assert safe_float_conversion("10") == 10.0
        assert safe_float_conversion("10.5") == 10.5

        # Cas 3: Valeur None
        assert safe_float_conversion(None) == 0.0
        assert safe_float_conversion(None, default=5.0) == 5.0

        # Cas 4: Chaîne non numérique
        assert safe_float_conversion("abc") == 0.0
        assert safe_float_conversion("abc", default=5.0) == 5.0

        # Cas 5: Valeur non convertible
        class NonConvertible:
            pass

        assert safe_float_conversion(NonConvertible()) == 0.0

    def test_safe_json_loads(self):
        """Test de chargement sécurisé de JSON"""
        # Cas 1: JSON valide
        json_str = '{"name": "Test", "age": 30}'
        result = safe_json_loads(json_str)

        assert result is not None
        assert isinstance(result, dict)
        assert result["name"] == "Test"
        assert result["age"] == 30

        # Cas 2: JSON invalide
        invalid_json = '{"name": "Test", age: 30}'
        result = safe_json_loads(invalid_json)

        assert result is None

        # Cas 3: Valeur par défaut spécifiée
        result = safe_json_loads(invalid_json, default={"default": True})

        assert result is not None
        assert result["default"] is True

        # Cas 4: Chaîne vide
        result = safe_json_loads("")

        assert result is None

        # Cas 5: None
        result = safe_json_loads(None)

        assert result is None

    def test_format_currency(self):
        """Test de formatage de valeurs monétaires"""
        # Cas 1: Valeur entière
        result = format_currency(1000, "€")
        assert "1 000" in result and "€" in result

        # Cas 2: Valeur avec décimales
        result = format_currency(1234.56, "€")
        assert "1 234" in result and "56" in result and "€" in result

        # Cas 3: Valeur négative
        result = format_currency(-500.25, "€")
        assert "-" in result and "500" in result and "€" in result

        # Cas 4: Devise différente
        result = format_currency(1000, "$")
        assert "1 000" in result and "$" in result

    def test_format_percentage(self):
        """Test de formatage de pourcentages"""
        # Cas 1: Valeur entière
        result = format_percentage(50)
        assert "50" in result and "%" in result

        # Cas 2: Valeur avec décimales
        result = format_percentage(12.345)
        assert "12" in result and "%" in result

        # Cas 3: Valeur négative
        result = format_percentage(-5.5)
        assert "-" in result and "5" in result and "%" in result

        # Cas 4: Avec signe pour les valeurs positives
        result = format_percentage(50, with_sign=True)
        assert "+" in result and "50" in result and "%" in result

    def test_chunks(self):
        """Test de découpage d'une liste en morceaux"""
        # Cas 1: Liste divisible
        lst = [1, 2, 3, 4, 5, 6]
        result = chunks(lst, 2)

        assert result == [[1, 2], [3, 4], [5, 6]]

        # Cas 2: Liste non divisible
        lst = [1, 2, 3, 4, 5]
        result = chunks(lst, 2)

        assert result == [[1, 2], [3, 4], [5]]

        # Cas 3: Taille de morceau supérieure à la taille de la liste
        lst = [1, 2, 3]
        result = chunks(lst, 5)

        assert result == [[1, 2, 3]]

        # Cas 4: Liste vide
        lst = []
        result = chunks(lst, 2)

        assert result == []

    def test_merge_dicts(self):
        """Test de fusion de dictionnaires"""
        # Cas 1: Fusion simple
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}

        result = merge_dicts(dict1, dict2)

        assert result == {"a": 1, "b": 2, "c": 3, "d": 4}

        # Cas 2: Clés en conflit
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}

        result = merge_dicts(dict1, dict2)

        assert result == {"a": 1, "b": 3, "c": 4}

        # Cas 3: Sous-dictionnaires
        dict1 = {"a": 1, "b": {"x": 1, "y": 2}}
        dict2 = {"b": {"y": 3, "z": 4}, "c": 5}

        result = merge_dicts(dict1, dict2)

        assert result == {"a": 1, "b": {"x": 1, "y": 3, "z": 4}, "c": 5}

        # Cas 4: Dictionnaires vides
        dict1 = {}
        dict2 = {"a": 1}

        result = merge_dicts(dict1, dict2)

        assert result == {"a": 1}

        result = merge_dicts(dict2, dict1)

        assert result == {"a": 1}

    def test_df_to_dict_list(self):
        """Test de conversion d'un DataFrame en liste de dictionnaires"""
        # Cas 1: DataFrame avec plusieurs lignes
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35]
        })

        result = df_to_dict_list(df)

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["name"] == "Alice"
        assert result[1]["age"] == 30

        # Cas 2: DataFrame vide
        df = pd.DataFrame({
            "name": [],
            "age": []
        })

        result = df_to_dict_list(df)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_dict_list_to_df(self):
        """Test de conversion d'une liste de dictionnaires en DataFrame"""
        # Cas 1: Liste de dictionnaires
        dict_list = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
            {"name": "Charlie", "age": 35}
        ]

        df = dict_list_to_df(dict_list)

        assert isinstance(df, pd.DataFrame)
        assert df.shape == (3, 2)
        assert list(df.columns) == ["name", "age"]
        assert df.loc[0, "name"] == "Alice"
        assert df.loc[1, "age"] == 30

        # Cas 2: Liste vide
        dict_list = []

        df = dict_list_to_df(dict_list)

        assert isinstance(df, pd.DataFrame)
        assert df.shape == (0, 0)

        # Cas 3: Dictionnaires avec des clés différentes
        dict_list = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30, "city": "New York"},
            {"name": "Charlie", "city": "London"}
        ]

        df = dict_list_to_df(dict_list)

        assert isinstance(df, pd.DataFrame)
        assert df.shape == (3, 3)
        assert set(df.columns) == {"name", "age", "city"}
        assert pd.isna(df.loc[2, "age"])
        assert pd.isna(df.loc[0, "city"])
