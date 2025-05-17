/**
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
