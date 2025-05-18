"""
Système de validation des formulaires amélioré
"""
from typing import Dict, List, Optional, Any, Callable, Union, TypeVar, Generic
from dataclasses import dataclass, field
import re
from enum import Enum
from datetime import datetime, date

from utils.exceptions import ValidationError

# Type pour les validateurs
T = TypeVar('T')


class ValidationStatus(Enum):
    """Statut de validation d'un champ"""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    NOT_VALIDATED = "not_validated"


@dataclass
class ValidationResult:
    """Résultat de la validation d'un champ"""
    status: ValidationStatus = ValidationStatus.NOT_VALIDATED
    message: str = ""
    value: Any = None


class Validator(Generic[T]):
    """
    Classe de base pour les validateurs

    Cette classe définit l'interface commune pour tous les validateurs
    et fournit les méthodes de base pour la validation.
    """

    def __init__(self, error_message: str = "Valeur invalide"):
        """
        Initialise le validateur

        Args:
            error_message: Message d'erreur en cas d'échec de validation
        """
        self.error_message = error_message

    def validate(self, value: T) -> ValidationResult:
        """
        Valide une valeur

        Args:
            value: Valeur à valider

        Returns:
            Résultat de la validation
        """
        is_valid = self._is_valid(value)

        if is_valid:
            return ValidationResult(
                status=ValidationStatus.VALID,
                message="Valide",
                value=value
            )
        else:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=self.error_message,
                value=value
            )

    def _is_valid(self, value: T) -> bool:
        """
        Vérifie si une valeur est valide

        Args:
            value: Valeur à vérifier

        Returns:
            True si la valeur est valide, False sinon
        """
        raise NotImplementedError("Les sous-classes doivent implémenter cette méthode")


class RequiredValidator(Validator[T]):
    """Validateur pour les champs obligatoires"""

    def __init__(self, error_message: str = "Ce champ est obligatoire"):
        """
        Initialise le validateur

        Args:
            error_message: Message d'erreur en cas d'échec de validation
        """
        super().__init__(error_message)

    def _is_valid(self, value: T) -> bool:
        """
        Vérifie si une valeur est non vide

        Args:
            value: Valeur à vérifier

        Returns:
            True si la valeur est non vide, False sinon
        """
        if value is None:
            return False

        if isinstance(value, str) and not value.strip():
            return False

        if isinstance(value, (list, dict)) and not value:
            return False

        return True


class MinLengthValidator(Validator[str]):
    """Validateur pour la longueur minimale d'une chaîne"""

    def __init__(self, min_length: int, error_message: Optional[str] = None):
        """
        Initialise le validateur

        Args:
            min_length: Longueur minimale
            error_message: Message d'erreur en cas d'échec de validation
        """
        self.min_length = min_length
        message = error_message or f"La longueur minimale est de {min_length} caractères"
        super().__init__(message)

    def _is_valid(self, value: str) -> bool:
        """
        Vérifie si une chaîne a la longueur minimale requise

        Args:
            value: Chaîne à vérifier

        Returns:
            True si la chaîne a la longueur minimale requise, False sinon
        """
        if not isinstance(value, str):
            return False

        return len(value.strip()) >= self.min_length


class MaxLengthValidator(Validator[str]):
    """Validateur pour la longueur maximale d'une chaîne"""

    def __init__(self, max_length: int, error_message: Optional[str] = None):
        """
        Initialise le validateur

        Args:
            max_length: Longueur maximale
            error_message: Message d'erreur en cas d'échec de validation
        """
        self.max_length = max_length
        message = error_message or f"La longueur maximale est de {max_length} caractères"
        super().__init__(message)

    def _is_valid(self, value: str) -> bool:
        """
        Vérifie si une chaîne a la longueur maximale requise

        Args:
            value: Chaîne à vérifier

        Returns:
            True si la chaîne a la longueur maximale requise, False sinon
        """
        if not isinstance(value, str):
            return False

        return len(value.strip()) <= self.max_length


class RegexValidator(Validator[str]):
    """Validateur pour une expression régulière"""

    def __init__(self, pattern: str, error_message: str = "Format invalide"):
        """
        Initialise le validateur

        Args:
            pattern: Expression régulière
            error_message: Message d'erreur en cas d'échec de validation
        """
        self.pattern = pattern
        self.regex = re.compile(pattern)
        super().__init__(error_message)

    def _is_valid(self, value: str) -> bool:
        """
        Vérifie si une chaîne correspond à l'expression régulière

        Args:
            value: Chaîne à vérifier

        Returns:
            True si la chaîne correspond à l'expression régulière, False sinon
        """
        if not isinstance(value, str):
            return False

        return bool(self.regex.match(value))


