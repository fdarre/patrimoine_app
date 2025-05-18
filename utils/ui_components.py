"""
Composants UI réutilisables utilisant le système de style centralisé
"""
import streamlit as st
from typing import Optional, Dict, Any, List, Callable, Tuple, Union
from utils.theme_manager import get_theme_color

def styled_metric(label: str, value: str, delta: Optional[str] = None,
                  delta_color: str = "normal", icon: str = "") -> None:
    """Affiche une métrique stylisée"""
    icon_html = f'<div style="font-size:24px;margin-right:8px;">{icon}</div>' if icon else ''
    delta_html = ""

    if delta:
        delta_class = ""
        if delta_color == "normal":
            delta_class = "positive" if delta.startswith("+") else "negative"
        elif delta_color == "inverse":
            delta_class = "negative" if delta.startswith("+") else "positive"
        delta_html = f'<div class="{delta_class}">{delta}</div>'

    st.markdown(f"""
    <div class="metric-card">
        <div style="display:flex;align-items:center;">
            {icon_html}
            <div>
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                {delta_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def styled_info_box(message: str, box_type: str = "info", dismissible: bool = False,
                    key: Optional[str] = None) -> None:
    """Affiche une boîte d'information stylisée"""
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

def create_card(title: str, content: str, footer: Optional[str] = None,
                badge_text: Optional[str] = None, badge_type: str = "primary",
                icon: Optional[str] = None, is_hoverable: bool = True,
                border_color: Optional[str] = None) -> str:
    """
    Crée une carte stylisée

    Args:
        title: Titre de la carte
        content: Contenu HTML de la carte
        footer: Pied de page de la carte (optionnel)
        badge_text: Texte du badge (optionnel)
        badge_type: Type du badge ('primary', 'secondary', 'success', 'warning', 'danger')
        icon: Icône à afficher (emoji ou texte)
        is_hoverable: Si la carte doit avoir un effet de survol
        border_color: Couleur de la bordure gauche (optionnel)

    Returns:
        Chaîne HTML de la carte
    """
    # Construction du titre avec icône et badge
    title_with_icon = f'{icon} {title}' if icon else title

    badge_html = ""
    if badge_text:
        badge_html = f'<span class="badge badge-{badge_type}">{badge_text}</span>'

    # Styles spécifiques
    hover_class = "card-hover" if is_hoverable else ""
    border_style = f"border-left: 4px solid {border_color};" if border_color else ""

    footer_html = f'<div class="card-footer">{footer}</div>' if footer else ""

    return f"""
    <div class="card {hover_class}" style="{border_style}">
        <div class="card-header">
            <div class="card-title">{title_with_icon}</div>
            {badge_html}
        </div>
        <div class="card-body">
            {content}
        </div>
        {footer_html}
    </div>
    """

def asset_card(name: str, asset_type: str, value: float, currency: str,
              performance: float, account_name: str = "", bank_name: str = "",
              icon: str = "💰", border_color: Optional[str] = None) -> str:
    """
    Crée une carte spécifique pour les actifs financiers
    """
    # Calcul de la classe de performance
    perf_class = "positive" if performance >= 0 else "negative"
    perf_icon = "📈" if performance >= 0 else "📉"

    # Construction du contenu
    content = f"""
    <div class="asset-stats">
        <div class="asset-stat">
            <div class="stat-label">Valeur</div>
            <div class="stat-value">{value:,.2f} {currency}</div>
        </div>
        <div class="asset-stat">
            <div class="stat-label">Performance</div>
            <div class="stat-value {perf_class}">{perf_icon} {performance:+.2f}%</div>
        </div>
    </div>
    """

    # Construction du footer
    footer = ""
    if account_name or bank_name:
        if account_name and bank_name:
            footer = f"🏦 {account_name} ({bank_name})"
        else:
            footer = f"🏦 {account_name or bank_name}"

    # Utilisation du composant card général
    return create_card(
        title=name,
        content=content,
        footer=footer,
        badge_text=asset_type.upper(),
        badge_type="primary",
        icon=icon,
        is_hoverable=True,
        border_color=border_color
    )

def todo_card(title: str, content: str, footer: Optional[str] = None) -> str:
    """Crée une carte spécifique pour les tâches à faire"""
    return create_card(
        title=title,
        content=content,
        footer=footer,
        icon="✅",
        is_hoverable=True,
        border_color="var(--warning-color)"
    )

def allocation_chart(allocations: Dict[str, float], key: Optional[str] = None) -> None:
    """Affiche un graphique d'allocation sous forme de barres horizontales stylisées"""
    if not allocations:
        return

    # Définition des couleurs par catégorie
    category_colors = {
        "actions": "#4e79a7", "obligations": "#f28e2c", "immobilier": "#e15759",
        "crypto": "#76b7b2", "metaux": "#59a14f", "cash": "#edc949", "autre": "#af7aa1"
    }

    # Trier les allocations par valeur décroissante
    sorted_allocations = sorted(allocations.items(), key=lambda x: x[1], reverse=True)

    # Construire les barres d'allocation
    allocation_html = '<div class="allocation-chart">'

    for category, percentage in sorted_allocations:
        color = category_colors.get(category.lower(), "#bab0ab")

        allocation_html += f"""
        <div class="allocation-item">
            <div class="allocation-label">{category.capitalize()}</div>
            <div class="allocation-bar-container">
                <div class="allocation-bar" style="width:{percentage}%;background-color:{color};"></div>
            </div>
            <div class="allocation-value">{percentage}%</div>
        </div>
        """

    allocation_html += '</div>'
    st.markdown(allocation_html, unsafe_allow_html=True)