"""
Composants UI réutilisables utilisant le système de style centralisé
"""
import streamlit as st
from typing import Optional, Dict, Any, List, Callable
from utils.style_loader import get_class, create_styled_element, create_card, create_badge, get_theme_color


def styled_metric(label: str, value: str, delta: Optional[str] = None,
                  delta_color: str = "normal", icon: str = "") -> None:
    """
    Affiche une métrique stylisée

    Args:
        label: Libellé de la métrique
        value: Valeur principale
        delta: Variation (optionnel)
        delta_color: Couleur du delta ('normal', 'inverse', 'off')
        icon: Icône à afficher (emoji)
    """
    # Utiliser les composants natifs de Streamlit au lieu d'HTML personnalisé
    st.markdown(f"**{label}**")

    metric_cols = st.columns([1, 5])
    with metric_cols[0]:
        if icon:
            st.markdown(f"## {icon}")
    with metric_cols[1]:
        st.markdown(f"### {value}")
        if delta:
            delta_class = ""
            if delta_color == "normal":
                delta_class = "positive" if delta.startswith("+") else "negative"
            elif delta_color == "inverse":
                delta_class = "negative" if delta.startswith("+") else "positive"

            st.markdown(f"<span class='{delta_class}'>{delta}</span>", unsafe_allow_html=True)


def styled_info_box(message: str, box_type: str = "info", dismissible: bool = False,
                    key: Optional[str] = None) -> None:
    """
    Affiche une boîte d'information stylisée

    Args:
        message: Message à afficher
        box_type: Type de boîte ('info', 'success', 'warning', 'error')
        dismissible: Si la boîte peut être fermée
        key: Clé unique pour la boîte
    """
    # Générer une clé si nécessaire
    if key is None:
        import hashlib
        key = f"infobox_{hashlib.md5(message.encode()).hexdigest()[:8]}"

    # Définir l'icône selon le type
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    icon = icons.get(box_type, "ℹ️")

    # Créer la boîte d'information
    info_box_html = f"""
    <div class="{get_class('infobox')} {get_class(box_type)}">
        <div style="display:flex;align-items:start;">
            <div style="font-size:18px;margin-right:10px;">{icon}</div>
            <div>{message}</div>
        </div>
    </div>
    """

    # Si la boîte est fermable, ajouter le bouton de fermeture
    if dismissible:
        if f"{key}_closed" not in st.session_state:
            st.session_state[f"{key}_closed"] = False

        if not st.session_state[f"{key}_closed"]:
            container = st.container()
            container.markdown(info_box_html, unsafe_allow_html=True)

            if container.button("Fermer", key=f"{key}_close_btn"):
                st.session_state[f"{key}_closed"] = True
                st.rerun()
    else:
        st.markdown(info_box_html, unsafe_allow_html=True)


def styled_progress(value: float, max_value: float = 100.0, color: str = "primary",
                    height: str = "10px", label: Optional[str] = None) -> None:
    """
    Affiche une barre de progression stylisée

    Args:
        value: Valeur actuelle
        max_value: Valeur maximale
        color: Couleur de la barre ('primary', 'success', 'warning', 'danger')
        height: Hauteur de la barre
        label: Libellé à afficher (optionnel)
    """
    # Calculer le pourcentage
    percentage = min(100, max(0, (value / max_value) * 100))

    # Obtenir la couleur
    color_code = get_theme_color(color)

    # Construire le label
    label_html = f'<div style="margin-bottom:5px;">{label}</div>' if label else ''

    # Construire la barre de progression
    progress_html = f"""
    {label_html}
    <div style="background:var(--gray-700);border-radius:4px;height:{height};width:100%;">
        <div style="background:{color_code};border-radius:4px;height:{height};width:{percentage}%;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:12px;margin-top:3px;">
        <span>{value}</span>
        <span>{max_value}</span>
    </div>
    """

    st.markdown(progress_html, unsafe_allow_html=True)


def styled_data_table(data: List[Dict[str, Any]], columns: Optional[List[str]] = None,
                      key: Optional[str] = None, use_pagination: bool = True,
                      page_size: int = 10) -> None:
    """
    Affiche un tableau de données stylisé avec pagination

    Args:
        data: Données à afficher
        columns: Colonnes à afficher (utilise toutes les colonnes si None)
        key: Clé unique pour le tableau
        use_pagination: Activer la pagination
        page_size: Nombre d'éléments par page
    """
    # Générer une clé si nécessaire
    if key is None:
        import hashlib
        key = f"table_{hash(str(data))}"

    # Si aucune donnée, afficher un message
    if not data:
        st.info("Aucune donnée à afficher")
        return

    # Déterminer les colonnes
    if columns is None:
        columns = list(data[0].keys())

    # Calculer les pages pour la pagination
    if use_pagination:
        total_pages = (len(data) + page_size - 1) // page_size

        # Initialiser la page courante
        if f"{key}_page" not in st.session_state:
            st.session_state[f"{key}_page"] = 0

        # Limiter les données à la page courante
        start_idx = st.session_state[f"{key}_page"] * page_size
        end_idx = min(start_idx + page_size, len(data))
        page_data = data[start_idx:end_idx]
    else:
        page_data = data
        total_pages = 1

        # Construire l'en-tête du tableau
        header_html = "<tr>"
        for col in columns:
            header_html += f'<th class="{get_class("table_header")}">{col}</th>'
        header_html += "</tr>"

        # Construire les lignes du tableau
        rows_html = ""
        for row in page_data:
            rows_html += f'<tr class="{get_class("table_row")}">'
            for col in columns:
                rows_html += f"<td>{row.get(col, '')}</td>"
            rows_html += "</tr>"

        # Construire le tableau complet
        table_html = f"""
        <div class="{get_class('table')}">
            <table style="width:100%;border-collapse:collapse;">
                <thead>{header_html}</thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """

        st.markdown(table_html, unsafe_allow_html=True)

        # Ajouter les contrôles de pagination
        if use_pagination and total_pages > 1:
            cols = st.columns([1, 3, 1])

            with cols[0]:
                if st.button("◀ Précédent", key=f"{key}_prev", disabled=st.session_state[f"{key}_page"] <= 0):
                    st.session_state[f"{key}_page"] -= 1
                    st.rerun()

            with cols[1]:
                st.write(f"Page {st.session_state[f'{key}_page'] + 1} sur {total_pages}")

            with cols[2]:
                if st.button("Suivant ▶", key=f"{key}_next",
                             disabled=st.session_state[f"{key}_page"] >= total_pages - 1):
                    st.session_state[f"{key}_page"] += 1
                    st.rerun()