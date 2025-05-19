#!/usr/bin/env python
"""
Script de gestion des migrations de base de données
"""
import argparse
import sys

from utils.logger import get_logger
from utils.migration_manager import migration_manager

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Gestion des migrations de base de données")
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")

    # Commande 'create': Créer une nouvelle migration
    create_parser = subparsers.add_parser("create", help="Créer une nouvelle migration")
    create_parser.add_argument("message", type=str, help="Message décrivant la migration")
    create_parser.add_argument("--empty", action="store_true", help="Créer une migration vide sans autogénération")

    # Commande 'upgrade': Mettre à jour la base de données
    upgrade_parser = subparsers.add_parser("upgrade", help="Mettre à jour la base de données")
    upgrade_parser.add_argument("--target", type=str, default="head",
                                help="Version cible (défaut: 'head' pour la dernière version)")

    # Commande 'downgrade': Rétrograder la base de données
    downgrade_parser = subparsers.add_parser("downgrade", help="Rétrograder la base de données")
    downgrade_parser.add_argument("target", type=str, help="Version cible")

    # Commande 'status': Afficher l'état actuel des migrations
    status_parser = subparsers.add_parser("status", help="Afficher l'état actuel des migrations")

    # Commande 'init': Initialiser la base de données avec les migrations
    init_parser = subparsers.add_parser("init", help="Initialiser la base de données")

    args = parser.parse_args()

    if args.command == "create":
        # Créer une nouvelle migration
        migration_manager.create_migration(args.message, not args.empty)
        print(f"Migration créée: {args.message}")

    elif args.command == "upgrade":
        # Mettre à jour la base de données
        migration_manager.upgrade_database(args.target)
        print(f"Base de données mise à jour vers: {args.target}")

    elif args.command == "downgrade":
        # Rétrograder la base de données
        print(f"Attention: Vous êtes sur le point de rétrograder la base de données vers {args.target}.")
        confirm = input("Cette opération peut entraîner une perte de données. Continuer? (oui/NON): ")

        if confirm.lower() == "oui":
            migration_manager.downgrade_database(args.target)
            print(f"Base de données rétrogradée vers: {args.target}")
        else:
            print("Opération annulée.")

    elif args.command == "status":
        # Afficher l'état actuel
        current = migration_manager.get_current_version()
        if current:
            print(f"Version actuelle de la base de données: {current}")
        else:
            print("Aucune migration n'a été appliquée ou la base n'existe pas.")

    elif args.command == "init":
        # Initialiser la base de données
        success = migration_manager.initialize_database()
        if success:
            print("Base de données initialisée avec succès.")
        else:
            print("Échec de l'initialisation de la base de données.")
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
