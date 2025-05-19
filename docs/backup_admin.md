Guide complet de mise en production - Application de Gestion Patrimoniale
Ce guide vous présente étape par étape toutes les actions nécessaires pour mettre votre application en production de
façon sécurisée et pérenne.

1. Préparation initiale
   A. Vérification de l'environnement
   bash# Vérifier que toutes les dépendances sont installées
   pip install -r requirements.txt

# S'assurer que les répertoires requis existent

mkdir -p data logs key_backups data/key_backups
B. Initialisation des clés de chiffrement (si non existantes)
bash# Cette commande génère les clés de sécurité pour chiffrer les données
python init_keys.py
Ce que ça fait : Crée les fichiers .key et .salt dans le dossier data/ ainsi qu'une sauvegarde initiale dans
data/key_backups/.
IMPORTANT : Faites immédiatement une copie de ces fichiers sur un support externe sécurisé. Sans ces clés, les données
chiffrées sont irrécupérables.

2. Configuration de la base de données
   A. Générer la migration du schéma complet
   bash# Créer une migration représentant le schéma complet actuel
   python migrate.py create "schema_complet"
   Ce que ça fait : Génère un fichier de migration dans migrations/versions/ qui contient toutes les instructions SQL
   pour créer votre schéma de base de données.
   B. Vérifier la migration générée
   Ouvrez le fichier généré (quelque chose comme migrations/versions/XXXX_schema_complet.py) et assurez-vous qu'il
   contient bien tous vos modèles (User, Bank, Account, Asset, HistoryPoint, etc.)
   C. Initialiser/mettre à jour la base de données
   bash# Initialise la base de données avec le schéma actuel
   python migrate.py upgrade
   Ce que ça fait : Crée ou met à jour la base de données avec le schéma défini dans les migrations.
   D. Vérifier l'état des migrations
   bash# Affiche la version actuelle de la base de données
   python migrate.py status
   Vous devriez voir un identifiant correspondant à la dernière migration appliquée.
3. Sécurisation des clés et sauvegardes manuelles
   A. Créer une sauvegarde initiale complète
   bash# Crée une sauvegarde manuelle chiffrée
   python scheduled_backup.py
   Ce que ça fait : Crée un fichier data/scheduled_backup_YYYYMMDD_HHMMSS.zip.enc contenant une sauvegarde chiffrée de
   votre base de données.
   B. Copier les fichiers critiques sur un support externe
   Copiez sur une clé USB ou un stockage cloud sécurisé :

