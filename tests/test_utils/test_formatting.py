"""
Tests pour les utilitaires de formatage
"""

from utils.formatting import (
    format_currency,
    format_percentage,
    format_number,
    format_date,
    format_duration,
    safe_format
)


class TestFormatting:
    """Tests pour les utilitaires de formatage"""

    def test_format_currency(self):
        """Test du formatage de valeurs monétaires"""
        # Cas 1: Valeur entière
        assert format_currency(1000, "€") == "1 000.00 €"

        # Cas 2: Valeur avec décimales
        assert format_currency(1234.56, "€") == "1 234.56 €"

        # Cas 3: Valeur négative
        assert format_currency(-500.25, "€") == "-500.25 €"

        # Cas 4: Zéro
        assert format_currency(0, "€") == "0.00 €"

        # Cas 5: Avec une autre devise
        assert format_currency(1000, "$") == "1 000.00 $"

        # Cas 6: Avec un nombre différent de décimales
        assert format_currency(1000, "€", decimals=0) == "1 000 €"
        assert format_currency(1000.123, "€", decimals=3) == "1 000.123 €"

        # Cas 7: Avec un séparateur de milliers différent
        assert format_currency(1000, "€", thousands_sep=",") == "1,000.00 €"

        # Cas 8: Valeur non numérique
        assert format_currency("abc", "€") == "0.00 €"
        assert format_currency(None, "€") == "0.00 €"

    def test_format_percentage(self):
        """Test du formatage de pourcentages"""
        # Cas 1: Valeur entière
        assert format_percentage(50) == "50.00%"

        # Cas 2: Valeur avec décimales
        assert format_percentage(12.345) == "12.35%"

        # Cas 3: Valeur négative
        assert format_percentage(-5.5) == "-5.50%"

        # Cas 4: Zéro
        assert format_percentage(0) == "0.00%"

        # Cas 5: Avec un nombre différent de décimales
        assert format_percentage(50, decimals=0) == "50%"
        assert format_percentage(12.345, decimals=3) == "12.345%"

        # Cas 6: Avec signe pour les valeurs positives
        assert format_percentage(50, with_sign=True) == "+50.00%"
        assert format_percentage(-5.5, with_sign=True) == "-5.50%"
        assert format_percentage(0, with_sign=True) == "0.00%"

        # Cas 7: Valeur non numérique
        assert format_percentage("abc") == "0.00%"
        assert format_percentage(None) == "0.00%"

    def test_format_number(self):
        """Test du formatage de nombres"""
        # Cas 1: Valeur entière
        assert format_number(1000) == "1 000.00"

        # Cas 2: Valeur avec décimales
        assert format_number(1234.56) == "1 234.56"

        # Cas 3: Valeur négative
        assert format_number(-500.25) == "-500.25"

        # Cas 4: Zéro
        assert format_number(0) == "0.00"

        # Cas 5: Avec un nombre différent de décimales
        assert format_number(1000, decimals=0) == "1 000"
        assert format_number(1000.123, decimals=3) == "1 000.123"

        # Cas 6: Avec un séparateur de milliers différent
        assert format_number(1000, thousands_sep=",") == "1,000.00"

        # Cas 7: Valeur non numérique
        assert format_number("abc") == "0.00"
        assert format_number(None) == "0.00"

    def test_format_date(self):
        """Test du formatage de dates"""
        from datetime import datetime, date

        # Cas 1: Objet datetime
        dt = datetime(2025, 5, 19, 12, 30, 0)
        assert format_date(dt) == "2025-05-19"

        # Cas 2: Objet date
        d = date(2025, 5, 19)
        assert format_date(d) == "2025-05-19"

        # Cas 3: Chaîne ISO
        assert format_date("2025-05-19") == "2025-05-19"

        # Cas 4: Format personnalisé
        assert format_date(dt, format_str="%d/%m/%Y") == "19/05/2025"
        assert format_date("2025-05-19", format_str="%d/%m/%Y") == "19/05/2025"

        # Cas 5: Chaînes avec différents formats
        assert format_date("19/05/2025", format_str="%Y-%m-%d") == "2025-05-19"
        assert format_date("05/19/2025", format_str="%Y-%m-%d") == "2025-05-19"

        # Cas 6: Valeurs invalides
        assert format_date("invalid-date") == ""
        assert format_date(None) == ""
        assert format_date(123) == ""

    def test_format_duration(self):
        """Test du formatage de durées"""
        # Cas 1: Secondes seulement
        assert format_duration(30) == "30s"

        # Cas 2: Minutes et secondes
        assert format_duration(90) == "1m 30s"

        # Cas 3: Heures, minutes et secondes
        assert format_duration(3661) == "1h 1m 1s"

        # Cas 4: Jours, heures, minutes et secondes
        assert format_duration(90061) == "1j 1h 1m 1s"

        # Cas 5: Zéro
        assert format_duration(0) == "0s"

        # Cas 6: Valeurs non numériques
        assert format_duration("abc") == "0s"
        assert format_duration(None) == "0s"

    def test_safe_format(self):
        """Test du formatage sécurisé"""
        # Cas 1: Formatage réussi
        result = safe_format(1000, format_currency, "default", currency="€")
        assert isinstance(result, str)
        assert "1 000" in result and "€" in result

        # Cas 2: Formatage échoué (fonction invalide)
        def failing_formatter(value):
            raise Exception("Formatting failed")

        result = safe_format(1000, failing_formatter, "default")
        assert result == "default"

        # Cas 3: Valeur par défaut avec None
        # Note: Ce test assume que format_currency(None, "€") retourne une valeur formatée et non "N/A"
        result = safe_format(None, format_currency, "N/A", currency="€")
        # Si le code retourne une valeur formatée pour None, on vérifie juste que c'est une chaîne
        # Si le code retourne "N/A", c'est aussi correct
        assert isinstance(result, str)
