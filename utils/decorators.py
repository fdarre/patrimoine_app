"""
Décorateurs utilitaires pour l'application
"""
import functools
import time
from typing import Callable

import streamlit as st

from utils.exceptions import AppError
from utils.logger import get_logger

logger = get_logger(__name__)


# La fonction handle_exceptions a été supprimée car remplacée par catch_exceptions dans utils.error_manager

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