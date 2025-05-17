"""
Composants visuels réutilisables pour l'interface utilisateur - Version Streamlit Only
"""
import streamlit as st
from typing import List, Dict, Any, Optional, Union, Tuple, Callable
import pandas as pd


def metric_card(title: str, value: Union[str, float, int],
             delta: Optional[Union[str, float, int]] = None,
             delta_color: str = "normal",
             help_text: str = "",
             icon: str = ""):
    """
    Affiche une carte de métrique améliorée avec Streamlit natif

    Args:
        title: Titre de la métrique
        value: Valeur principale
        delta: Variation (optionnel)
        delta_color: Couleur de la variation ('normal', 'inverse', 'off')
        help_text: Texte d'aide en infobulle (optionnel)
        icon: Icône à afficher (emoji)
    """
    # Formatter la valeur si numérique
    if isinstance(value, (int, float)):
        formatted_value = f"{value:,.2f}".replace(",", " ")
    else:
        formatted_value = value

    # Formater le delta si présent
    if delta is not None:
        if delta_color == "inverse":
            delta_color = "inverse" if delta > 0 else "normal"
        elif delta_color == "off":
            delta_color = "off"

    # Ajouter l'icône si présente
    if icon:
        title = f"{icon} {title}"

    # Utiliser le composant metric natif de Streamlit
    with st.container():
        st.metric(title, formatted_value, delta, delta_color=delta_color, help=help_text)

        # Ajouter une classe CSS pour le styling
        st.markdown("""
        <style>
        [data-testid="stMetricValue"] {
            font-size: 24px !important;
            font-weight: 600 !important;
        }
        </style>
        """, unsafe_allow_html=True)


def info_card(title: str, content: str, icon: str = "ℹ️",
           card_type: str = "info", dismissible: bool = False,
           key: Optional[str] = None):
    """
    Affiche une carte d'information avec Streamlit natif

    Args:
        title: Titre de la carte
        content: Contenu HTML ou texte
        icon: Icône à afficher
        card_type: Type de carte ('info', 'success', 'warning', 'error')
        dismissible: Si la carte peut être fermée
        key: Clé unique pour l'état de la carte
    """
    # Générer une clé si nécessaire
    if not key:
        import hashlib
        key = f"card_{hashlib.md5((title + content).encode()).hexdigest()}"

    # Vérifier si la carte est fermée (si dismissible)
    if dismissible:
        if key not in st.session_state:
            st.session_state[key] = True

        if not st.session_state[key]:
            return

    # Créer un container pour la carte
    with st.container():
        # Appliquer le style selon le type
        if card_type == "success":
            st.success(f"**{title}**\n\n{content}")
        elif card_type == "warning":
            st.warning(f"**{title}**\n\n{content}")
        elif card_type == "error":
            st.error(f"**{title}**\n\n{content}")
        else:
            st.info(f"**{title}**\n\n{content}")

        # Ajouter un bouton pour fermer si dismissible
        if dismissible:
            if st.button("Fermer", key=f"close_{key}"):
                st.session_state[key] = False
                st.rerun()


