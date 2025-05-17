"""
Utilitaires pour les indicateurs de chargement et les notifications
"""
import streamlit as st
import time
from typing import Optional, Callable, Any
from contextlib import contextmanager


@contextmanager
def loading_indicator(message: str = "Chargement...", success_message: Optional[str] = None):
    """
    Contextmanager qui affiche un indicateur de chargement pendant une opération
    et optionnellement un message de succès à la fin.
    
    Args:
        message: Message à afficher pendant le chargement
        success_message: Message de succès à afficher après le chargement (optional)
    
    Usage:
        with loading_indicator("Chargement des données...", "Données chargées"):
            # Code à exécuter pendant le chargement
            data = load_data()
    """
    # Créer un placeholder pour le spinner
    placeholder = st.empty()
    
    # Afficher le spinner
    with placeholder.container():
        with st.spinner(message):
            try:
                # Exécuter le code dans le contexte
                yield
                # Afficher le message de succès si fourni
                if success_message:
                    placeholder.success(success_message)
                    # Effacer après un court délai
                    time.sleep(1.5)
                    placeholder.empty()
            except Exception as e:
                # En cas d'erreur, afficher un message d'erreur
                placeholder.error(f"Erreur: {str(e)}")
                # Ne pas effacer automatiquement en cas d'erreur
                raise


def show_notification(message: str, type: str = "info", duration: int = 3):
    """
    Affiche une notification temporaire
    
    Args:
        message: Message à afficher
        type: Type de notification ('info', 'success', 'warning', 'error')
        duration: Durée d'affichage en secondes
    """
    # Créer un placeholder pour la notification
    placeholder = st.empty()
    
    # Définir le style selon le type
    if type == "success":
        placeholder.success(message)
    elif type == "warning":
        placeholder.warning(message)
    elif type == "error":
        placeholder.error(message)
    else:
        placeholder.info(message)
    
    # Créer un thread pour effacer la notification après un délai
    if duration > 0:
        # Utiliser un timer dans un thread séparé
        import threading
        timer = threading.Timer(duration, placeholder.empty)
        timer.start()
        

def with_progress_bar(func: Callable, steps: int, message: str = "Traitement en cours...") -> Any:
    """
    Exécute une fonction avec une barre de progression
    
    Args:
        func: Fonction à exécuter
        steps: Nombre d'étapes à afficher dans la barre de progression
        message: Message à afficher pendant le traitement
        
    Returns:
        Résultat de la fonction
    """
    # Créer une barre de progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Fonction pour mettre à jour la progression
    def update_progress(step, step_message=None):
        progress = step / steps
        progress_bar.progress(progress)
        if step_message:
            status_text.text(f"{message} ({step}/{steps}) - {step_message}")
        else:
            status_text.text(f"{message} ({step}/{steps})")
    
    try:
        # Appeler la fonction avec la fonction de mise à jour
        result = func(update_progress)
        # Compléter la barre de progression
        progress_bar.progress(1.0)
        status_text.text("Traitement terminé")
        time.sleep(1)
        return result
    finally:
        # Nettoyer
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
