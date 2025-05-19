# README - Système de Chiffrement et Sauvegarde

## Sommaire

1. [Vue d'ensemble](#vue-densemble)
2. [Fonctionnement du chiffrement](#fonctionnement-du-chiffrement)
3. [Procédures de sauvegarde](#procédures-de-sauvegarde)
4. [Procédures de restauration](#procédures-de-restauration)
5. [Bonnes pratiques](#bonnes-pratiques)
6. [Résolution des problèmes](#résolution-des-problèmes)
7. [Commandes et outils](#commandes-et-outils)

## Vue d'ensemble

Cette application utilise un système de chiffrement avancé au niveau des champs pour protéger les données sensibles. Les
données sont stockées dans une base de données SQLite, avec certains champs sensibles cryptés individuellement. Ce
système est conçu pour offrir:

- **Sécurité maximale** de vos données sensibles
- **Facilité de sauvegarde** avec vérification d'intégrité
- **Robustesse** en cas de défaillance matérielle ou logicielle
- **Protection** contre la perte accidentelle des clés de chiffrement

Les mécanismes de chiffrement s'appuient sur l'algorithme Fernet (AES-128 en mode CBC) et utilisent un système de clés
dérivées avec sel cryptographique.

## Fonctionnement du chiffrement

### Les clés de chiffrement

Le système utilise deux fichiers principaux pour stocker les informations de chiffrement:

- **`.key`** : La clé principale de chiffrement (32 bytes)
- **`.salt`** : Le sel cryptographique utilisé pour la dérivation de clé (16 bytes)
- **`.key_metadata.json`** : Métadonnées incluant la version des clés et dates de vérification

Ces fichiers sont stockés dans le répertoire `data/` et sont essentiels pour accéder aux données. **Sans ces fichiers,
les données chiffrées ne peuvent pas être récupérées.**

### Initialisation du système

À la première utilisation:

1. Exécutez `python init_keys.py` pour générer les clés initiales
2. L'application crée automatiquement des sauvegardes de ces clés dans `data/key_backups/`
3. Une sauvegarde initiale spéciale avec le suffixe `_initial` est créée

### Versionnage des clés

Le système utilise un mécanisme de versionnage pour les clés:

- Chaque ensemble de clés a un numéro de version (v1, v2, etc.)
- Les sauvegardes incluent ce numéro pour faciliter l'identification
- En cas de rotation des clés, la version est incrémentée automatiquement

## Procédures de sauvegarde

### Sauvegarde automatique

L'application effectue des sauvegardes automatiques sur plusieurs niveaux:

1. **Sauvegarde quotidienne de la base de données**
    - Exécutée via `scheduled_backup.py`
    - Conservation des 7 dernières sauvegardes
    - Fichiers nommés `scheduled_backup_YYYYMMDD_HHMMSS.zip.enc`

2. **Sauvegarde quotidienne des clés**
    - Crée une copie quotidienne des fichiers de clés
    - Inclut version et date dans le nom du fichier

### Sauvegarde manuelle

Pour créer une sauvegarde manuelle:

1. **Via l'interface utilisateur**:
    - Accédez à l'onglet "Paramètres" > "Sauvegarde"
    - Cliquez sur "Créer une sauvegarde maintenant"
    - Utilisez le bouton "Télécharger la sauvegarde" pour récupérer le fichier

2. **Via un script**:
   ```bash
   python scheduled_backup.py
   ```

### Contenu d'une sauvegarde

Chaque fichier de sauvegarde (`.zip.enc`) contient:

- La base de données SQLite complète
- Un fichier `metadata.json` avec des informations de vérification d'intégrité
- Un hash SHA-256 de la base de données pour validation lors de la restauration

Les sauvegardes sont **chiffrées** avec les mêmes clés que la base de données.

## Procédures de restauration

### Restauration de la base de données

Pour restaurer une sauvegarde:

1. **Via l'interface utilisateur**:
    - Accédez à l'onglet "Paramètres" > "Sauvegarde"
    - Utilisez "Importer une sauvegarde" pour sélectionner le fichier `.zip.enc`
    - Cliquez sur "Restaurer la sauvegarde"
    - L'application créera automatiquement une sauvegarde de sécurité avant restauration

2. **Points importants à savoir**:
    - Les clés actuelles doivent être compatibles avec la sauvegarde
    - Une vérification d'intégrité est effectuée avant la restauration complète
    - En cas d'échec, la base originale reste inchangée

### Restauration des clés de chiffrement

Si les fichiers de clés (`.key` et `.salt`) sont perdus ou corrompus:

1. **Procédure de récupération**:
    - Localisez les fichiers de sauvegarde de clés dans `data/key_backups/`
    - Copiez les fichiers les plus récents (ou les fichiers `_initial`) vers le répertoire `data/`
    - Renommez-les en `.key` et `.salt` respectivement
   ```bash
   cp data/key_backups/key_backup_v1_20240519_120000 data/.key
   cp data/key_backups/salt_backup_v1_20240519_120000 data/.salt
   cp data/key_backups/metadata_backup_v1_20240519_120000 data/.key_metadata.json
   ```

2. **Vérification des clés restaurées**:
    - Lancez l'application normalement
    - Si les clés sont compatibles, un message de succès apparaît dans les logs
    - Si les clés ne sont pas compatibles, un message d'erreur est affiché

## Bonnes pratiques

### Gestion des clés

1. **Ne JAMAIS supprimer** les fichiers `.key` et `.salt` sans avoir des sauvegardes
2. **Sauvegarder les clés séparément** de la base de données (support physique différent)
3. **Conserver les sauvegardes initiales** des clés en lieu sûr
4. **Vérifier régulièrement** les sauvegardes en effectuant des restaurations de test

### Sauvegardes

1. **Créer des sauvegardes manuelles** avant toute opération critique
2. **Exporter régulièrement** les sauvegardes sur des supports externes
3. **Tester périodiquement** la restauration pour s'assurer que tout fonctionne
4. **Conserver plusieurs versions** de sauvegardes à différentes dates

### Rotation des clés (avancé)

La rotation des clés doit être effectuée avec **extrême prudence**:

1. Créer une sauvegarde complète de la base et des clés actuelles
2. Générer de nouvelles clés avec `python init_keys.py --force`
3. Recréer la base de données entière en important les données depuis l'ancienne base
4. Ceci n'est recommandé qu'en cas de suspicion de compromission des clés

## Résolution des problèmes

### Erreur "Fichiers de clés manquants"

Si l'application affiche "ERREUR CRITIQUE: Fichiers de clés manquants":

1. Vérifiez l'existence des fichiers `.key` et `.salt` dans le répertoire `data/`
2. Si absents, restaurez-les depuis les sauvegardes (
   voir [Restauration des clés](#restauration-des-clés-de-chiffrement))
3. Si aucune sauvegarde n'existe, vous devrez réinitialiser l'application et perdre les données chiffrées

### Erreur "Les clés ne peuvent pas déchiffrer les données existantes"

Cette erreur indique que les clés actuelles ne correspondent pas aux données:

1. Vérifiez que vous utilisez les bonnes clés
2. Restaurez une version antérieure des clés depuis les sauvegardes
3. Essayez les clés initiales (suffixe `_initial`) qui devraient toujours fonctionner avec la base originale

### Corruption de la base de données

En cas de corruption:

1. Ne pas paniquer, des sauvegardes existent
2. Restaurer la dernière sauvegarde automatique depuis `data/scheduled_backup_*`
3. Si cela échoue, essayer une sauvegarde plus ancienne

## Commandes et outils

### Scripts principaux

- **`init_keys.py`** : Initialise les clés de chiffrement
  ```bash
  python init_keys.py                 # Initialisation première installation
  python init_keys.py --force         # DANGER: Écrase les clés existantes
  ```

- **`scheduled_backup.py`** : Crée une sauvegarde complète
  ```bash
  python scheduled_backup.py          # Exécute une sauvegarde manuelle
  ```

- **`fixtures.py`** : Crée des données de test (développement)
  ```bash
  python fixtures.py                  # Ajoute des données de test
  python fixtures.py --reset          # Réinitialise la base et ajoute des données de test
  ```

### Emplacement des fichiers importants

- **Clés de chiffrement**: `data/.key`, `data/.salt`, `data/.key_metadata.json`
- **Sauvegardes des clés**: `data/key_backups/`
- **Base de données**: `data/patrimoine.db`
- **Sauvegardes automatiques**: `data/scheduled_backup_*.zip.enc`
- **Logs**: `logs/app.log`

---

En suivant ces instructions et bonnes pratiques, vous garantirez la sécurité et l'intégrité de vos données dans toutes
les situations.
