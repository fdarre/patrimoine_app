python  # ui/components/__init__.py
"""
Composants UI réutilisables pour l'application
"""


def apply_button_styling(is_valid: bool):
    """
    Applique le style CSS aux boutons selon leur état de validité

    Args:
        is_valid: Si le formulaire est valide ou non
    """
    import streamlit as st
    btn_style = "background-color:#28a745;color:white;" if is_valid else "background-color:#6c757d;color:white;"

    st.markdown(f"""
    <style>
    div.stButton > button {{
        width: 100%;
        height: 3em;
        {btn_style}
    }}
    </style>
    """, unsafe_allow_html=True)


def create_allocation_pills(allocations):
    """
    Crée des pills d'allocation pour les catégories

    Args:
        allocations: Dictionnaire d'allocations

    Returns:
        HTML des pills d'allocation
    """
    html = ""
    if allocations:
        for cat, pct in sorted(allocations.items(), key=lambda x: x[1], reverse=True)[:3]:
            html += f'<span class="allocation-pill {cat}">{cat[:3].capitalize()} {pct}%</span>'
    return html


def styled_todo_card(title, content, footer=None):
    """
    Affiche une carte de tâche stylisée

    Args:
        title: Titre de la tâche
        content: Contenu de la tâche
        footer: Texte de pied de page (optionnel)
    """
    import streamlit as st

    footer_html = f'<div class="todo-footer">{footer}</div>' if footer else ""

    st.markdown(f"""
    <div class="todo-card">
        <div class="todo-header">{title}</div>
        <div class="todo-content">{content}</div>
        {footer_html}
    </div>
    """, unsafe_allow_html=True)


def create_asset_card(name, asset_type, value, currency, performance, account="", bank=""):
    """
    Affiche une carte d'actif stylisée

    Args:
        name: Nom de l'actif
        asset_type: Type d'actif
        value: Valeur actuelle
        currency: Devise
        performance: Performance en pourcentage
        account: Nom du compte (optionnel)
        bank: Nom de la banque (optionnel)
    """
    import streamlit as st

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