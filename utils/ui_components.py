"""
Composants UI réutilisables utilisant le nouveau système de style
"""
import streamlit as st
from typing import Optional, Dict, List, Callable, Union, Any, Tuple

def styled_card(title: str, content: str, footer: Optional[str] = None,
                card_class: str = "", title_class: str = "",
                content_class: str = "", footer_class: str = "") -> None:
    """
    Affiche une carte stylisée

    Args:
        title: Titre de la carte
        content: Contenu HTML de la carte
        footer: Pied de page optionnel
        card_class: Classe CSS supplémentaire pour la carte
        title_class: Classe CSS supplémentaire pour le titre
        content_class: Classe CSS supplémentaire pour le contenu
        footer_class: Classe CSS supplémentaire pour le pied de page
    """
    footer_html = f'<div class="card-footer {footer_class}">{footer}</div>' if footer else ""

    st.markdown(f"""
    <div class="card {card_class}">
        <div class="card-title {title_class}">{title}</div>
        <div class="card-body {content_class}">{content}</div>
        {footer_html}
    </div>
    """, unsafe_allow_html=True)

def styled_todo_card(title: str, content: str, footer: Optional[str] = None) -> None:
    """
    Affiche une carte de tâche stylisée

    Args:
        title: Titre de la tâche
        content: Description de la tâche
        footer: Informations supplémentaires optionnelles
    """
    footer_html = f'<div class="todo-footer">{footer}</div>' if footer else ""

    st.markdown(f"""
    <div class="todo-card">
        <div class="todo-header">{title}</div>
        <div class="todo-content">{content}</div>
        {footer_html}
    </div>
    """, unsafe_allow_html=True)

