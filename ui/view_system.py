"""
Module central pour la gestion des vues de l'application
"""
from typing import Dict, List, Optional, Any, Callable, Union
import streamlit as st
from abc import ABC, abstractmethod

from utils.state_manager import state
from utils.error_manager import handle_ui_exceptions


class View(ABC):
    """
    Classe de base abstraite pour toutes les vues

    Cette classe définit l'interface commune pour toutes les vues
    et fournit les méthodes de base pour le rendu.
    """

    def __init__(self, title: str = ""):
        """
        Initialise la vue

        Args:
            title: Titre de la vue
        """
        self.title = title

    @abstractmethod
    def render(self) -> None:
        """
        Méthode abstraite pour rendre la vue
        """
        pass

    def show_title(self) -> None:
        """
        Affiche le titre de la vue
        """
        if self.title:
            st.header(self.title, anchor=False)

    def execute(self) -> None:
        """
        Exécute la vue avec gestion des erreurs
        """
        try:
            self.show_title()
            self.render()
        except Exception as e:
            # Utiliser le gestionnaire d'erreurs
            from utils.error_manager import error_manager
            error_manager.handle_exception(e)


class TabView(View):
    """
    Vue avec onglets
    """

    def __init__(self, title: str = "", tabs: Optional[Dict[str, View]] = None):
        """
        Initialise la vue avec onglets

        Args:
            title: Titre de la vue
            tabs: Dictionnaire des vues par onglet {nom_onglet: vue}
        """
        super().__init__(title)
        self.tabs = tabs or {}

    def add_tab(self, name: str, view: View) -> None:
        """
        Ajoute un onglet à la vue

        Args:
            name: Nom de l'onglet
            view: Vue à afficher dans l'onglet
        """
        self.tabs[name] = view

    def render(self) -> None:
        """
        Affiche la vue avec onglets
        """
        if not self.tabs:
            st.warning("Aucun onglet défini")
            return

        # Créer les onglets Streamlit
        tab_names = list(self.tabs.keys())
        streamlit_tabs = st.tabs(tab_names)

        # Afficher chaque onglet
        for i, (name, view) in enumerate(self.tabs.items()):
            with streamlit_tabs[i]:
                view.execute()


class ListView(View):
    """
    Vue pour afficher une liste d'éléments
    """

    def __init__(
            self,
            title: str = "",
            items: Optional[List[Any]] = None,
            item_view: Optional[Callable[[Any], None]] = None,
            empty_message: str = "Aucun élément à afficher",
            with_pagination: bool = True,
            items_per_page: int = 10,
            with_search: bool = False,
            with_filters: bool = False
    ):
        """
        Initialise la vue de liste

        Args:
            title: Titre de la vue
            items: Liste des éléments à afficher
            item_view: Fonction pour afficher un élément
            empty_message: Message à afficher si la liste est vide
            with_pagination: Si la pagination est activée
            items_per_page: Nombre d'éléments par page
            with_search: Si la recherche est activée
            with_filters: Si les filtres sont activés
        """
        super().__init__(title)
        self.items = items or []
        self.item_view = item_view
        self.empty_message = empty_message
        self.with_pagination = with_pagination
        self.items_per_page = items_per_page
        self.with_search = with_search
        self.with_filters = with_filters
        self.filters = {}
        self.search_term = ""

    def set_items(self, items: List[Any]) -> None:
        """
        Définit la liste des éléments

        Args:
            items: Nouvelle liste d'éléments
        """
        self.items = items

    def set_item_view(self, item_view: Callable[[Any], None]) -> None:
        """
        Définit la fonction d'affichage d'un élément

        Args:
            item_view: Fonction pour afficher un élément
        """
        self.item_view = item_view

    def add_filter(self, name: str, options: List[Any], default: Any = None) -> None:
        """
        Ajoute un filtre à la vue

        Args:
            name: Nom du filtre
            options: Liste des options du filtre
            default: Option par défaut
        """
        self.filters[name] = {
            "options": options,
            "default": default
        }

    def render(self) -> None:
        """
        Affiche la vue de liste
        """
        # Si la liste est vide, afficher le message
        if not self.items:
            st.info(self.empty_message)
            return

        # Si l'affichage d'un élément n'est pas défini, afficher un avertissement
        if not self.item_view:
            st.warning("Fonction d'affichage d'un élément non définie")
            return

        # Filtrer les éléments si nécessaire
        filtered_items = self.items

        # Afficher la recherche si activée
        if self.with_search:
            self.search_term = st.text_input("🔍 Rechercher", key="list_view_search")

            if self.search_term:
                # Implémenter la recherche selon le type d'éléments
                # Cette implémentation dépend du type d'éléments
                pass

        # Afficher les filtres si activés
        if self.with_filters and self.filters:
            # Créer une ligne pour les filtres
            filter_cols = st.columns(len(self.filters))

            # Afficher chaque filtre
            for i, (name, filter_info) in enumerate(self.filters.items()):
                with filter_cols[i]:
                    # Ajouter l'option "Tous" au début
                    options = ["Tous"] + filter_info["options"]

                    # Déterminer l'index par défaut
                    default_index = 0
                    if filter_info["default"] is not None:
                        try:
                            default_index = options.index(filter_info["default"])
                        except ValueError:
                            pass

                    # Afficher le sélecteur
                    st.selectbox(
                        f"Filtrer par {name}",
                        options=options,
                        index=default_index,
                        key=f"list_view_filter_{name}"
                    )

        # Pagination si activée
        if self.with_pagination:
            # Calculer le nombre de pages
            total_pages = (len(filtered_items) + self.items_per_page - 1) // self.items_per_page

            # Récupérer la page courante
            page = state.get_pagination_index("list_view") + 1

            # Calculer les indices de début et de fin
            start_idx = (page - 1) * self.items_per_page
            end_idx = min(start_idx + self.items_per_page, len(filtered_items))

            # Afficher les éléments de la page courante
            for item in filtered_items[start_idx:end_idx]:
                self.item_view(item)

            # Afficher les contrôles de pagination
            if total_pages > 1:
                cols = st.columns([1, 3, 1])

                with cols[0]:
                    if st.button("◀ Précédent", disabled=page <= 1):
                        state.set_pagination_index("list_view", page - 2)
                        st.rerun()

                with cols[1]:
                    st.write(f"Page {page} sur {total_pages}")

                with cols[2]:
                    if st.button("Suivant ▶", disabled=page >= total_pages):
                        state.set_pagination_index("list_view", page)
                        st.rerun()
        else:
            # Afficher tous les éléments
            for item in filtered_items:
                self.item_view(item)


