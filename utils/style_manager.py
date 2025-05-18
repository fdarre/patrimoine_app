"""
Gestionnaire de styles centralisé et amélioré pour l'application
"""
import streamlit as st
import os
from typing import Optional


# Constantes pour les chemins des fichiers
STATIC_DIR = "static"
STYLES_DIR = os.path.join(STATIC_DIR, "styles")
CSS_CACHE = {}


class StyleManager:
    """
    Gestionnaire centralisé pour les styles de l'application

    Cette classe gère le chargement, la combinaison et l'application des styles CSS,
    permettant une approche modulaire et cohérente.
    """

    def __init__(self, mode: str = "dark"):
        """
        Initialise le gestionnaire de styles

        Args:
            mode: Mode d'affichage (dark, light)
        """
        self.mode = mode
        self.initialized = False
        self.base_styles = []
        self.component_styles = []
        self.custom_styles = []

    def initialize_styles(self) -> None:
        """
        Initialise tous les styles de l'application

        Cette méthode charge les styles de base, les styles des composants
        et applique le mode d'affichage.
        """
        if self.initialized:
            return

        # Charger les styles de base
        base_css = self._load_base_styles()

        # Charger les styles des composants
        component_css = self._load_component_styles()

        # Charger le thème
        theme_css = self._load_theme()

        # Combiner tous les styles
        all_css = base_css + component_css + theme_css + "\n".join(self.custom_styles)

        # Appliquer les styles
        self._apply_css(all_css)

        # Marquer comme initialisé
        self.initialized = True

    def add_custom_style(self, css: str) -> None:
        """
        Ajoute un style CSS personnalisé

        Args:
            css: Code CSS à ajouter
        """
        # Ajouter le style à la liste
        self.custom_styles.append(css)

        # Si déjà initialisé, appliquer le nouveau style
        if self.initialized:
            self._apply_css(css)

    def set_mode(self, mode: str) -> None:
        """
        Change le mode d'affichage

        Args:
            mode: Nouveau mode (dark, light)
        """
        if mode not in ["dark", "light"]:
            raise ValueError(f"Mode inconnu: {mode}")

        # Changer le mode uniquement s'il est différent
        if mode != self.mode:
            self.mode = mode

            # Réinitialiser les styles
            self.initialized = False
            self.initialize_styles()

    def _load_base_styles(self) -> str:
        """
        Charge les styles de base

        Returns:
            CSS combiné des styles de base
        """
        # Fichiers CSS de base à charger, dans l'ordre
        base_files = [
            "variables.css",
            "reset.css",
            "layout.css",
            "typography.css",
            "forms.css"
        ]

        # Charger chaque fichier
        css = []
        for file_name in base_files:
            file_path = os.path.join(STYLES_DIR, "base", file_name)
            file_css = self._load_css_file(file_path)
            if file_css:
                css.append(file_css)

        return "\n".join(css)

    def _load_component_styles(self) -> str:
        """
        Charge les styles des composants

        Returns:
            CSS combiné des styles des composants
        """
        # Dossier des composants
        components_dir = os.path.join(STYLES_DIR, "components")

        # Si le dossier n'existe pas, retourner une chaîne vide
        if not os.path.exists(components_dir):
            return ""

        # Liste de tous les fichiers CSS dans le dossier
        css_files = [f for f in os.listdir(components_dir) if f.endswith(".css")]

        # Charger chaque fichier
        css = []
        for file_name in css_files:
            file_path = os.path.join(components_dir, file_name)
            file_css = self._load_css_file(file_path)
            if file_css:
                css.append(file_css)

        return "\n".join(css)

    def _load_theme(self) -> str:
        """
        Charge le thème selon le mode d'affichage

        Returns:
            CSS du thème
        """
        # Fichier du thème
        theme_file = f"{self.mode}-theme.css"
        theme_path = os.path.join(STYLES_DIR, "themes", theme_file)

        # Charger le thème
        return self._load_css_file(theme_path) or ""

    def _load_css_file(self, file_path: str) -> Optional[str]:
        """
        Charge un fichier CSS depuis un chemin spécifié, avec cache

        Args:
            file_path: Chemin complet du fichier CSS

        Returns:
            Contenu du fichier CSS ou None si le fichier n'existe pas
        """
        # Utiliser le cache si disponible
        if file_path in CSS_CACHE:
            return CSS_CACHE[file_path]

        try:
            if not os.path.exists(file_path):
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # Mettre en cache
                CSS_CACHE[file_path] = content

                return content
        except Exception as e:
            st.warning(f"Erreur lors du chargement du CSS: {str(e)}")
            return None

    def _apply_css(self, css: str) -> None:
        """
        Applique un contenu CSS à l'application Streamlit

        Args:
            css: Contenu CSS à appliquer
        """
        if css:
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    def get_color(self, color_name: str) -> str:
        """
        Récupère une couleur du thème actuel

        Args:
            color_name: Nom de la couleur ou raccourci

        Returns:
            Code CSS de la couleur
        """
        # Mappings des raccourcis de couleurs
        color_mappings = {
            "primary": "var(--primary-color)",
            "secondary": "var(--secondary-color)",
            "success": "var(--success-color)",
            "warning": "var(--warning-color)",
            "danger": "var(--danger-color)",
            "info": "var(--info-color)",
            "text": "var(--text-color)",
            "bg": "var(--bg-color)",
            "card": "var(--card-bg)"
        }

        # Si le nom est un raccourci, retourner la valeur mappée
        if color_name in color_mappings:
            return color_mappings[color_name]

        # Sinon tenter d'interpréter comme une variable CSS
        if color_name.startswith("--"):
            return f"var({color_name})"
        else:
            return f"var(--{color_name})"


