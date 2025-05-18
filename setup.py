"""
Script de configuration initiale de l'application
"""
import getpass
import os

from config.app_config import DATA_DIR
from database.db_config import engine, SessionLocal, Base
from database.models import User
from utils.password import hash_password


def setup():
    """
    Configure l'application pour la première utilisation
    """
    print("Configuration initiale de l'application Gestion Patrimoniale")
    print("===========================================================")

    # Créer le répertoire de données s'il n'existe pas
    os.makedirs(DATA_DIR, exist_ok=True)

    # Créer les tables
    Base.metadata.create_all(bind=engine)

    # Vérifier si un utilisateur existe déjà
    db = SessionLocal()
    existing_user = db.query(User).first()

    if existing_user:
        print("Un utilisateur existe déjà. La configuration initiale a déjà été effectuée.")
        db.close()
        return

    # Créer le premier utilisateur (admin)
    print("\nCréation du compte administrateur:")

    while True:
        username = input("Nom d'utilisateur (admin): ") or "admin"
        email = input("Email: ")

        # Demander et confirmer le mot de passe
        while True:
            password = getpass.getpass("Mot de passe: ")
            password_confirm = getpass.getpass("Confirmer le mot de passe: ")

            if password == password_confirm:
                break
            else:
                print("Les mots de passe ne correspondent pas. Veuillez réessayer.")

        # Créer l'utilisateur
        admin_user = User(
            username=username,
            email=email,
            password_hash=hash_password(password)
        )

        db.add(admin_user)

        try:
            db.commit()
            print(f"\nCompte administrateur '{username}' créé avec succès!")
            break
        except Exception as e:
            db.rollback()
            print(f"Erreur lors de la création du compte: {str(e)}")
            retry = input("Voulez-vous réessayer? (o/n): ")
            if retry.lower() != 'o':
                break

    db.close()

    print("\nConfiguration terminée. Vous pouvez maintenant démarrer l'application.")


if __name__ == "__main__":
    setup()