Fichiers de clés : data/.key et data/.salt
Métadonnées des clés : data/.key_metadata.json
Sauvegarde initiale des clés : tous les fichiers data/key_backups/*_initial_*
Sauvegarde de la base : le fichier data/scheduled_backup_*.zip.enc créé à l'étape précédente

4. Configuration des sauvegardes automatiques
   A. Configurer une tâche planifiée pour les sauvegardes
   Sous Linux/Mac (crontab)
   bash# Ouvrir l'éditeur crontab
   crontab -e

# Ajouter cette ligne pour une exécution quotidienne à 2h du matin

0 2 * * * cd /chemin/vers/application && python scheduled_backup.py
Sous Windows (Planificateur de tâches)

Ouvrez le "Planificateur de tâches"
Créez une nouvelle tâche pour exécuter python scheduled_backup.py tous les jours
Définissez le répertoire de démarrage à l'emplacement de votre application

B. Tester la sauvegarde automatique
bash# Exécuter manuellement le script de sauvegarde pour vérifier son fonctionnement
python scheduled_backup.py
Vérifiez qu'un nouveau fichier apparaît dans data/scheduled_backup_*.zip.enc

5. Premier démarrage
   A. Démarrer l'application
   bash# Démarrer l'application Streamlit
   streamlit run main.py
   B. Créer un compte administrateur

Accédez à l'interface d'inscription
Créez un compte administrateur (le premier compte créé est administrateur)
Connectez-vous avec ce compte

C. Configurer les banques et comptes
Avant d'ajouter vos actifs, configurez d'abord vos banques et comptes dans l'interface.
D. Effectuer une sauvegarde après la configuration initiale
bashpython scheduled_backup.py

6. En cas de problème : Procédure de récupération
   A. Récupérer depuis une sauvegarde automatique
   bash# Démarrer l'application normalement
   streamlit run main.py

# Dans l'interface : Paramètres > Sauvegarde > Restaurer une sauvegarde

# Sélectionnez le fichier sauvegarde récent (.zip.enc)

B. Si les clés sont perdues ou corrompues

Arrêtez l'application
Restaurez les fichiers .key, .salt et .key_metadata.json depuis votre copie de sauvegarde
Placez-les dans le répertoire data/
Redémarrez l'application

C. Récupération manuelle (en dernier recours)
bash# Arrêtez l'application si elle est en cours d'exécution

# Restaurer les clés depuis les sauvegardes

cp data/key_backups/key_backup_v1_XXXXX data/.key
cp data/key_backups/salt_backup_v1_XXXXX data/.salt
cp data/key_backups/metadata_backup_v1_XXXXX data/.key_metadata.json

# Restaurer la base de données depuis une sauvegarde

python -c "from services.backup_service import BackupService; BackupService.restore_backup('
data/scheduled_backup_XXXXX.zip.enc', 'data/patrimoine.db')"

# Redémarrer l'application

streamlit run main.py

7. Documentation et vérifications périodiques
   A. Documentation à conserver
   Créez un dossier "BACKUP_ADMIN" contenant :

Ce guide d'exploitation
Les dates et chemins des sauvegardes initiales
La localisation des sauvegardes externes des clés

B. Vérifications périodiques recommandées

Hebdomadaire : Vérifiez que les sauvegardes automatiques se créent
Mensuelle : Effectuez un test de restauration sur une instance séparée
Trimestrielle : Mettez à jour vos sauvegardes externes des clés

8. Mise à jour future de l'application
   Si vous modifiez le code de l'application :
   bash# 1. Créez une sauvegarde avant la mise à jour
   python scheduled_backup.py

# 2. Si vous avez modifié les modèles, créez une migration

python migrate.py create "description_des_changements"

# 3. Appliquez les migrations

python migrate.py upgrade

# 4. Redémarrez l'application

streamlit run main.py
Résumé des éléments critiques à protéger

Fichiers de clés : data/.key, data/.salt, data/.key_metadata.json
Sauvegardes initiales des clés : data/key_backups/*_initial_*
Sauvegardes de la base de données : data/scheduled_backup_*.zip.enc
Base de données actuelle : data/patrimoine.db

Sans les fichiers de clés, les données chiffrées sont irrécupérables, même avec une sauvegarde de la base de données.
Assurez-vous de conserver ces fichiers en lieu sûr et de disposer de plusieurs copies.

Je vois que vous rencontrez une erreur avec Alembic lors de la création de votre migration. Cette erreur indique que
votre base de données n'est pas à jour avec les migrations existantes. Résolvons ce problème et continuons avec le guide
de mise en production.

1. Résolution de l'erreur de migration
   Pour résoudre l'erreur "Target database is not up to date", suivez ces étapes dans l'ordre:
   bash# 1. Vérifiez d'abord l'état actuel
   python migrate.py status

# 2. Mettez à jour la base de données avec les migrations existantes

python migrate.py upgrade

# 3. Maintenant, essayez de créer votre migration

python migrate.py create "schema_complet"
Si cela ne fonctionne toujours pas, vous pouvez effectuer une initialisation complète:
bash# Initialiser la base de données (à utiliser avec précaution si vous avez déjà des données)
python migrate.py init

# Ensuite, créez la migration

python migrate.py create "schema_complet"

2. Guide complet de mise en production
   Une fois le problème de migration résolu, voici la marche à suivre étape par étape:
   A. Finalisation de la préparation
   bash# Vérifiez que tous les répertoires nécessaires existent
   mkdir -p data logs data/key_backups

# Vérifiez que les clés sont correctement générées

ls -la data/.key data/.salt data/.key_metadata.json

# Si elles n'existent pas, générez-les

python init_keys.py
B. Mise en place de la base de données
bash# Appliquez toutes les migrations pour initialiser/mettre à jour la base
python migrate.py upgrade head

# Vérifiez que tout est à jour

python migrate.py status
C. Sauvegarde initiale et sécurisation
bash# Créez une sauvegarde initiale complète
python scheduled_backup.py

# Vérifiez que la sauvegarde a été créée

ls -la data/scheduled_backup_*
D. Configuration des sauvegardes automatiques (très important)
Configurez une tâche cron pour exécuter automatiquement les sauvegardes:
bash# Ouvrir l'éditeur crontab
crontab -e

# Ajouter cette ligne pour une exécution quotidienne à 2h du matin

0 2 * * * cd /chemin/complet/vers/patrimoine_app && python scheduled_backup.py
E. Démarrage de l'application
bash# Démarrer l'application en mode production
streamlit run main.py
F. ÉLÉMENTS CRITIQUES À SAUVEGARDER IMMÉDIATEMENT
Copiez ces fichiers sur au moins deux supports externes différents (USB, cloud sécurisé, etc.):

Fichiers de clés de chiffrement:
data/.key
data/.salt
data/.key_metadata.json

Sauvegarde initiale des clés:
data/key_backups/*_initial_*

Première sauvegarde complète de la base:
data/scheduled_backup_*.zip.enc

CRUCIAL: Sans ces fichiers, vos données chiffrées seront IRRÉCUPÉRABLES même avec des sauvegardes!

3. Plan de récupération en cas de problème
   A. Si vous perdez la base de données

Assurez-vous que les fichiers de clés (.key et .salt) sont présents
Restaurez depuis la sauvegarde la plus récente:

Via l'interface: Paramètres > Sauvegarde > Restaurer une sauvegarde
Ou avec la commande:
bash# Remplacer XXXXX par le timestamp de la sauvegarde
python -c "from services.backup_service import BackupService; BackupService.restore_backup('
data/scheduled_backup_XXXXX.zip.enc', 'data/patrimoine.db')"

B. Si vous perdez les fichiers de clés

Arrêtez immédiatement l'application
Restaurez les fichiers de clés depuis votre sauvegarde externe:
bash# Copier les fichiers de clés depuis votre support externe
cp /chemin/vers/sauvegarde/.key data/
cp /chemin/vers/sauvegarde/.salt data/
cp /chemin/vers/sauvegarde/.key_metadata.json data/

Redémarrez l'application

C. Vérifications périodiques (recommandé)

Hebdomadaire: Vérifiez l'existence des fichiers de sauvegarde récents
bashls -la data/scheduled_backup_*

Mensuelle: Testez la restauration sur une instance séparée
bash# Copier la base et les sauvegardes vers un dossier de test
mkdir -p test_restore
cp data/patrimoine.db test_restore/
cp data/scheduled_backup_*.zip.enc test_restore/
cp data/.key test_restore/
cp data/.salt test_restore/
cp data/.key_metadata.json test_restore/

# Tester la restauration

cd test_restore
python -c "from services.backup_service import BackupService; BackupService.restore_backup('
scheduled_backup_XXXXX.zip.enc', 'patrimoine_test.db')"

4. Points d'attention spécifiques à votre application

Structure de données chiffrées: Soyez prudent si vous modifiez les modèles impliquant des champs chiffrés (
EncryptedString, EncryptedJSON). Créez toujours une migration et testez-la sur des données de test.
Sauvegardes des clés: La perte des fichiers .key et .salt est FATALE pour vos données. Créez des sauvegardes multiples
en lieu sûr.
Utilisation des types chiffrés: Les recherches sur les champs chiffrés sont limitées au niveau SQL. Tenez-en compte si
votre base de données devient volumineuse.

Votre application semble bien conçue pour une utilisation en production, une fois les problèmes de migration résolus. La
mise en place rigoureuse des sauvegardes est l'élément le plus critique avant d'y entrer vos données réelles.
Puis-je vous aider sur un aspect spécifique de cette mise en production?