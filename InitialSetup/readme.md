Guide complet des commandes pour déploiement local

1. Préparation de l'environnement
   bash# Créer les dossiers nécessaires
   mkdir -p data logs data/key_backups
   chmod -R 755 data logs
2. Initialisation des clés (déjà fait)
   bash# python init_keys.py # Ne pas relancer
3. Création de la base de données
   bash# Créer les tables
   python create_db.py
4. Création d'un utilisateur administrateur
   bash# Créer un utilisateur admin
   python create_user.py
5. Gestion des migrations (optionnel)
   Si vous modifiez les modèles par la suite, vous pouvez utiliser les migrations:
   bash# Vérifier l'état actuel des migrations
   python migrate.py status

# Créer une nouvelle migration (après modification des modèles)

python migrate.py create "description_du_changement"

# Appliquer toutes les migrations

python migrate.py upgrade

6. Démarrer l'application
   bash# Pour localhost uniquement
   streamlit run main.py