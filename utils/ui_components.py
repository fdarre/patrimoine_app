"""
Système de composants UI modulaires pour l'application Streamlit
"""
from typing import Dict, List, Optional, Union, Any, Callable
import streamlit as st
import pandas as pd
from dataclasses import dataclass
import re
import uuid

class UIComponent:
    """
    Classe de base pour tous les composants UI
    """

    def render(self) -> None:
        """
        Méthode abstraite pour rendre le composant
        """
        raise NotImplementedError("Les sous-classes doivent implémenter cette méthode")


class Card(UIComponent):
    """
    Composant pour afficher une carte stylisée
    """

    def __init__(
        self,
        title: str,
        content: str = "",
        footer: Optional[str] = None,
        card_class: str = "",
        title_class: str = "",
        content_class: str = "",
        footer_class: str = ""
    ):
        """
        Initialise une carte

        Args:
            title: Titre de la carte
            content: Contenu HTML de la carte
            footer: Pied de page optionnel
            card_class: Classe CSS supplémentaire pour la carte
            title_class: Classe CSS supplémentaire pour le titre
            content_class: Classe CSS supplémentaire pour le contenu
            footer_class: Classe CSS supplémentaire pour le pied de page
        """
        self.title = title
        self.content = content
        self.footer = footer
        self.card_class = card_class
        self.title_class = title_class
        self.content_class = content_class
        self.footer_class = footer_class

    def render(self) -> None:
        """
        Affiche la carte
        """
        footer_html = f'<div class="card-footer {self.footer_class}">{self.footer}</div>' if self.footer else ""

        st.markdown(f"""
        <div class="card {self.card_class}">
            <div class="card-title {self.title_class}">{self.title}</div>
            <div class="card-body {self.content_class}">{self.content}</div>
            {footer_html}
        </div>
        """, unsafe_allow_html=True)


class TodoCard(UIComponent):
    """
    Composant pour afficher une carte de tâche
    """

    def __init__(
        self,
        title: str,
        content: str,
        footer: Optional[str] = None,
        on_complete: Optional[Callable] = None
    ):
        """
        Initialise une carte de tâche

        Args:
            title: Titre de la tâche
            content: Description de la tâche
            footer: Informations supplémentaires optionnelles
            on_complete: Fonction à appeler lorsque la tâche est marquée comme terminée
        """
        self.title = title
        self.content = content
        self.footer = footer
        self.on_complete = on_complete
        self.card_id = str(uuid.uuid4())[:8]

    def render(self) -> None:
        """
        Affiche la carte de tâche
        """
        footer_html = f'<div class="todo-footer">{self.footer}</div>' if self.footer else ""

        st.markdown(f"""
        <div class="todo-card" id="todo-{self.card_id}">
            <div class="todo-header">{self.title}</div>
            <div class="todo-content">{self.content}</div>
            {footer_html}
        </div>
        """, unsafe_allow_html=True)

        if self.on_complete:
            if st.button("Terminé", key=f"done_todo_{self.card_id}"):
                self.on_complete()


