#!/usr/bin/env python
"""
Script pour créer toutes les tables de la base de données
"""
from sqlalchemy import inspect

from database.db_config import engine
from database.models import Base
from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Crée toutes les tables définies dans les modèles"""
    try:
        # Vérifier si des tables existent déjà
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if existing_tables:
            print(f"Tables existantes: {', '.join(existing_tables)}")
            response = input("Des tables existent déjà. Voulez-vous continuer? (o/N): ")
            if response.lower() != 'o':
                print("Opération annulée.")
                return False

        # Créer toutes les tables définies dans les modèles
        print("Création des tables...")
        Base.metadata.create_all(bind=engine)

        print("\nTables créées avec succès!")
        print("\nUTILISEZ MAINTENANT create_user.py POUR CRÉER UN UTILISATEUR ADMIN")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de la création des tables: {str(e)}")
        print(f"Erreur: {str(e)}")
        return False


if __name__ == "__main__":
    main()