class FormView(View):
    """
    Vue pour afficher un formulaire
    """

    def __init__(
            self,
            title: str = "",
            on_submit: Optional[Callable[[Dict[str, Any]], None]] = None,
            submit_label: str = "Enregistrer",
            cancel_label: str = "Annuler",
            on_cancel: Optional[Callable[[], None]] = None
    ):
        """
        Initialise la vue de formulaire

        Args:
            title: Titre de la vue
            on_submit: Fonction à appeler lors de la soumission du formulaire
            submit_label: Libellé du bouton de soumission
            cancel_label: Libellé du bouton d'annulation
            on_cancel: Fonction à appeler lors de l'annulation
        """
        super().__init__(title)
        self.on_submit = on_submit
        self.submit_label = submit_label
        self.cancel_label = cancel_label
        self.on_cancel = on_cancel
        self.fields: Dict[str, Any] = {}

    def add_field(self, name: str, field: Any) -> None:
        """
        Ajoute un champ au formulaire

        Args:
            name: Nom du champ
            field: Champ à ajouter
        """
        self.fields[name] = field

    def render(self) -> None:
        """
        Affiche le formulaire
        """
        # Créer un formulaire Streamlit
        with st.form(self.title.lower().replace(" ", "_") + "_form"):
            # Afficher les champs
            for name, field in self.fields.items():
                # L'affichage du champ dépend du type de champ
                # Cette implémentation dépend du type de champ
                pass

            # Afficher les boutons
            col1, col2 = st.columns(2)

            with col1:
                submitted = st.form_submit_button(self.submit_label)

            with col2:
                cancelled = st.form_submit_button(self.cancel_label)

            # Gérer la soumission
            if submitted and self.on_submit:
                # Récupérer les valeurs des champs
                values = {name: field.get_value() for name, field in self.fields.items()}

                # Appeler la fonction de soumission
                self.on_submit(values)

            # Gérer l'annulation
            if cancelled and self.on_cancel:
                self.on_cancel()


class ViewController:
    """
    Contrôleur pour gérer les vues

    Cette classe permet de centraliser la gestion des vues
    et de faciliter la navigation entre les vues.
    """

    def __init__(self):
        """Initialise le contrôleur de vues"""
        self.views: Dict[str, View] = {}
        self.current_view = ""

    def register_view(self, name: str, view: View) -> None:
        """
        Enregistre une vue

        Args:
            name: Nom de la vue
            view: Vue à enregistrer
        """
        self.views[name] = view

    def set_current_view(self, name: str) -> None:
        """
        Définit la vue courante

        Args:
            name: Nom de la vue
        """
        if name in self.views:
            self.current_view = name
            state.set("current_view", name)
        else:
            raise ValueError(f"Vue inconnue: {name}")

    def get_current_view(self) -> Optional[View]:
        """
        Récupère la vue courante

        Returns:
            Vue courante ou None si aucune vue n'est définie
        """
        if not self.current_view:
            # Essayer de récupérer la vue depuis l'état
            self.current_view = state.get("current_view", "")

        if self.current_view in self.views:
            return self.views[self.current_view]

        return None

    def show_current_view(self) -> None:
        """
        Affiche la vue courante
        """
        view = self.get_current_view()

        if view:
            view.execute()
        else:
            # Si aucune vue n'est définie, afficher un message
            st.warning("Aucune vue n'est définie")


# Créer une instance singleton du contrôleur
view_controller = ViewController()