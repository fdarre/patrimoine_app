"""
Structure de dossiers pour l'application

Ce script crée les dossiers nécessaires pour les styles CSS, 
les fichiers JavaScript et autres ressources statiques.
"""
import os
import shutil
import sys


def create_directory_structure():
    """
    Crée la structure de dossiers pour l'application dans le répertoire du projet
    """
    # Définir explicitement le répertoire de base du projet
    # Vous pouvez modifier cette ligne si votre projet est dans un autre emplacement
    base_dir = "/home/fred/patrimoine_app"

    # Vérifier si le répertoire existe
    if not os.path.exists(base_dir):
        print(f"Erreur: Le répertoire {base_dir} n'existe pas.")
        # Essayer de détecter automatiquement le répertoire du projet
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Remonter jusqu'à trouver le dossier principal du projet
        while os.path.basename(current_dir) != "patrimoine_app" and os.path.dirname(current_dir) != current_dir:
            current_dir = os.path.dirname(current_dir)

        if os.path.basename(current_dir) == "patrimoine_app":
            base_dir = current_dir
            print(f"Utilisation du répertoire détecté automatiquement: {base_dir}")
        else:
            # Dernier recours: utiliser le répertoire courant
            base_dir = os.getcwd()
            print(f"Utilisation du répertoire courant: {base_dir}")

    print(f"Création de la structure de dossiers dans: {base_dir}")

    # Définir les chemins des dossiers à créer
    directories = [
        os.path.join(base_dir, "static"),
        os.path.join(base_dir, "static", "styles"),
        os.path.join(base_dir, "static", "js"),
        os.path.join(base_dir, "static", "images"),
        os.path.join(base_dir, "logs")
    ]

    # Créer les dossiers s'ils n'existent pas
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Dossier créé ou déjà existant: {directory}")

    # Créer le fichier .gitkeep dans les dossiers vides pour les conserver dans Git
    for directory in directories:
        gitkeep_file = os.path.join(directory, ".gitkeep")
        if not os.path.exists(gitkeep_file):
            with open(gitkeep_file, "w") as f:
                pass
            print(f"Fichier .gitkeep créé: {gitkeep_file}")

    # Écrire les fichiers CSS et JS aux bons endroits
    css_dest = os.path.join(base_dir, "static", "styles", "main.css")
    js_dest = os.path.join(base_dir, "static", "js", "main.js")

    # Contenu CSS
    css_content = """/* 
 * styles/main.css
 * Styles centralisés pour l'application de gestion patrimoniale
 */

/* Variables globales */
:root {
    --text-color: #fff;
    --dark-text-color: #333;
    --background-color: #1e1e1e;
    --primary-color: #4e79a7;
    --secondary-color: #f28e2c;
    --success-color: #40c057;
    --warning-color: #ffc107;
    --danger-color: #fa5252;
    --light-bg: #343a40;
    --darker-bg: #212529;
    --border-color: #495057;
    --muted-color: #6c757d;
    --light-text: #adb5bd;
}

/* Cartes et conteneurs */
.metric-card {
    background-color: var(--light-bg);
    border-radius: 0.5rem;
    padding: 1rem;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.2);
    margin-bottom: 1rem;
    color: var(--text-color);
    transition: transform 0.2s;
}

.metric-card:hover {
    transform: translateY(-2px);
}

.todo-card {
    background-color: #fff3cd;
    border-left: 4px solid var(--warning-color);
    padding: 1rem;
    margin-bottom: 0.5rem;
    border-radius: 0.25rem;
    color: var(--dark-text-color) !important;
}

.component-card {
    background-color: #31383e;
    border-left: 4px solid var(--primary-color);
    padding: 1rem;
    margin-bottom: 0.5rem;
    border-radius: 0.25rem;
    color: var(--text-color);
}

.sync-card {
    border: 1px solid var(--border-color);
    border-radius: 5px;
    padding: 15px;
    margin-bottom: 15px;
    background-color: var(--light-bg);
    transition: all 0.2s ease;
}

.sync-card:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.sync-card h3 {
    margin-top: 0;
    font-size: 18px;
    color: var(--text-color);
}

.sync-card p {
    color: var(--light-text);
    margin-bottom: 15px;
}

/* Indicateurs et badges */
.positive {
    color: var(--success-color);
}

.negative {
    color: var(--danger-color);
}

.badge {
    background-color: var(--light-bg);
    border-radius: 3px;
    padding: 1px 5px;
    font-size: 12px;
    color: var(--text-color);
    display: inline-block;
}

.badge-primary {
    background-color: var(--primary-color);
}

.badge-secondary {
    background-color: var(--secondary-color);
}

.badge-success {
    background-color: var(--success-color);
}

.badge-danger {
    background-color: var(--danger-color);
}

/* Navigation */
.breadcrumb {
    margin-bottom: 15px;
    font-size: 14px;
    color: var(--muted-color);
}

.breadcrumb a {
    color: var(--light-text);
    text-decoration: none;
}

.breadcrumb a:hover {
    text-decoration: underline;
}

/* Tableaux */
.dataframe {
    border-collapse: collapse;
    width: 100%;
    border: 1px solid var(--border-color);
    font-size: 14px;
    background-color: var(--background-color);
}

.dataframe th {
    background-color: var(--light-bg);
    color: var(--text-color);
    text-align: left;
    padding: 12px 8px;
    border-bottom: 2px solid var(--border-color);
}

.dataframe td {
    border-bottom: 1px solid var(--border-color);
    padding: 10px 8px;
    color: var(--text-color);
}

.dataframe tr:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

/* Pagination */
.pagination {
    display: flex;
    list-style: none;
    padding: 0;
    margin: 1rem 0;
    justify-content: center;
}

.page-item {
    margin: 0 2px;
}

.page-link {
    color: var(--text-color);
    background-color: var(--light-bg);
    border: 1px solid var(--border-color);
    padding: 5px 10px;
    border-radius: 3px;
    text-decoration: none;
    cursor: pointer;
}

.page-item.active .page-link {
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}

.page-item.disabled .page-link {
    color: var(--muted-color);
    pointer-events: none;
}

/* Formulaires et boutons */
.form-control {
    background-color: var(--light-bg);
    border: 1px solid var(--border-color);
    color: var(--text-color);
    padding: 8px 12px;
    border-radius: 4px;
}

.btn {
    display: inline-block;
    font-weight: 400;
    text-align: center;
    white-space: nowrap;
    vertical-align: middle;
    user-select: none;
    border: 1px solid transparent;
    padding: .375rem .75rem;
    font-size: 1rem;
    line-height: 1.5;
    border-radius: .25rem;
    transition: all .15s ease-in-out;
    cursor: pointer;
}

.btn-primary {
    color: #fff;
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}

.btn-success {
    color: #fff;
    background-color: var(--success-color);
    border-color: var(--success-color);
}

.btn-danger {
    color: #fff;
    background-color: var(--danger-color);
    border-color: var(--danger-color);
}

/* Loaders et feedback */
.loader {
    border: 4px solid var(--light-bg);
    border-radius: 50%;
    border-top: 4px solid var(--primary-color);
    width: 30px;
    height: 30px;
    animation: spin 2s linear infinite;
    margin: 20px auto;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.toast {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    border-radius: 4px;
    color: var(--dark-text-color);
    max-width: 300px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 9999;
    animation: fadeIn 0.3s, fadeOut 0.3s 2.7s;
    animation-fill-mode: forwards;
}

.toast-success {
    background-color: var(--success-color);
}

.toast-error {
    background-color: var(--danger-color);
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeOut {
    from { opacity: 1; transform: translateY(0); }
    to { opacity: 0; transform: translateY(-20px); }
}

/* Correctifs spécifiques pour streamlit */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-color) !important;
}

.stButton > button {
    width: 100%;
}

.allocation-box {
    background-color: var(--light-bg);
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
    color: var(--text-color);
}

.allocation-title {
    font-weight: bold;
    margin-bottom: 0.5rem;
    color: var(--text-color);
}

.composite-header {
    background-color: #2c5840;
    padding: 0.5rem;
    border-radius: 0.25rem;
    margin-bottom: 0.5rem;
    color: var(--text-color);
}

/* Pour les sélecteurs et entrées */
.stSelectbox, .stTextInput, .stTextArea {
    color: var(--text-color);
}

/* Exception pour les cartes todo */
.todo-card p, .todo-card div, .todo-card span {
    color: var(--dark-text-color);
}
"""

    # Contenu JavaScript
    js_content = """/**
 * main.js - JavaScript pour l'application de gestion patrimoniale
 * Note: L'intégration avec Streamlit peut être limitée, certaines 
 * fonctionnalités peuvent nécessiter des contournements.
 */

// Fonction pour afficher un toast de notification
function showToast(message, type = 'success') {
    // Créer l'élément toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    // Ajouter au DOM
    document.body.appendChild(toast);

    // Supprimer après 3 secondes
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Améliorer l'expérience des tableaux
function enhanceTables() {
    const tables = document.querySelectorAll('.dataframe');

    tables.forEach(table => {
        // Ajouter la classe pour le style
        table.classList.add('enhanced-table');

        // Ajouter des événements de tri si nécessaire
        const headers = table.querySelectorAll('th');
        headers.forEach(header => {
            header.addEventListener('click', () => {
                // Le tri serait implémenté ici, mais comme Streamlit recharge la page,
                // cette fonctionnalité devra être implémentée côté serveur
            });
        });
    });
}

// Fonction pour animer les cartes métriques
function animateMetricCards() {
    const cards = document.querySelectorAll('.metric-card');

    cards.forEach(card => {
        // Animation d'entrée
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';

        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100);
    });
}

// Exécuter lorsque le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    // Améliorer les tableaux
    enhanceTables();

    // Animer les cartes métriques
    animateMetricCards();

    // Intercepter les clics sur les boutons pour ajouter des feedbacks
    document.querySelectorAll('button').forEach(button => {
        button.addEventListener('click', function() {
            // Ajouter une classe temporaire
            button.classList.add('button-clicked');

            // Supprimer après la fin de l'animation
            setTimeout(() => {
                button.classList.remove('button-clicked');
            }, 300);
        });
    });
});

// Exporter des fonctions utilitaires pour une utilisation dans Streamlit via iframes
window.appUtils = {
    showToast: showToast,
    enhanceTables: enhanceTables
};
"""

    # Écrire les fichiers
    try:
        with open(css_dest, "w") as f:
            f.write(css_content)
        print(f"Fichier CSS créé: {css_dest}")

        with open(js_dest, "w") as f:
            f.write(js_content)
        print(f"Fichier JS créé: {js_dest}")
    except Exception as e:
        print(f"Erreur lors de l'écriture des fichiers: {str(e)}")

    print("Structure de dossiers créée avec succès!")


if __name__ == "__main__":
    create_directory_structure()