class AssetCard(UIComponent):
    """
    Composant pour afficher une carte d'actif
    """

    def __init__(
        self,
        name: str,
        asset_type: str,
        value: float,
        currency: str,
        performance: float,
        account: Optional[str] = "",
        bank: Optional[str] = "",
        on_details: Optional[Callable] = None,
        on_edit: Optional[Callable] = None
    ):
        """
        Initialise une carte d'actif

        Args:
            name: Nom de l'actif
            asset_type: Type d'actif
            value: Valeur actuelle
            currency: Devise
            performance: Performance en pourcentage
            account: Nom du compte (optionnel)
            bank: Nom de la banque (optionnel)
            on_details: Fonction à appeler pour afficher les détails
            on_edit: Fonction à appeler pour éditer l'actif
        """
        self.name = name
        self.asset_type = asset_type
        self.value = value
        self.currency = currency
        self.performance = performance
        self.account = account
        self.bank = bank
        self.on_details = on_details
        self.on_edit = on_edit
        self.card_id = str(uuid.uuid4())[:8]

    def render(self) -> None:
        """
        Affiche la carte d'actif
        """
        perf_class = "positive" if self.performance >= 0 else "negative"
        perf_sign = "+" if self.performance >= 0 else ""

        account_info = ""
        if self.account or self.bank:
            account_info = f"{self.account}" if self.account else ""
            if self.bank:
                account_info += f" ({self.bank})" if self.account else f"{self.bank}"

        st.markdown(f"""
        <div class="asset-card" id="asset-{self.card_id}">
            <div class="asset-header">
                <div class="asset-title">{self.name}</div>
                <div class="asset-badge">{self.asset_type}</div>
            </div>
            <div class="asset-stats">
                <div class="asset-value">{self.value:,.2f} {self.currency}</div>
                <div class="asset-performance {perf_class}">{perf_sign}{self.performance:.2f}%</div>
            </div>
            <div class="asset-footer">{account_info}</div>
        </div>
        """.replace(",", " "), unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Détails", key=f"details_{self.card_id}") and self.on_details:
                self.on_details()

        with col2:
            if st.button("Modifier", key=f"edit_{self.card_id}") and self.on_edit:
                self.on_edit()


class AllocationPills(UIComponent):
    """
    Composant pour afficher des pills d'allocation
    """

    def __init__(self, allocations: Dict[str, float]):
        """
        Initialise des pills d'allocation

        Args:
            allocations: Dictionnaire d'allocations {catégorie: pourcentage}
        """
        self.allocations = allocations

    def render(self) -> None:
        """
        Affiche les pills d'allocation
        """
        html = '<div class="allocation-pills">'

        for category, percentage in sorted(self.allocations.items(), key=lambda x: x[1], reverse=True):
            if percentage > 0:
                html += f'<span class="allocation-pill {category}">{category.capitalize()} {percentage}%</span>'

        html += '</div>'

        st.markdown(html, unsafe_allow_html=True)


class Breadcrumb(UIComponent):
    """
    Composant pour afficher un fil d'ariane
    """

    def __init__(self, items: List[tuple]):
        """
        Initialise un fil d'ariane

        Args:
            items: Liste des éléments du fil d'ariane [(texte, lien), ...]
        """
        self.items = items

    def render(self) -> None:
        """
        Affiche le fil d'ariane
        """
        html = '<div class="breadcrumb">'

        for i, (name, link) in enumerate(self.items):
            if i > 0:
                html += ' &gt; '

            if link and i < len(self.items) - 1:
                html += f'<a href="{link}" class="breadcrumb-link">{name}</a>'
            elif i == len(self.items) - 1:
                html += f'<span class="breadcrumb-current">{name}</span>'
            else:
                html += f'<span class="breadcrumb-item">{name}</span>'

        html += '</div>'

        st.markdown(html, unsafe_allow_html=True)


class InfoBox(UIComponent):
    """
    Composant pour afficher une boîte d'information
    """

    def __init__(
        self,
        message: str,
        box_type: str = "info",
        dismissible: bool = False,
        key: Optional[str] = None
    ):
        """
        Initialise une boîte d'information

        Args:
            message: Message à afficher
            box_type: Type de boîte (info, success, warning, error)
            dismissible: Si la boîte peut être fermée
            key: Clé unique pour le composant
        """
        self.message = message
        self.box_type = box_type
        self.dismissible = dismissible

        if key is None:
            import hashlib
            key = f"infobox_{hashlib.md5(message.encode()).hexdigest()[:8]}"

        self.key = key

    def render(self) -> None:
        """
        Affiche la boîte d'information
        """
        icons = {
            "info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"
        }
        icon = icons.get(self.box_type, "ℹ️")

        info_box_html = f"""
        <div class="infobox {self.box_type}">
            <div style="display:flex;align-items:start;">
                <div style="font-size:18px;margin-right:10px;">{icon}</div>
                <div>{self.message}</div>
            </div>
        </div>
        """

        if self.dismissible:
            if f"{self.key}_closed" not in st.session_state:
                st.session_state[f"{self.key}_closed"] = False

            if not st.session_state[f"{self.key}_closed"]:
                container = st.container()
                container.markdown(info_box_html, unsafe_allow_html=True)

                if container.button("Fermer", key=f"{self.key}_close_btn"):
                    st.session_state[f"{self.key}_closed"] = True
                    st.rerun()
        else:
            st.markdown(info_box_html, unsafe_allow_html=True)


class Metric(UIComponent):
    """
    Composant pour afficher une métrique
    """

    def __init__(
        self,
        label: str,
        value: Any,
        delta: Optional[str] = None,
        delta_class: str = ""
    ):
        """
        Initialise une métrique

        Args:
            label: Libellé de la métrique
            value: Valeur principale
            delta: Variation (optionnel)
            delta_class: Classe CSS pour la variation (positive/negative)
        """
        self.label = label
        self.value = value
        self.delta = delta
        self.delta_class = delta_class

    def render(self) -> None:
        """
        Affiche la métrique
        """
        delta_html = f'<div class="{self.delta_class}">{self.delta}</div>' if self.delta else ""

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{self.label}</div>
            <div class="metric-value">{self.value}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)


class FormStyler(UIComponent):
    """
    Composant pour styliser les formulaires
    """

    def __init__(self, is_valid: bool = True):
        """
        Initialise un styliseur de formulaire

        Args:
            is_valid: Si le formulaire est valide
        """
        self.is_valid = is_valid

    def render(self) -> None:
        """
        Applique le style au formulaire
        """
        btn_style = "background-color:var(--success-color);" if self.is_valid else "background-color:var(--gray-500);"

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