"""
Helpers pour l'interface utilisateur Streamlit
"""
import hashlib
import threading
import time
from typing import List, Any, Optional, Callable

import pandas as pd
import streamlit as st

from utils.logger import get_logger

logger = get_logger(__name__)


def show_message(message: str, type: str = "info", auto_dismiss: bool = False, key: Optional[str] = None):
    """
    Affiche un message temporaire dans l'interface

    Args:
        message: Message à afficher
        type: Type de message ('info', 'success', 'warning', 'error')
        auto_dismiss: Si le message doit disparaître automatiquement
        key: Clé unique pour le composant
    """
    # Générer une clé si non fournie
    if key is None:
        key = f"msg_{hashlib.md5(message.encode()).hexdigest()[:8]}"

    # Placeholder pour le message
    placeholder = st.empty()

    # Afficher le message selon le type
    if type == "success":
        placeholder.success(message, icon="✅")
    elif type == "warning":
        placeholder.warning(message, icon="⚠️")
    elif type == "error":
        placeholder.error(message, icon="❌")
    else:
        placeholder.info(message, icon="ℹ️")

    # Auto-dismiss après 3 secondes
    if auto_dismiss:
        def dismiss():
            time.sleep(3)
            placeholder.empty()

        threading.Thread(target=dismiss, daemon=True).start()

    return placeholder


def confirmation_dialog(title: str, message: str, confirm_label: str = "Confirmer",
                        cancel_label: str = "Annuler", key: Optional[str] = None) -> bool:
    """
    Affiche une boîte de dialogue de confirmation

    Args:
        title: Titre de la boîte de dialogue
        message: Message à afficher
        confirm_label: Texte du bouton de confirmation
        cancel_label: Texte du bouton d'annulation
        key: Clé unique pour le composant

    Returns:
        True si confirmé, False sinon
    """
    # Générer une clé si non fournie
    if key is None:
        key = f"dialog_{hashlib.md5(title.encode()).hexdigest()[:8]}"

    # Afficher la boîte de dialogue
    with st.expander(title, expanded=True):
        st.markdown(message)

        col1, col2 = st.columns(2)
        with col1:
            confirm = st.button(confirm_label, key=f"{key}_confirm")
        with col2:
            cancel = st.button(cancel_label, key=f"{key}_cancel")

        if cancel:
            return False
        return confirm


def searchable_selectbox(label: str, options: List[Any], default_index: int = 0,
                         key: Optional[str] = None, format_func: Optional[Callable] = None):
    """
    Sélecteur avec recherche

    Args:
        label: Label du sélecteur
        options: Liste d'options
        default_index: Index de l'option par défaut
        key: Clé unique pour le composant
        format_func: Fonction pour formater les valeurs affichées

    Returns:
        Option sélectionnée
    """
    # Générer une clé si non fournie
    if key is None:
        key = f"select_{hashlib.md5(label.encode()).hexdigest()[:8]}"

    # Texte de recherche
    search_key = f"{key}_search"
    search = st.text_input(f"Rechercher dans {label}", key=search_key)

    # Filtrer les options selon la recherche
    if search:
        # Appliquer la fonction de formatage pour la recherche si fournie
        if format_func:
            filtered_options = [opt for opt in options
                                if search.lower() in format_func(opt).lower()]
        else:
            filtered_options = [opt for opt in options
                                if search.lower() in str(opt).lower()]
    else:
        filtered_options = options

    # Afficher le sélecteur filtré
    if filtered_options:
        index = min(default_index, len(filtered_options) - 1) if filtered_options else 0
        return st.selectbox(
            label,
            options=filtered_options,
            index=index,
            format_func=format_func if format_func else lambda x: x,
            key=key
        )
    else:
        st.info(f"Aucun résultat pour '{search}'")
        return None


def custom_metric(label: str, value: Any, delta: Optional[Any] = None,
                  help: Optional[str] = None, color: Optional[str] = None):
    """
    Affiche une métrique personnalisée

    Args:
        label: Label de la métrique
        value: Valeur principale
        delta: Variation (optionnel)
        help: Texte d'aide (optionnel)
        color: Couleur de la valeur (optionnel)
    """
    # Style pour la valeur
    value_style = f'color: {color};' if color else ''

    # Calculer la classe pour le delta
    if delta is not None:
        try:
            delta_float = float(delta)
            delta_class = "positive" if delta_float >= 0 else "negative"
            delta_sign = "+" if delta_float > 0 else ""
            delta_display = f'<div class="{delta_class}">{delta_sign}{delta}</div>'
        except (ValueError, TypeError):
            delta_display = f'<div>{delta}</div>'
    else:
        delta_display = ''

    # Afficher la métrique
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 0.8rem; color: #adb5bd;">{label}</div>
        <div style="font-size: 1.5rem; font-weight: bold; {value_style}">{value}</div>
        {delta_display}
    </div>
    """, unsafe_allow_html=True)

    # Afficher l'aide si fournie
    if help:
        st.markdown(f'<div style="font-size: 0.8rem; color: #adb5bd;">{help}</div>',
                    unsafe_allow_html=True)


def dynamic_filter(df: pd.DataFrame, column: str, label: str, default: str = "Tous",
                   key: Optional[str] = None, format_func: Optional[Callable] = None):
    """
    Crée un filtre dynamique pour un DataFrame

    Args:
        df: DataFrame à filtrer
        column: Colonne à filtrer
        label: Label du filtre
        default: Valeur par défaut ("Tous" pour aucun filtre)
        key: Clé unique pour le composant
        format_func: Fonction pour formater les valeurs affichées

    Returns:
        Filtre sélectionné
    """
    # Générer les options à partir du DataFrame
    unique_values = df[column].dropna().unique().tolist()
    options = [default] + sorted(unique_values)

    # Sélecteur pour le filtre
    selected = st.selectbox(
        label,
        options=options,
        format_func=format_func if format_func else lambda x: x,
        key=key
    )

    return selected


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
        progress_text.text(f"{message} ({i + 1}/{total})")

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
