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
    # Construire l'icône
    icon_html = f'<div style="font-size:24px;margin-right:8px;">{icon}</div>' if icon else ''

    # Construire le delta
    delta_html = ""
    if delta:
        delta_class = ""
        if delta_color == "normal":
            delta_class = "positive" if delta.startswith("+") else "negative"
        elif delta_color == "inverse":
            delta_class = "negative" if delta.startswith("+") else "positive"

        delta_html = f'<div class="{get_class(delta_class)}">{delta}</div>'

    # Construire la métrique complète
    metric_html = f"""
    <div class="{get_class('metric')}">
        <div style="display:flex;align-items:center;">
            {icon_html}
            <div>
                <div style="font-size:14px;color:{get_theme_color('text_muted')};">{label}</div>
                <div style="font-size:24px;font-weight:bold;">{value}</div>
                {delta_html}
            </div>
        </div>
    </div>
    """

    st.markdown(metric_html, unsafe_allow_html=True)


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

    def styled_button(label: str, button_type: str = "primary", on_click: Optional[Callable] = None,
                      args: tuple = (), key: Optional[str] = None, disabled: bool = False,
                      icon: str = "", width: str = "auto") -> bool:
        """
        Affiche un bouton stylisé

        Args:
            label: Libellé du bouton
            button_type: Type de bouton ('primary', 'secondary', 'success', 'warning', 'danger')
            on_click: Fonction à appeler lors du clic
            args: Arguments à passer à la fonction
            key: Clé unique pour le bouton
            disabled: Si le bouton est désactivé
            icon: Icône à afficher (emoji)
            width: Largeur du bouton

        Returns:
            True si le bouton a été cliqué, False sinon
        """
        # Générer une clé si nécessaire
        if key is None:
            import hashlib
            key = f"btn_{hashlib.md5(label.encode()).hexdigest()[:8]}"

        # Construire le libellé avec l'icône
        display_label = f"{icon} {label}" if icon else label

        # Appliquer le style selon le type
        from utils.style_loader import create_button_style
        st.markdown(create_button_style(button_type), unsafe_allow_html=True)

        # Créer un style pour la largeur
        if width != "auto":
            st.markdown(f"""
            <style>
            div.stButton button[kind="{key}"] {{
                width: {width};
            }}
            </style>
            """, unsafe_allow_html=True)

        # Créer le bouton
        return st.button(display_label, key=key, on_click=on_click, args=args, disabled=disabled)

    def create_tabs_style(active_color: str = "primary") -> None:
        """
        Applique un style personnalisé aux onglets Streamlit

        Args:
            active_color: Couleur de l'onglet actif
        """
        color = get_theme_color(active_color)

        st.markdown(f"""
        <style>
        .stTabs [data-baseweb="tab-list"] {{
            gap: 1rem;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 3rem;
            white-space: nowrap;
            font-size: 0.9rem;
            color: var(--text-muted);
            border-radius: 0.375rem 0.375rem 0 0;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: rgba(0, 0, 0, 0.05);
            color: {color} !important;
            border-bottom-color: {color} !important;
        }}
        </style>
        """, unsafe_allow_html=True)

    def timeline(items: List[Dict[str, Any]], key: Optional[str] = None) -> None:
        """
        Affiche une timeline d'événements

        Args:
            items: Liste d'événements à afficher avec au moins 'date', 'title' et 'description'
            key: Clé unique pour le composant
        """
        if not items:
            return

        # Générer une clé si nécessaire
        if key is None:
            import hashlib
            key = f"timeline_{hashlib.md5(str(items).encode()).hexdigest()[:8]}"

        # Construire la timeline
        timeline_html = f'<div class="{get_class("timeline")}">'

        for i, item in enumerate(items):
            date = item.get('date', '')
            title = item.get('title', '')
            description = item.get('description', '')
            icon = item.get('icon', '•')
            color = item.get('color', 'primary')

            # Déterminer la couleur
            color_code = get_theme_color(color)

            # Construire l'élément de timeline
            timeline_html += f"""
            <div class="{get_class("timeline-item")}">
                <div class="{get_class("timeline-marker")}" style="background-color:{color_code};">
                    <div class="{get_class("timeline-icon")}">{icon}</div>
                </div>
                <div class="{get_class("timeline-content")}">
                    <div class="{get_class("timeline-date")}">{date}</div>
                    <div class="{get_class("timeline-title")}">{title}</div>
                    <div class="{get_class("timeline-description")}">{description}</div>
                </div>
            </div>
            """

        timeline_html += '</div>'

        # Appliquer le style
        st.markdown(f"""
        <style>
        .{get_class("timeline")} {{
            position: relative;
            margin: 0;
            padding: 0;
            list-style: none;
        }}

        .{get_class("timeline-item")} {{
            position: relative;
            padding-left: 2.5rem;
            margin-bottom: 1.5rem;
        }}

        .{get_class("timeline-marker")} {{
            position: absolute;
            left: 0;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            text-align: center;
            line-height: 20px;
            font-size: 12px;
            color: white;
            z-index: 1;
        }}

        .{get_class("timeline-icon")} {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
        }}

        .{get_class("timeline-content")} {{
            position: relative;
        }}

        .{get_class("timeline-date")} {{
            font-size: 0.85rem;
            color: {get_theme_color('text_muted')};
            margin-bottom: 0.25rem;
        }}

        .{get_class("timeline-title")} {{
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}

        .{get_class("timeline-description")} {{
            color: {get_theme_color('text_light')};
            font-size: 0.95rem;
        }}
        </style>
        """, unsafe_allow_html=True)

        st.markdown(timeline_html, unsafe_allow_html=True)

    def allocation_chart(allocations: Dict[str, float], key: Optional[str] = None) -> None:
        """
        Affiche un graphique d'allocation sous forme de barres horizontales stylisées

        Args:
            allocations: Dictionnaire des allocations {catégorie: pourcentage}
            key: Clé unique pour le composant
        """
        if not allocations:
            return

        # Générer une clé si nécessaire
        if key is None:
            import hashlib
            key = f"alloc_{hashlib.md5(str(allocations).encode()).hexdigest()[:8]}"

        # Définition des couleurs par catégorie
        category_colors = {
            "actions": "#4e79a7",
            "obligations": "#f28e2c",
            "immobilier": "#e15759",
            "crypto": "#76b7b2",
            "metaux": "#59a14f",
            "cash": "#edc949",
            "autre": "#af7aa1"
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

        # Appliquer le style
        st.markdown(f"""
        <style>
        .allocation-chart {{
            margin: 1rem 0;
        }}

        .allocation-item {{
            display: flex;
            align-items: center;
            margin-bottom: 0.75rem;
        }}

        .allocation-label {{
            width: 120px;
            font-size: 0.9rem;
            color: {get_theme_color('text_light')};
        }}

        .allocation-bar-container {{
            flex-grow: 1;
            height: 10px;
            background-color: var(--gray-700);
            border-radius: 5px;
            margin: 0 10px;
            overflow: hidden;
        }}

        .allocation-bar {{
            height: 100%;
            border-radius: 5px;
        }}

        .allocation-value {{
            width: 50px;
            text-align: right;
            font-size: 0.9rem;
            font-weight: 500;
            color: {get_theme_color('text_light')};
        }}
        </style>
        """, unsafe_allow_html=True)

        st.markdown(allocation_html, unsafe_allow_html=True)

    def asset_card(asset, account=None, bank=None, key=None):
        """
        Affiche une carte d'actif stylisée

        Args:
            asset: Objet actif à afficher
            account: Objet compte associé (optionnel)
            bank: Objet banque associée (optionnel)
            key: Clé unique pour le composant
        """
        if key is None:
            import hashlib
            key = f"asset_{asset.id}"

        # Calculer les métriques
        pv = asset.valeur_actuelle - asset.prix_de_revient
        pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
        pv_class = "positive" if pv >= 0 else "negative"
        pv_icon = "📈" if pv >= 0 else "📉"

        # Créer le badge pour le type de produit
        badge_html = create_badge(asset.type_produit.upper(), "primary")

        # Créer le contenu principal
        content = f"""
        <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
            <div>
                <div style="color: {get_theme_color('text_muted')}; font-size: 0.875rem;">Valeur</div>
                <div style="font-size: 1.5rem; font-weight: 700;">{asset.valeur_actuelle:,.2f} {asset.devise}</div>
            </div>
            <div>
                <div style="color: {get_theme_color('text_muted')}; font-size: 0.875rem;">Performance</div>
                <div class="{pv_class}" style="font-size: 1.5rem; font-weight: 700;">
                    {pv_icon} {pv_percent:+.2f}%
                </div>
            </div>
        </div>
        """

        # Créer le pied de page
        footer = ""
        if account:
            footer += f"Compte: {account.libelle}"
            if bank:
                footer += f" ({bank.nom})"

        # Créer la carte complète
        card_html = create_card(
            title=f"{asset.nom} {badge_html}",
            content=content,
            footer=footer,
            extra_classes=f"asset-card-{key}"
        )

        return card_html