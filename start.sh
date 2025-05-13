#!/bin/bash
# Démarrage de l'application Gestion Patrimoniale

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Python 3 n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# Vérifier si les dépendances sont installées
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "Installation des dépendances..."
    pip install -r requirements.txt
fi

# Vérifier si la configuration initiale a été effectuée
if [ ! -f "data/patrimoine.db" ]; then
    echo "Configuration initiale de l'application..."
    python3 setup.py
fi

# Démarrer l'application
echo "Démarrage de l'application..."
streamlit run main.py