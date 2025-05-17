"""
Utilitaires pour l'interface utilisateur
"""
import streamlit as st
from typing import Optional

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
        import hashlib
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
        import time
        import threading

        def dismiss():
            time.sleep(3)
            placeholder.empty()

        threading.Thread(target=dismiss, daemon=True).start()

    return placeholder