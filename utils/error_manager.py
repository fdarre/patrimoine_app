"""
Gestionnaire d'erreurs centralisé pour l'application
"""
import functools
import os
import traceback
from typing import Callable, Dict, Type

import streamlit as st

from utils.exceptions import AppError, DatabaseError, ValidationError, AuthenticationError
from utils.logger import get_logger

logger = get_logger(__name__)

# Définir la variable d'environnement ici au lieu d'utiliser st.secrets
ENV = os.environ.get("APP_ENV", "prod")

class ErrorManager:
    """
    Gestionnaire centralisé pour la gestion des erreurs et exceptions

    Cette classe offre des méthodes pour gérer les exceptions de manière uniforme
    à travers l'application, avec un affichage approprié dans l'interface utilisateur.
    """

    def __init__(self):
        """Initialise le gestionnaire d'erreurs"""
        self.error_handlers: Dict[Type[Exception], Callable] = {}
        self.register_default_handlers()

    def register_handler(self, exception_type: Type[Exception], handler: Callable) -> None:
        """
        Enregistre un gestionnaire pour un type d'exception

        Args:
            exception_type: Type d'exception
            handler: Fonction de gestion de l'exception
        """
        self.error_handlers[exception_type] = handler

    def register_default_handlers(self) -> None:
        """Enregistre les gestionnaires par défaut pour les types d'exceptions courantes"""
        self.register_handler(ValidationError, self._handle_validation_error)
        self.register_handler(DatabaseError, self._handle_database_error)
        self.register_handler(AuthenticationError, self._handle_authentication_error)
        self.register_handler(AppError, self._handle_app_error)
        self.register_handler(Exception, self._handle_generic_exception)

    def handle_exception(self, e: Exception) -> None:
        """
        Gère une exception avec le gestionnaire approprié

        Args:
            e: Exception à gérer
        """
        # Journaliser l'exception
        logger.error(f"Exception caught: {type(e).__name__}: {str(e)}")

        # Trouver le gestionnaire le plus spécifique
        handler = None
        for exc_type, h in self.error_handlers.items():
            if isinstance(e, exc_type):
                handler = h
                break

        # Si aucun gestionnaire trouvé, utiliser le gestionnaire générique
        if handler is None:
            handler = self._handle_generic_exception

        # Appeler le gestionnaire
        handler(e)

    def catch_exceptions(self, func: Callable) -> Callable:
        """
        Décorateur pour capturer et gérer les exceptions dans une fonction

        Args:
            func: Fonction à décorer

        Returns:
            Fonction décorée
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.handle_exception(e)
                return None

        return wrapper

    def _handle_validation_error(self, e: ValidationError) -> None:
        """
        Gère une erreur de validation

        Args:
            e: Erreur de validation
        """
        st.error(f"Validation Error: {e.message}")
        logger.warning(f"Validation Error: {e.message}")

    def _handle_database_error(self, e: DatabaseError) -> None:
        """
        Gère une erreur de base de données

        Args:
            e: Erreur de base de données
        """
        st.error(f"Database Error: {e.message}")
        logger.error(f"Database Error: {e.message}")

    def _handle_authentication_error(self, e: AuthenticationError) -> None:
        """
        Gère une erreur d'authentification

        Args:
            e: Erreur d'authentification
        """
        st.error(f"Authentication Error: {e.message}")
        logger.warning(f"Authentication Error: {e.message}")

    def _handle_app_error(self, e: AppError) -> None:
        """
        Gère une erreur d'application

        Args:
            e: Erreur d'application
        """
        st.error(f"Application Error: {e.message}")
        logger.error(f"Application Error: {e.message}")

    def _handle_generic_exception(self, e: Exception) -> None:
        """
        Gère une exception générique

        Args:
            e: Exception générique
        """
        # Journaliser l'erreur avec la trace complète
        logger.exception("Unhandled exception")

        # Afficher une version simplifiée dans l'interface utilisateur
        st.error("An unexpected error occurred. Please check the logs for more details.")

        # En mode développement, afficher les détails de l'erreur
        if ENV == "dev":
            with st.expander("Error details (development mode)"):
                st.code(traceback.format_exc())


# Créer une instance singleton du gestionnaire
error_manager = ErrorManager()


def catch_exceptions(func: Callable) -> Callable:
    """
    Décorateur pour capturer et gérer les exceptions dans une fonction

    Args:
        func: Fonction à décorer

    Returns:
        Fonction décorée
    """
    return error_manager.catch_exceptions(func)