#!/usr/bin/env python
"""
Script pour créer un utilisateur administrateur
"""
import uuid
from datetime import datetime

from database.db_config import get_db
from database.models import User
from utils.logger import get_logger
from utils.password import hash_password

logger = get_logger(__name__)


def main():
    """Crée un utilisateur administrateur si aucun n'existe"""
    try:
        db = next(get_db())
        try:
            # Vérifier si des utilisateurs existent déjà
            user_count = db.query(User).count()

            if user_count > 0:
                print(f"{user_count} utilisateurs existent déjà.")
                response = input("Voulez-vous créer un utilisateur admin supplémentaire? (o/N): ")
                if response.lower() != 'o':
                    print("Opération annulée.")
                    return False

            # Demander ou utiliser des informations par défaut
            use_defaults = input("Utiliser les valeurs par défaut (admin/admin123)? (O/n): ")

            if use_defaults.lower() == 'n':
                username = input("Nom d'utilisateur: ")
                email = input("Email: ")
                password = input("Mot de passe: ")

                if not username or not password:
                    print("Le nom d'utilisateur et le mot de passe sont obligatoires.")
                    return False
            else:
                username = "admin"
                email = "admin@exemple.com"
                password = "admin123"

            # Créer l'utilisateur
            admin_user = User(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                password_hash=hash_password(password),
                is_active=True,
                created_at=datetime.now()
            )

            db.add(admin_user)
            db.commit()

            print(f"Utilisateur {username} créé avec succès!")

            if use_defaults.lower() != 'n':
                print("\nIdentifiants par défaut:")
                print("Nom d'utilisateur: admin")
                print("Mot de passe: admin123")
                print("\nCHANGEZ CE MOT DE PASSE APRÈS VOTRE PREMIÈRE CONNEXION!")

            return True

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Erreur lors de la création de l'utilisateur: {str(e)}")
        print(f"Erreur: {str(e)}")

        if "no such table: users" in str(e):
            print("\nERREUR: La table 'users' n'existe pas.")
            print("Exécutez d'abord le script create_db.py pour créer les tables!")

        return False


if __name__ == "__main__":
    main()