def styled_sync_card(title: str, description: str, card_class: str = "") -> None:
    """
    Affiche une carte de synchronisation stylisée

    Args:
        title: Titre de la carte
        description: Description de la synchronisation
        card_class: Classe CSS supplémentaire pour la carte
    """
    st.markdown(f"""
    <div class="sync-card {card_class}">
        <h3>{title}</h3>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)

def styled_allocation_bar(category: str, percentage: float) -> None:
    """
    Affiche une barre d'allocation stylisée

    Args:
        category: Catégorie d'allocation
        percentage: Pourcentage alloué
    """
    st.markdown(f"""
    <div class="allocation-container">
        <div class="allocation-label">{category}</div>
        <div class="allocation-bar-bg">
            <div class="allocation-bar allocation-{category}" style="width:{percentage}%;"></div>
        </div>
        <div>{percentage}%</div>
    </div>
    """, unsafe_allow_html=True)

def styled_allocation_total(total: float) -> None:
    """
    Affiche une barre de total d'allocation stylisée

    Args:
        total: Pourcentage total d'allocation
    """
    progress_class = "allocation-total-valid"
    if total < 100:
        progress_class = "allocation-total-warning"
    elif total > 100:
        progress_class = "allocation-total-error"

    st.markdown(f"""
    <div class="allocation-total">
        <h4 class="allocation-total-label">Total: {total}%</h4>
        <div class="allocation-total-bar-bg">
            <div class="allocation-total-bar {progress_class}" style="width:{min(total, 100)}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def styled_metric(label: str, value: Any, delta: Optional[str] = None, delta_class: str = "") -> None:
    """
    Affiche une métrique stylisée

    Args:
        label: Libellé de la métrique
        value: Valeur principale
        delta: Variation (optionnel)
        delta_class: Classe CSS pour la variation (positive/negative)
    """
    delta_html = f'<div class="{delta_class}">{delta}</div>' if delta else ""

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def styled_badge(text: str, badge_type: str = "primary") -> str:
    """
    Génère un badge stylisé

    Args:
        text: Texte du badge
        badge_type: Type de badge (primary, secondary, success, warning, danger, info)

    Returns:
        HTML du badge
    """
    return f'<span class="badge badge-{badge_type}">{text}</span>'

def styled_info_box(message: str, box_type: str = "info", dismissible: bool = False, key: Optional[str] = None) -> None:
    """
    Affiche une boîte d'information stylisée

    Args:
        message: Message à afficher
        box_type: Type de boîte (info, success, warning, error)
        dismissible: Si la boîte peut être fermée
        key: Clé unique pour le composant
    """
    if key is None:
        import hashlib
        key = f"infobox_{hashlib.md5(message.encode()).hexdigest()[:8]}"

    icons = {
        "info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"
    }
    icon = icons.get(box_type, "ℹ️")

    info_box_html = f"""
    <div class="infobox {box_type}">
        <div style="display:flex;align-items:start;">
            <div style="font-size:18px;margin-right:10px;">{icon}</div>
            <div>{message}</div>
        </div>
    </div>
    """

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

def show_message(message: str, type: str = "info", auto_dismiss: bool = False, key: Optional[str] = None) -> None:
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
        import hashlib
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

def create_breadcrumb(items: List[Tuple[str, Optional[str]]]) -> None:
    """
    Crée un fil d'ariane (breadcrumb)

    Args:
        items: Liste des éléments du fil d'ariane [(texte, lien), ...]
    """
    html = '<div class="breadcrumb">'

    for i, (name, link) in enumerate(items):
        if i > 0:
            html += ' &gt; '

        if link and i < len(items) - 1:
            html += f'<a href="{link}" class="breadcrumb-link">{name}</a>'
        elif i == len(items) - 1:
            html += f'<span class="breadcrumb-current">{name}</span>'
        else:
            html += f'<span class="breadcrumb-item">{name}</span>'

    html += '</div>'

    st.markdown(html, unsafe_allow_html=True)

def apply_button_styling(is_valid: bool) -> None:
    """
    Applique le style CSS aux boutons selon leur état de validité

    Args:
        is_valid: Si le formulaire est valide ou non
    """
    btn_style = "background-color:var(--success-color);" if is_valid else "background-color:var(--gray-500);"

    st.markdown(f"""
    <style>
    div.stButton > button {{
        width: 100%;
        height: 3em;
        {btn_style}
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

def create_allocation_pills(allocations: Dict[str, float]) -> str:
    """
    Crée des pills d'allocation pour chaque catégorie

    Args:
        allocations: Dictionnaire d'allocations {catégorie: pourcentage}

    Returns:
        HTML des pills d'allocation
    """
    html = '<div class="allocation-pills">'

    for category, percentage in sorted(allocations.items(), key=lambda x: x[1], reverse=True):
        if percentage > 0:
            html += f'<span class="allocation-pill {category}">{category.capitalize()} {percentage}%</span>'

    html += '</div>'

    return html

def create_asset_card(name: str, asset_type: str, value: float, currency: str,
                     performance: float, account: str = "", bank: str = "") -> None:
    """
    Crée une carte d'actif stylisée

    Args:
        name: Nom de l'actif
        asset_type: Type d'actif
        value: Valeur actuelle
        currency: Devise
        performance: Performance en pourcentage
        account: Nom du compte (optionnel)
        bank: Nom de la banque (optionnel)
    """
    perf_class = "positive" if performance >= 0 else "negative"
    perf_sign = "+" if performance >= 0 else ""

    account_info = ""
    if account or bank:
        account_info = f"{account}" if account else ""
        if bank:
            account_info += f" ({bank})" if account else f"{bank}"

    st.markdown(f"""
    <div class="asset-card">
        <div class="asset-header">
            <div class="asset-title">{name}</div>
            <div class="asset-badge">{asset_type}</div>
        </div>
        <div class="asset-stats">
            <div class="asset-value">{value:,.2f} {currency}</div>
            <div class="asset-performance {perf_class}">{perf_sign}{performance:.2f}%</div>
        </div>
        <div class="asset-footer">{account_info}</div>
    </div>
    """.replace(",", " "), unsafe_allow_html=True)

def paginate_items(items: List[Any], page_size: int = 10, page_key: str = "pagination") -> Tuple[List[Any], int, int]:
    """
    Pagine une liste d'éléments

    Args:
        items: Liste d'éléments à paginer
        page_size: Nombre d'éléments par page
        page_key: Clé pour la pagination dans st.session_state

    Returns:
        Tuple (liste paginée, nombre de pages, page courante)
    """
    # Calculer le nombre total de pages
    total_items = len(items)
    total_pages = max(1, (total_items + page_size - 1) // page_size)

    # Initialiser l'index de page dans session_state si nécessaire
    if page_key not in st.session_state:
        st.session_state[page_key] = 0

    # Calculer les indices de début et fin
    current_page = st.session_state[page_key]
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, total_items)

    # Retourner la page courante
    return items[start_idx:end_idx], total_pages, current_page + 1

def render_pagination_controls(n_pages: int, current_page: int, page_key: str = "pagination") -> None:
    """
    Affiche les contrôles de pagination

    Args:
        n_pages: Nombre total de pages
        current_page: Page courante (1-indexed)
        page_key: Clé pour la pagination dans st.session_state
    """
    if n_pages <= 1:
        return

    cols = st.columns([1, 3, 1])

    with cols[0]:
        if st.button("⏮️ Précédent", key=f"{page_key}_prev", disabled=current_page <= 1):
            st.session_state[page_key] = max(0, st.session_state[page_key] - 1)
            st.rerun()

    with cols[1]:
        st.write(f"Page {current_page} sur {n_pages}")

    with cols[2]:
        if st.button("Suivant ⏭️", key=f"{page_key}_next", disabled=current_page >= n_pages):
            st.session_state[page_key] = min(n_pages - 1, st.session_state[page_key] + 1)
            st.rerun()