# Créer une instance singleton du gestionnaire
style_manager = StyleManager()


# Exemple de CSS de base pour les allocations
ALLOCATION_CSS = """
.allocation-container {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
}

.allocation-label {
    width: 80px;
}

.allocation-bar-bg {
    background: #f8f9fa;
    height: 8px;
    width: 70%;
    margin: 0 10px;
}

.allocation-bar {
    height: 8px;
}

.allocation-bar.allocation-actions {
    background: #4e79a7;
}

.allocation-bar.allocation-obligations {
    background: #f28e2c;
}

.allocation-bar.allocation-immobilier {
    background: #e15759;
}

.allocation-bar.allocation-cash {
    background: #edc949;
}

.allocation-bar.allocation-crypto {
    background: #76b7b2;
}

.allocation-bar.allocation-metaux {
    background: #59a14f;
}

.allocation-bar.allocation-autre {
    background: #af7aa1;
}

.allocation-total {
    margin-top: 20px;
}

.allocation-total-label {
    margin-bottom: 5px;
}

.allocation-total-bar-bg {
    background: #f8f9fa;
    height: 10px;
    width: 100%;
    border-radius: 5px;
}

.allocation-total-bar {
    height: 10px;
    border-radius: 5px;
}

.allocation-total-bar.allocation-total-valid {
    background: #28a745;
}

.allocation-total-bar.allocation-total-warning {
    background: #ffc107;
}

.allocation-total-bar.allocation-total-error {
    background: #dc3545;
}

.allocation-pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    margin-right: 4px;
    color: white;
}

.allocation-pill.actions {
    background: #4e79a7;
}

.allocation-pill.obligations {
    background: #f28e2c;
}

.allocation-pill.immobilier {
    background: #e15759;
}

.allocation-pill.cash {
    background: #edc949;
}

.allocation-pill.crypto {
    background: #76b7b2;
}

.allocation-pill.metaux {
    background: #59a14f;
}

.allocation-pill.autre {
    background: #af7aa1;
}
"""


def initialize_styles():
    """
    Fonction d'initialisation pour l'application principale

    Cette fonction doit être appelée au début de l'application
    pour configurer tous les styles.
    """
    # Initialiser avec le mode par défaut
    style_manager.add_custom_style(ALLOCATION_CSS)
    style_manager.initialize_styles()