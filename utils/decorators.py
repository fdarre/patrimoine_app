"""
Décorateurs utilitaires pour l'application
"""
import functools
import time
import streamlit as st
from typing import Callable, Any
from sqlalchemy.exc import SQLAlchemyError

from utils.exceptions import AppError, DatabaseError
from utils.logger import get_logger

logger = get_logger(__name__)


def handle_exceptions(func: Callable) -> Callable:
    """
    Décorateur pour gérer uniformément les exceptions

    Args:
        func: Fonction à décorer

    Returns:
        Fonction décorée avec gestion des exceptions
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            logger.error(f"Erreur d'application dans {func.__name__}: {e.message}")
            raise
        except SQLAlchemyError as e:
            error_msg = f"Erreur de base de données dans {func.__name__}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        except Exception as e:
            error_msg = f"Exception non gérée dans {func.__name__}: {str(e)}"
            logger.exception(error_msg)
            raise AppError(error_msg) from e

    return wrapper


def streamlit_exception_handler(func: Callable) -> Callable:
    """
    Décorateur pour gérer les exceptions et afficher des messages dans Streamlit

    Args:
        func: Fonction à décorer

    Returns:
        Fonction décorée avec gestion des exceptions Streamlit
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            st.error(f"Erreur: {e.message}")
            logger.error(f"Erreur d'application dans {func.__name__}: {e.message}")
            return None
        except Exception as e:
            st.error(f"Une erreur inattendue s'est produite. Veuillez consulter les logs pour plus de détails.")
            logger.exception(f"Exception non gérée dans {func.__name__}: {str(e)}")
            return None

    return wrapper


def timeit(func: Callable) -> Callable:
    """
    Décorateur pour mesurer le temps d'exécution d'une fonction

    Args:
        func: Fonction à décorer

    Returns:
        Fonction décorée avec mesure du temps
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(f"{func.__name__} executed in {end_time - start_time:.2f} seconds")
        return result

    return wrapper


def db_session(func: Callable) -> Callable:
    """
    Décorateur pour injecter une session de base de données

    Args:
        func: Fonction à décorer

    Returns:
        Fonction décorée avec session de base de données
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from database.db_config import get_db
        db = next(get_db())
        try:
            kwargs['db'] = db
            return func(*args, **kwargs)
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    return wrapper