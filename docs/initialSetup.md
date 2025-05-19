# Guide de déploiement de l'application de gestion patrimoniale

## Processus de déploiement complet

### 1. Préparation de l'environnement

```bash
# Créer l'environnement virtuel Python
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows:
venv\Scripts\activate
# Sur Linux/Mac:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Créer les dossiers requis
mkdir -p data logs data/key_backups

2. Initialisation des clés de chiffrement
bash# Initialiser les clés de chiffrement (ÉTAPE CRITIQUE)
python init_keys.py
Génère les clés nécessaires pour le chiffrement de la base de données.
3. IMPORTANT: Premier lancement de l'application
bash# Démarrer l'application une première fois
streamlit run main.py
⚠️ CRITIQUE: Cette étape doit être effectuée AVANT toute manipulation des migrations.
Ce premier lancement:

Crée la structure initiale de la base de données
Initialise le système de fichiers nécessaire
Crée automatiquement un utilisateur admin (admin/admin123)
Prépare l'environnement pour que les migrations puissent fonctionner

Vous pouvez arrêter l'application avec Ctrl+C après que la page s'affiche dans votre navigateur.
4. Préparation des migrations
bash# Créer le dossier des versions de migrations s'il n'existe pas
mkdir -p migrations/versions

# Vérifier l'état actuel des migrations
python migrate.py status
Vérifie que le système de migrations est correctement initialisé. Le message "Aucune migration n'a été appliquée..." est normal à ce stade.
5. CRÉATION DE LA MIGRATION INITIALE (ÉTAPE MANQUANTE)
bash# Créer la migration initiale qui capture l'état actuel de la base
python migrate.py create "initial_schema"

# Appliquer cette première migration
python migrate.py upgrade
⚠️ IMPORTANT: Cette étape crée une "photo" de l'état initial de votre base de données qui servira de point de départ pour toutes les modifications futures.
Vous ne devez faire cette étape qu'une seule fois lors du déploiement initial.
6. Gestion des migrations futures
Pour créer et appliquer de nouvelles migrations (après modification des modèles):
bash# Créer une nouvelle migration
python migrate.py create "description_de_votre_changement"

# Vérifier le fichier généré dans migrations/versions/

# Appliquer la migration
python migrate.py upgrade
7. Relancer l'application
bash# Lancer l'application pour utilisation normale
streamlit run main.py
Dépannage

Si les migrations échouent: Assurez-vous d'avoir bien exécuté main.py au moins une fois avant.
Si la base de données est corrompue: Supprimez le fichier dans le dossier data et recommencez depuis l'étape 3.
Si vous obtenez des erreurs sur les clés: Vérifiez que init_keys.py a été exécuté correctement.

Workflow de développement
Après le déploiement initial, voici le workflow pour modifier la structure de la base de données:

Modifier les modèles dans database/models.py
Créer une migration: python migrate.py create "description"
Examiner le fichier généré dans migrations/versions/
Appliquer la migration: python migrate.py upgrade
Tester en lançant l'application: streamlit run main.py