class EmailValidator(RegexValidator):
    """Validateur pour les adresses e-mail"""

    def __init__(self, error_message: str = "Adresse e-mail invalide"):
        """
        Initialise le validateur

        Args:
            error_message: Message d'erreur en cas d'échec de validation
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        super().__init__(pattern, error_message)


class NumericValidator(Validator[Union[str, int, float]]):
    """Validateur pour les valeurs numériques"""

    def _is_valid(self, value: Union[str, int, float]) -> bool:
        """
        Vérifie si une valeur est numérique

        Args:
            value: Valeur à vérifier

        Returns:
            True si la valeur est numérique, False sinon
        """
        if isinstance(value, (int, float)):
            return True

        if isinstance(value, str):
            try:
                float(value)
                return True
            except ValueError:
                return False

        return False


class RangeValidator(Validator[Union[int, float]]):
    """Validateur pour les valeurs numériques dans une plage"""

    def __init__(
            self,
            min_value: Optional[Union[int, float]] = None,
            max_value: Optional[Union[int, float]] = None,
            error_message: Optional[str] = None
    ):
        """
        Initialise le validateur

        Args:
            min_value: Valeur minimale (None pour pas de minimum)
            max_value: Valeur maximale (None pour pas de maximum)
            error_message: Message d'erreur en cas d'échec de validation
        """
        self.min_value = min_value
        self.max_value = max_value

        if min_value is not None and max_value is not None:
            message = error_message or f"La valeur doit être entre {min_value} et {max_value}"
        elif min_value is not None:
            message = error_message or f"La valeur doit être supérieure ou égale à {min_value}"
        elif max_value is not None:
            message = error_message or f"La valeur doit être inférieure ou égale à {max_value}"
        else:
            message = error_message or "Valeur hors limites"

        super().__init__(message)

    def _is_valid(self, value: Union[int, float]) -> bool:
        """
        Vérifie si une valeur est dans la plage spécifiée

        Args:
            value: Valeur à vérifier

        Returns:
            True si la valeur est dans la plage, False sinon
        """
        try:
            # Convertir la valeur en nombre si c'est une chaîne
            if isinstance(value, str):
                value = float(value)

            # Vérifier la plage
            if self.min_value is not None and value < self.min_value:
                return False

            if self.max_value is not None and value > self.max_value:
                return False

            return True
        except (ValueError, TypeError):
            return False


class AllocationSumValidator(Validator[Dict[str, float]]):
    """Validateur pour la somme des allocations"""

    def __init__(
            self,
            target_sum: float = 100.0,
            tolerance: float = 0.01,
            error_message: Optional[str] = None
    ):
        """
        Initialise le validateur

        Args:
            target_sum: Somme cible des allocations
            tolerance: Tolérance pour la somme
            error_message: Message d'erreur en cas d'échec de validation
        """
        self.target_sum = target_sum
        self.tolerance = tolerance
        message = error_message or f"La somme des allocations doit être de {target_sum}%"
        super().__init__(message)

    def _is_valid(self, value: Dict[str, float]) -> bool:
        """
        Vérifie si la somme des allocations est correcte

        Args:
            value: Dictionnaire des allocations

        Returns:
            True si la somme est correcte, False sinon
        """
        if not isinstance(value, dict):
            return False

        try:
            total = sum(float(v) for v in value.values())
            return abs(total - self.target_sum) <= self.tolerance
        except (ValueError, TypeError):
            return False

    def validate(self, value: Dict[str, float]) -> ValidationResult:
        """
        Valide les allocations avec un message personnalisé

        Args:
            value: Dictionnaire des allocations

        Returns:
            Résultat de la validation
        """
        is_valid = self._is_valid(value)

        if is_valid:
            return ValidationResult(
                status=ValidationStatus.VALID,
                message="Allocation valide",
                value=value
            )
        else:
            try:
                total = sum(float(v) for v in value.values())
                message = f"La somme des allocations est de {total:.2f}% (attendu: {self.target_sum}%)"
            except (ValueError, TypeError):
                message = self.error_message

            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=message,
                value=value
            )


@dataclass
class FormField:
    """Champ de formulaire avec validation"""
    name: str
    label: str
    validators: List[Validator] = field(default_factory=list)
    value: Any = None
    result: ValidationResult = field(default_factory=lambda: ValidationResult())

    def validate(self) -> ValidationResult:
        """
        Valide le champ

        Returns:
            Résultat de la validation
        """
        # Si pas de validateurs, le champ est toujours valide
        if not self.validators:
            self.result = ValidationResult(
                status=ValidationStatus.VALID,
                message="",
                value=self.value
            )
            return self.result

        # Appliquer tous les validateurs
        for validator in self.validators:
            result = validator.validate(self.value)

            # Si un validateur échoue, arrêter la validation
            if result.status == ValidationStatus.ERROR:
                self.result = result
                return self.result

        # Tous les validateurs ont réussi
        self.result = ValidationResult(
            status=ValidationStatus.VALID,
            message="",
            value=self.value
        )

        return self.result


class Form:
    """Formulaire avec validation"""

    def __init__(self, name: str):
        """
        Initialise le formulaire

        Args:
            name: Nom du formulaire
        """
        self.name = name
        self.fields: Dict[str, FormField] = {}

    def add_field(self, field: FormField) -> None:
        """
        Ajoute un champ au formulaire

        Args:
            field: Champ à ajouter
        """
        self.fields[field.name] = field

    def set_value(self, name: str, value: Any) -> None:
        """
        Définit la valeur d'un champ

        Args:
            name: Nom du champ
            value: Valeur à définir
        """
        if name in self.fields:
            self.fields[name].value = value

    def get_value(self, name: str) -> Any:
        """
        Récupère la valeur d'un champ

        Args:
            name: Nom du champ

        Returns:
            Valeur du champ
        """
        if name in self.fields:
            return self.fields[name].value
        return None

    def validate(self) -> bool:
        """
        Valide tous les champs du formulaire

        Returns:
            True si tous les champs sont valides, False sinon
        """
        is_valid = True

        for field in self.fields.values():
            result = field.validate()
            if result.status == ValidationStatus.ERROR:
                is_valid = False

        return is_valid

    def get_validation_errors(self) -> Dict[str, str]:
        """
        Récupère les erreurs de validation

        Returns:
            Dictionnaire des erreurs de validation {nom_champ: message}
        """
        errors = {}

        for name, field in self.fields.items():
            if field.result.status == ValidationStatus.ERROR:
                errors[name] = field.result.message

        return errors

    def get_values(self) -> Dict[str, Any]:
        """
        Récupère toutes les valeurs du formulaire

        Returns:
            Dictionnaire des valeurs {nom_champ: valeur}
        """
        return {name: field.value for name, field in self.fields.items()}


# Fonctions utilitaires pour créer des validateurs courants

def create_required_field(name: str, label: str, error_message: str = "Ce champ est obligatoire") -> FormField:
    """
    Crée un champ obligatoire

    Args:
        name: Nom du champ
        label: Libellé du champ
        error_message: Message d'erreur en cas d'échec de validation

    Returns:
        Champ de formulaire
    """
    return FormField(
        name=name,
        label=label,
        validators=[RequiredValidator(error_message)]
    )


def create_email_field(name: str, label: str, required: bool = True) -> FormField:
    """
    Crée un champ d'adresse e-mail

    Args:
        name: Nom du champ
        label: Libellé du champ
        required: Si le champ est obligatoire

    Returns:
        Champ de formulaire
    """
    validators = []

    if required:
        validators.append(RequiredValidator("L'adresse e-mail est obligatoire"))

    validators.append(EmailValidator())

    return FormField(
        name=name,
        label=label,
        validators=validators
    )


def create_numeric_field(
        name: str,
        label: str,
        required: bool = True,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
) -> FormField:
    """
    Crée un champ numérique

    Args:
        name: Nom du champ
        label: Libellé du champ
        required: Si le champ est obligatoire
        min_value: Valeur minimale
        max_value: Valeur maximale

    Returns:
        Champ de formulaire
    """
    validators = []

    if required:
        validators.append(RequiredValidator("Ce champ est obligatoire"))

    validators.append(NumericValidator("La valeur doit être un nombre"))

    if min_value is not None or max_value is not None:
        validators.append(RangeValidator(min_value, max_value))

    return FormField(
        name=name,
        label=label,
        validators=validators
    )