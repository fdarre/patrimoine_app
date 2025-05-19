# Système de migrations pour l'application Patrimoine

Ce document explique le système de migrations de base de données intégré à l'application, basé sur Alembic et
SQLAlchemy.

## Qu'est-ce que c'est ?

Le système de migrations permet de :

- Versionner le schéma de base de données
- Appliquer des modifications structurelles de manière incrémentale
- Mettre à jour ou rétrograder la base de données vers n'importe quelle version
- Assurer la cohérence des données lors des mises à jour d'application

## Pourquoi c'est important ?

Sans système de migrations :

- Les modifications de schéma peuvent entraîner des pertes de données
- Il est difficile de déployer des mises à jour sur des installations existantes
- On ne peut pas facilement revenir en arrière en cas de problème
- Le déploiement sur plusieurs environnements devient complexe

## Structure du système

Le système est composé de :

- `migrations/` : Dossier contenant toutes les migrations
    - `versions/` : Dossier contenant les fichiers de migration individuels
    - `env.py` : Configuration de l'environnement d'exécution des migrations
- `alembic.ini` : Fichier de configuration d'Alembic
- `migrate.py` : Script utilitaire pour gérer les migrations
- `utils/migration_manager.py` : Gestionnaire de migrations pour l'application

## Comment ça marche ?

1. **Initialisation** : Lors du démarrage de l'application, le système vérifie si la base de données est à jour avec les
   migrations.
2. **Historique** : Chaque modification de schéma est enregistrée dans un fichier de migration daté et numéroté.
3. **Opérations** : Les migrations contiennent des opérations "upgrade" (mise à jour) et "downgrade" (retour en
   arrière).
4. **État** : Alembic maintient une table `alembic_version` qui garde trace de la version actuelle.

## Commandes disponibles

Le script `migrate.py` fournit les commandes suivantes :

### Créer une nouvelle migration

```bash
python migrate.py create "Description de la migration"
```

Cette commande crée une nouvelle migration basée sur les différences entre les modèles SQLAlchemy et le schéma actuel.

Options :

- `--empty` : Crée une migration vide sans autogénération

### Mettre à jour la base de données

```bash
python migrate.py upgrade [--target VERSION]
```

Met à jour la base de données vers la dernière version ou une version spécifique.

### Rétrograder la base de données

```bash
python migrate.py downgrade VERSION
```

Rétrograde la base de données vers une version antérieure.

### Afficher l'état actuel

```bash
python migrate.py status
```

Affiche la version actuelle de la base de données.

### Initialiser la base de données

```bash
python migrate.py init
```

Initialise la base de données avec la dernière version des migrations.

## Cycle de développement

1. Modifiez les modèles dans `database/models.py`
2. Créez une migration : `python migrate.py create "Description"`
3. Vérifiez et ajustez le fichier de migration généré si nécessaire
4. Testez la migration : `python migrate.py upgrade`
5. En cas de problème, rétrograder : `python migrate.py downgrade`

## Cas particuliers avec le chiffrement

Notre application utilise un système de chiffrement au niveau des champs (`EncryptedString`, `EncryptedJSON`). Quelques
points importants :

- Les types personnalisés sont correctement gérés par Alembic
- Les migrations respectent le chiffrement des données existantes
- Les restaurations de sauvegardes appliquent automatiquement les migrations nécessaires

## Bonnes pratiques

1. **Migrer fréquemment** : Créez une migration pour chaque modification de modèle
2. **Descriptions claires** : Utilisez des messages descriptifs pour les migrations
3. **Vérification manuelle** : Examinez les fichiers générés avant de les appliquer
4. **Tests** : Testez les migrations sur un environnement de développement avant production
5. **Sauvegardes** : Effectuez toujours une sauvegarde avant d'appliquer des migrations majeures

## Résolution de problèmes

### Conflits de migration

Si deux développeurs créent des migrations parallèles, vous pouvez rencontrer des conflits. Dans ce cas :

- Identifiez la migration la plus récente commune
- Rétrograder jusqu'à cette version
- Fusionnez manuellement les changements
- Créez une nouvelle migration

### Erreurs lors des migrations

En cas d'erreur pendant une migration :

1. Consultez les logs d'erreur
2. Restaurez une sauvegarde si nécessaire
3. Corrigez le problème dans le fichier de migration
4. Relancez la migration

### Données incompatibles

Si une migration échoue en raison de données existantes incompatibles :

1. Créez une migration intermédiaire pour nettoyer/transformer les données
2. Puis appliquez la migration structurelle
