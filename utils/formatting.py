"""
Fonctions utilitaires de formatage centralisées
"""
from datetime import datetime, date
from typing import Any, Union


def format_currency(
        value: Union[float, int],
        currency: str = "€",
        decimals: int = 2,
        thousands_sep: str = " "
) -> str:
    """
    Formate un nombre en valeur monétaire avec séparateurs de milliers

    Args:
        value: Valeur à formater
        currency: Symbole de la devise
        decimals: Nombre de décimales
        thousands_sep: Séparateur de milliers

    Returns:
        Chaîne formatée
    """
    try:
        # Formater le nombre avec le nombre spécifié de décimales
        formatted = f"{value:,.{decimals}f}"

        # Remplacer la virgule par le séparateur spécifié
        formatted = formatted.replace(",", thousands_sep)

        # Ajouter le symbole de devise avec un espace
        return f"{formatted} {currency}"
    except (ValueError, TypeError):
        return f"0.{('0' * decimals)} {currency}"


def format_percentage(
        value: Union[float, int],
        decimals: int = 2,
        with_sign: bool = False
) -> str:
    """
    Formate un nombre en pourcentage

    Args:
        value: Valeur à formater
        decimals: Nombre de décimales
        with_sign: Ajouter un signe + pour les valeurs positives

    Returns:
        Chaîne formatée
    """
    try:
        if with_sign and value > 0:
            return f"+{value:.{decimals}f}%"
        return f"{value:.{decimals}f}%"
    except (ValueError, TypeError):
        return f"0.{('0' * decimals)}%"


def format_number(
        value: Union[float, int],
        decimals: int = 2,
        thousands_sep: str = " "
) -> str:
    """
    Formate un nombre avec séparateurs de milliers

    Args:
        value: Valeur à formater
        decimals: Nombre de décimales
        thousands_sep: Séparateur de milliers

    Returns:
        Chaîne formatée
    """
    try:
        formatted = f"{value:,.{decimals}f}"
        return formatted.replace(",", thousands_sep)
    except (ValueError, TypeError):
        return f"0.{('0' * decimals)}"


def format_date(
        value: Union[datetime, date, str],
        format_str: str = "%Y-%m-%d"
) -> str:
    """
    Formate une date en chaîne selon le format spécifié

    Args:
        value: Date à formater (datetime, date ou chaîne iso)
        format_str: Format de sortie

    Returns:
        Date formatée ou chaîne vide si invalide
    """
    try:
        if isinstance(value, str):
            # Parser la chaîne en date
            try:
                # Essayer le format iso standard
                value = datetime.fromisoformat(value)
            except ValueError:
                # Essayer d'autres formats courants
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
                    try:
                        value = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return ""

        # Formater la date
        return value.strftime(format_str)
    except (ValueError, TypeError, AttributeError):
        return ""


def format_duration(seconds: Union[int, float]) -> str:
    """
    Formate une durée en secondes en chaîne lisible

    Args:
        seconds: Nombre de secondes

    Returns:
        Durée formatée
    """
    try:
        seconds = int(seconds)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        parts = []
        if days > 0:
            parts.append(f"{days}j")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")

        return " ".join(parts)
    except (ValueError, TypeError):
        return "0s"


def safe_format(
        value: Any,
        formatter: callable,
        default: str = "",
        **kwargs
) -> str:
    """
    Applique une fonction de formatage de manière sécurisée

    Args:
        value: Valeur à formater
        formatter: Fonction de formatage à appliquer
        default: Valeur par défaut si le formatage échoue
        **kwargs: Arguments à passer à la fonction de formatage

    Returns:
        Valeur formatée ou valeur par défaut
    """
    try:
        return formatter(value, **kwargs)
    except Exception:
        return default