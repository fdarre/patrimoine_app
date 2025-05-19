"""
Utilitaires pour les indicateurs de chargement et les notifications - Version Streamlit
"""
import time
from contextlib import contextmanager
from typing import Optional

import streamlit as st


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
    # Créer un placeholder pour le spinner et le feedback
    placeholder = st.empty()

    # Afficher le spinner natif de Streamlit
    with placeholder.container():
        with st.spinner(message):
            try:
                # Exécuter le code dans le contexte
                yield
                # Afficher le message de succès si fourni
                if success_message:
                    # Utiliser success natif de Streamlit
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
    Affiche une notification temporaire dans l'interface

    Args:
        message: Message à afficher
        type: Type de notification ('info', 'success', 'warning', 'error')
        duration: Durée d'affichage en secondes (0 pour permanent)
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

    # Pour les notifications temporaires, programmer leur suppression
    if duration > 0:
        # Cette solution n'est pas idéale car elle bloque le thread,
        # mais Streamlit n'offre pas de mécanisme natif pour les notifications temporaires
        # sans utiliser JavaScript. Pour une meilleure solution, il faudrait
        # implémenter un système de gestion de notifications dans session_manager.
        time.sleep(duration)
        placeholder.empty()


def with_progress_bar(iterable, message: str = "Traitement en cours..."):
    """
    Affiche une barre de progression pendant l'itération sur un itérable

    Args:
        iterable: Itérable à parcourir
        message: Message à afficher pendant le traitement

    Yields:
        Éléments de l'itérable
    """
    # Cette fonction est beaucoup plus simple avec st.progress()
    progress_text = st.empty()
    progress_bar = st.progress(0)

    # Calculer le nombre total d'éléments si possible
    try:
        total = len(iterable)
    except (TypeError, AttributeError):
        # Si l'itérable n'a pas de longueur définie, on ne peut pas faire de progression
        progress_text.text(f"{message} (progression indéterminée)")
        for item in iterable:
            yield item
        progress_text.empty()
        progress_bar.empty()
        return

    # Parcourir l'itérable avec progression
    for i, item in enumerate(iterable):
        # Mettre à jour la progression
        progress = (i + 1) / total
        progress_bar.progress(progress)
        progress_text.text(f"{message} ({i+1}/{total})")

        # Yield l'élément
        yield item

    # Terminer avec 100%
    progress_bar.progress(1.0)
    progress_text.text("Traitement terminé")
    time.sleep(0.5)

    # Nettoyer l'interface
    progress_text.empty()
    progress_bar.empty()


def show_processing_steps(steps: list, current_step: int = 0):
    """
    Affiche les étapes d'un traitement avec l'étape actuelle mise en évidence

    Args:
        steps: Liste des étapes (textes)
        current_step: Index de l'étape actuelle (0-indexed)
    """
    # Créer un conteneur pour les étapes
    with st.container():
        # Créer une colonne par étape
        cols = st.columns(len(steps))

        for i, (col, step) in enumerate(zip(cols, steps)):
            with col:
                # Définir le style selon si c'est l'étape actuelle ou non
                if i < current_step:
                    # Étape terminée
                    st.markdown(f"""
                    <div style="text-align:center; color:#40c057;">
                        <div style="font-size:24px;">✓</div>
                        <div>{step}</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif i == current_step:
                    # Étape actuelle
                    st.markdown(f"""
                    <div style="text-align:center; color:#4e79a7; font-weight:bold;">
                        <div style="font-size:24px;">⚡</div>
                        <div>{step}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Étape future
                    st.markdown(f"""
                    <div style="text-align:center; color:#6c757d;">
                        <div style="font-size:24px;">○</div>
                        <div>{step}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Ajouter une barre de progression
        progress = (current_step) / (len(steps) - 1) if len(steps) > 1 else 1.0
        st.progress(min(1.0, max(0.0, progress)))