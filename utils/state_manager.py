"""
Gestionnaire d'état centralisé pour l'application Streamlit
"""
from typing import Any, Dict, List, Optional, Set, Union, Callable
import streamlit as st
import json
import hashlib
from datetime import datetime


class StateManager:
    """
    Gestionnaire centralisé pour l'état de session Streamlit

    Cette classe fournit une interface unifiée pour manipuler st.session_state,
    ce qui améliore la cohérence et évite les duplications de code à travers l'application.
    """

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de l'état de session

        Args:
            key: Clé de l'état
            default: Valeur par défaut si la clé n'existe pas

        Returns:
            Valeur associée à la clé ou valeur par défaut
        """
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any) -> None:
        """
        Définit une valeur dans l'état de session

        Args:
            key: Clé de l'état
            value: Valeur à stocker
        """
        st.session_state[key] = value

    @staticmethod
    def delete(key: str) -> None:
        """
        Supprime une clé de l'état de session

        Args:
            key: Clé à supprimer
        """
        if key in st.session_state:
            del st.session_state[key]

    @staticmethod
    def clear_all() -> None:
        """
        Vide tout l'état de session
        """
        for key in list(st.session_state.keys()):
            del st.session_state[key]

    @staticmethod
    def exists(key: str) -> bool:
        """
        Vérifie si une clé existe dans l'état de session

        Args:
            key: Clé à vérifier

        Returns:
            True si la clé existe, False sinon
        """
        return key in st.session_state

    @staticmethod
    def get_or_create(key: str, factory: Callable[[], Any]) -> Any:
        """
        Récupère une valeur ou la crée si elle n'existe pas

        Args:
            key: Clé de l'état
            factory: Fonction qui crée la valeur par défaut

        Returns:
            Valeur associée à la clé
        """
        if key not in st.session_state:
            st.session_state[key] = factory()
        return st.session_state[key]

    @staticmethod
    def update(key: str, value: Any) -> bool:
        """
        Met à jour une valeur si la clé existe

        Args:
            key: Clé de l'état
            value: Nouvelle valeur

        Returns:
            True si la mise à jour a réussi, False si la clé n'existe pas
        """
        if key in st.session_state:
            st.session_state[key] = value
            return True
        return False

    @staticmethod
    def increment(key: str, amount: int = 1) -> int:
        """
        Incrémente une valeur numérique

        Args:
            key: Clé de l'état
            amount: Montant à ajouter

        Returns:
            Nouvelle valeur
        """
        if key not in st.session_state:
            st.session_state[key] = 0
        st.session_state[key] += amount
        return st.session_state[key]

    @staticmethod
    def toggle(key: str) -> bool:
        """
        Inverse une valeur booléenne

        Args:
            key: Clé de l'état

        Returns:
            Nouvelle valeur
        """
        if key not in st.session_state:
            st.session_state[key] = False
        st.session_state[key] = not st.session_state[key]
        return st.session_state[key]

    # Méthodes spécifiques à l'application

    @staticmethod
    def set_edit_mode(asset_id: str, state: bool = True) -> None:
        """
        Active ou désactive le mode d'édition pour un actif

        Args:
            asset_id: ID de l'actif
            state: État du mode d'édition
        """
        key = f"edit_asset_{asset_id}"
        st.session_state[key] = state

    @staticmethod
    def is_edit_mode(asset_id: str) -> bool:
        """
        Vérifie si un actif est en mode d'édition

        Args:
            asset_id: ID de l'actif

        Returns:
            True si l'actif est en mode d'édition, False sinon
        """
        key = f"edit_asset_{asset_id}"
        return st.session_state.get(key, False)

    @staticmethod
    def set_view_details(asset_id: str) -> None:
        """
        Active l'affichage des détails pour un actif

        Args:
            asset_id: ID de l'actif
        """
        st.session_state['view_asset_details'] = asset_id

    @staticmethod
    def clear_view_details() -> None:
        """
        Désactive l'affichage des détails
        """
        if 'view_asset_details' in st.session_state:
            del st.session_state['view_asset_details']

    @staticmethod
    def set_current_page(page_name: str) -> None:
        """
        Définit la page courante

        Args:
            page_name: Nom de la page
        """
        st.session_state["navigation"] = page_name

    @staticmethod
    def mark_task_completed(task_id: str) -> None:
        """
        Marque une tâche comme terminée

        Args:
            task_id: ID de la tâche
        """
        if 'completed_tasks' not in st.session_state:
            st.session_state['completed_tasks'] = set()
        st.session_state['completed_tasks'].add(task_id)

    @staticmethod
    def is_task_completed(task_id: str) -> bool:
        """
        Vérifie si une tâche est marquée comme terminée

        Args:
            task_id: ID de la tâche

        Returns:
            True si la tâche est terminée, False sinon
        """
        if 'completed_tasks' not in st.session_state:
            st.session_state['completed_tasks'] = set()
        return task_id in st.session_state['completed_tasks']

    @staticmethod
    def get_pagination_index(key_prefix: str) -> int:
        """
        Récupère l'index de pagination pour un préfixe donné

        Args:
            key_prefix: Préfixe de la clé

        Returns:
            Index de pagination (0-indexed)
        """
        pagination_key = f"{key_prefix}_page"
        return st.session_state.get(pagination_key, 0)

    @staticmethod
    def set_pagination_index(key_prefix: str, index: int) -> None:
        """
        Définit l'index de pagination pour un préfixe donné

        Args:
            key_prefix: Préfixe de la clé
            index: Nouvel index (0-indexed)
        """
        pagination_key = f"{key_prefix}_page"
        st.session_state[pagination_key] = index

    @staticmethod
    def generate_key(base: str, *args) -> str:
        """
        Génère une clé unique basée sur les arguments

        Args:
            base: Base de la clé
            *args: Arguments supplémentaires pour la clé

        Returns:
            Clé générée
        """
        key_str = f"{base}_{'_'.join(str(arg) for arg in args)}"
        return key_str

    @staticmethod
    def get_all_keys() -> List[str]:
        """
        Récupère toutes les clés de l'état de session

        Returns:
            Liste des clés
        """
        return list(st.session_state.keys())


# Créer une instance du gestionnaire
state = StateManager()