def action_button(label: str, icon: str = "",
               button_type: str = "primary",
               on_click: Optional[Callable] = None,
               args: Tuple = (),
               disabled: bool = False,
               help_text: str = "",
               key: Optional[str] = None,
               use_container_width: bool = False):
    """
    Crée un bouton d'action stylisé avec Streamlit natif

    Args:
        label: Texte du bouton
        icon: Icône (emoji ou code HTML)
        button_type: Type du bouton ('primary', 'success', 'warning', 'danger', 'outline')
        on_click: Fonction à appeler lors du clic
        args: Arguments à passer à la fonction on_click
        disabled: Si le bouton est désactivé
        help_text: Texte d'aide en infobulle
        key: Clé unique pour le bouton
        use_container_width: Utiliser toute la largeur du conteneur
    """
    # Générer une clé si nécessaire
    if not key:
        import hashlib
        key = f"btn_{hashlib.md5(label.encode()).hexdigest()}"

    # Préparer le label avec l'icône
    button_label = f"{icon} {label}" if icon else label

    # Appliquer une classe CSS de couleur selon le type
    button_classes = {
        "primary": "--primary-color",
        "success": "--success-color",
        "warning": "--warning-color",
        "danger": "--danger-color",
        "outline": "--light-bg"
    }
    button_class = button_classes.get(button_type, "--primary-color")

    # Injecter le CSS pour ce bouton spécifique
    st.markdown(f"""
    <style>
    [data-testid="baseButton-secondary"]:has(div:contains('{button_label}')) {{
        background-color: var({button_class});
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Créer le bouton Streamlit standard
    return st.button(
        button_label,
        key=key,
        disabled=disabled,
        help=help_text,
        on_click=on_click,
        args=args,
        use_container_width=use_container_width
    )


def card_container(content_func: Callable,
                title: str = "",
                footer: str = "",
                collapsible: bool = False,
                collapsed: bool = False,
                key: Optional[str] = None):
    """
    Crée un conteneur de type carte pour encapsuler du contenu

    Args:
        content_func: Fonction qui génère le contenu
        title: Titre de la carte
        footer: Pied de page de la carte
        collapsible: Si la carte peut être réduite/agrandie
        collapsed: État initial si collapsible
        key: Clé unique pour la carte
    """
    # Générer une clé si nécessaire
    if not key:
        import hashlib
        key = f"card_{hashlib.md5(title.encode()).hexdigest()}"

    # Créer une "carte" avec un container et expander Streamlit
    with st.container():
        # Appliquer un style visuel de carte
        st.markdown("""
        <style>
        [data-testid="stVerticalBlock"] > div:has(div.card-container) {
            background-color: var(--light-bg);
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="card-container"></div>', unsafe_allow_html=True)

        # Gérer l'affichage selon si c'est collapsible ou non
        if collapsible:
            # Comportement pour carte pliable
            if title:
                with st.expander(title, expanded=not collapsed):
                    content_func()

                    if footer:
                        st.markdown(f"""
                        <div style="border-top: 1px solid #ddd; padding-top: 10px; font-size: 12px; color: #adb5bd;">
                            {footer}
                        </div>
                        """, unsafe_allow_html=True)
        else:
            # Comportement pour carte simple
            if title:
                st.markdown(f"### {title}")

            content_func()

            if footer:
                st.markdown(f"""
                <div style="border-top: 1px solid #ddd; padding-top: 10px; font-size: 12px; color: #adb5bd;">
                    {footer}
                </div>
                """, unsafe_allow_html=True)


def data_table(data: Union[List[Dict], Dict[str, List], List[List], pd.DataFrame],
            columns: Optional[List[str]] = None,
            key: Optional[str] = None,
            pagination: bool = False,
            page_size: int = 10,
            searchable: bool = False,
            sortable: bool = False,
            with_index: bool = False):
    """
    Affiche un tableau de données amélioré avec Streamlit

    Args:
        data: Données à afficher (liste de dict, dict de listes, liste de listes, ou DataFrame)
        columns: Noms des colonnes (optionnel)
        key: Clé unique pour le tableau
        pagination: Activer la pagination
        page_size: Nombre d'éléments par page
        searchable: Activer la recherche
        sortable: Activer le tri
        with_index: Afficher l'index
    """
    # Générer une clé si nécessaire
    if not key:
        import hashlib
        key = f"table_{hash(str(data))}"

    # Convertir les données en DataFrame si ce n'est pas déjà le cas
    if not isinstance(data, pd.DataFrame):
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # Liste de dictionnaires
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Dictionnaire de listes
            df = pd.DataFrame(data)
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            # Liste de listes
            df = pd.DataFrame(data, columns=columns)
        else:
            # Cas par défaut
            df = pd.DataFrame(data)
    else:
        df = data.copy()

    # Ajouter une barre de recherche si demandé
    if searchable:
        search_term = st.text_input("🔍 Rechercher", key=f"{key}_search")
        if search_term:
            # Recherche dans toutes les colonnes
            mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            df = df[mask]

    # Ajouter des options de tri si demandé
    if sortable and not df.empty:
        sort_cols = st.columns([3, 2, 1])
        with sort_cols[0]:
            sort_column = st.selectbox(
                "Trier par",
                options=df.columns.tolist(),
                key=f"{key}_sort_col"
            )
        with sort_cols[1]:
            sort_order = st.radio(
                "Ordre",
                options=["Ascendant", "Descendant"],
                horizontal=True,
                key=f"{key}_sort_order"
            )

        # Appliquer le tri
        ascending = sort_order == "Ascendant"
        df = df.sort_values(by=sort_column, ascending=ascending)

    # Appliquer la pagination si demandé
    if pagination:
        # Initialiser la page courante dans session_state si nécessaire
        if f"{key}_page" not in st.session_state:
            st.session_state[f"{key}_page"] = 1

        # Calculer le nombre total de pages
        total_pages = (len(df) + page_size - 1) // page_size if len(df) > 0 else 1
        current_page = st.session_state[f"{key}_page"]

        # S'assurer que la page courante est valide
        if current_page > total_pages:
            current_page = total_pages
            st.session_state[f"{key}_page"] = current_page

        # Calculer les indices de début et de fin
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, len(df))

        # Extraire la page courante
        df_display = df.iloc[start_idx:end_idx].copy() if not df.empty else df.copy()

        # Afficher le nombre total d'éléments et la pagination actuelle
        st.write(f"Affichage de {start_idx + 1}-{end_idx} sur {len(df)} éléments")

        # Afficher le tableau
        st.dataframe(df_display, hide_index=not with_index, use_container_width=True)

        # Contrôles de pagination simples avec Streamlit
        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            if st.button("◀ Précédent", disabled=current_page <= 1, key=f"{key}_prev"):
                st.session_state[f"{key}_page"] = current_page - 1
                st.rerun()

        with col2:
            st.write(f"Page {current_page} / {total_pages}")

        with col3:
            if st.button("Suivant ▶", disabled=current_page >= total_pages, key=f"{key}_next"):
                st.session_state[f"{key}_page"] = current_page + 1
                st.rerun()
    else:
        # Afficher le tableau sans pagination
        st.dataframe(df, hide_index=not with_index, use_container_width=True)


def notification_area():
    """
    Crée une zone dédiée pour afficher les notifications temporaires
    """
    # Créer un conteneur pour les notifications
    notification_container = st.container()

    # Définir un emplacement pour les notifications dans session_state
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []

    # Retourner le conteneur pour permettre d'ajouter des notifications
    return notification_container


def show_notification(message: str, type: str = "info", duration: int = 3):
    """
    Affiche une notification dans la zone de notification

    Args:
        message: Message à afficher
        type: Type de notification ('info', 'success', 'warning', 'error')
        duration: Durée d'affichage en secondes
    """
    # Ajouter la notification à la liste
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []

    st.session_state.notifications.append({
        'message': message,
        'type': type,
        'duration': duration,
        'time': time.time()
    })

    # Recharger la page pour afficher la notification
    st.rerun()