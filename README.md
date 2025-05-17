# Application de Gestion Patrimoniale

Une application complète pour centraliser, visualiser et analyser la composition de votre patrimoine financier et immobilier réparti sur plusieurs comptes bancaires, enveloppes fiscales, et supports d'investissement.

## 🧭 Aperçu

Cette application vous permet de suivre avec précision la composition et l'évolution de votre patrimoine. Elle a été conçue pour les investisseurs particuliers souhaitant avoir une vision granulaire de leurs actifs et de leur allocation réelle à travers différents comptes et établissements bancaires.

![Dashboard](https://via.placeholder.com/800x400?text=Dashboard+Screenshot)

## ✨ Fonctionnalités principales

### 👥 Multi-utilisateurs
- Authentification sécurisée avec gestion de sessions JWT
- Protection contre les attaques par force brute
- Données isolées par utilisateur

### 🏦 Gestion des banques et comptes
- Définition des banques avec notes personnalisées
- Création de comptes par typologie (courant, livret, PEA, titres, assurance-vie, etc.)
- Organisation hiérarchique: Banque > Compte > Actifs

### 💼 Gestion des actifs
- Ajout d'actifs par template, code ISIN, ou manuellement
- Répartition par catégorie (actions, obligations, immobilier, etc.)
- Définition de la répartition géographique par catégorie
- Gestion des actifs composites (ex: fonds contenant d'autres actifs)
- Suivi des plus/moins-values

### 🔄 Synchronisation automatique
- Récupération des prix via Yahoo Finance (pour les actifs avec code ISIN)
- Synchronisation des taux de change pour les devises étrangères
- Suivi des prix des métaux précieux
- Mise à jour manuelle des valeurs possible

### 📊 Analyses et visualisations
- Dashboard avec métriques principales
- Répartition par catégorie d'actif
- Répartition géographique 
- Analyse par banque et compte
- Analyse par type de produit
- Évolution temporelle du patrimoine

### ✅ Gestion des tâches
- Ajout de tâches liées aux actifs
- Liste centralisée des tâches à faire
- Marquage des tâches comme terminées

### 🔐 Sécurité renforcée
- Base de données SQLite chiffrée
- Chiffrement des données sensibles au niveau des champs
- Système de sauvegarde et restauration chiffré
- Mots de passe hachés avec Bcrypt

## 🛠️ Technologies utilisées

- **Backend**: Python, FastAPI, SQLAlchemy
- **Frontend**: Streamlit
- **Base de données**: SQLite (avec chiffrement)
- **Manipulation des données**: Pandas
- **Visualisations**: Matplotlib, Plotly
- **Authentification**: JWT
- **APIs externes**: Yahoo Finance, Open Exchange Rates

## 🚀 Installation

```bash
# Cloner le dépôt
git clone https://github.com/votre-username/gestion-patrimoniale.git
cd gestion-patrimoniale

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'application (première utilisation)
python setup.py

# Lancer l'application
streamlit run main.py
```

## 🧩 Structure de l'application

```
patrimoine_app/
├── backend/            # API FastAPI
├── data/               # Données et fichiers de base de données
├── database/           # Configuration et modèles de base de données
├── services/           # Services métier
├── ui/                 # Interface utilisateur Streamlit
├── utils/              # Utilitaires
├── config/             # Configuration de l'application
├── logs/               # Journaux d'application
└── static/             # Ressources statiques
```

## 🔒 Sécurité et confidentialité

- Toutes les données sensibles sont chiffrées dans la base de données
- Les mots de passe sont hachés et jamais stockés en clair
- Les sauvegardes sont chiffrées avec une clé dérivée de la clé principale
- Session sécurisée avec expiration automatique
- Protection contre les attaques par force brute

## 🔍 Utilisation

### Premier démarrage
1. Créez un compte administrateur
2. Ajoutez vos banques
3. Créez vos comptes pour chaque banque
4. Ajoutez vos actifs avec leurs allocations

### Workflow recommandé
1. Consultez le dashboard pour une vue d'ensemble
2. Utilisez les analyses pour optimiser votre allocation
3. Synchronisez régulièrement les prix pour suivre l'évolution
4. Créez des tâches pour les actions à entreprendre sur vos actifs

## 🔮 Évolutions prévues

- Import de données depuis des exports bancaires
- Intégration avec des API financières supplémentaires
- Alertes et notifications
- Application mobile compagnon
- Analyse de performance avancée
- Projections et simulations
- Outils de rééquilibrage automatique

## 📝 Licence

Ce projet est distribué sous licence MIT. Voir le fichier `LICENSE` pour plus d'informations.

## 🙏 Remerciements

- Libraries Python et JavaScript utilisées
- Communauté des développeurs pour leurs conseils
- Utilisateurs pour leurs retours et suggestions

---

© 2025 Application de Gestion Patrimoniale