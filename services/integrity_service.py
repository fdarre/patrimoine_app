"""
Service de vérification de l'intégrité des données
"""
from sqlalchemy.orm import Session

from database.db_config import DataCorruptionError
from database.models import Asset, Bank, Account, User
from utils.error_manager import catch_exceptions
from utils.logger import get_logger

logger = get_logger(__name__)


class IntegrityService:
    """Service pour la vérification de l'intégrité des données chiffrées"""

    @staticmethod
    @catch_exceptions
    def verify_database_integrity(db: Session) -> bool:
        """
        Vérifie l'intégrité des données chiffrées dans la base

        Cette méthode teste l'accès à un échantillon de données chiffrées pour
        s'assurer que le déchiffrement fonctionne correctement.

        Args:
            db: Session de base de données

        Returns:
            True si l'intégrité est vérifiée, False sinon
        """
        try:
            # Échantillonnage de données chiffrées pour vérifier le déchiffrement
            assets = db.query(Asset).limit(5).all()
            banks = db.query(Bank).limit(5).all()
            accounts = db.query(Account).limit(5).all()
            users = db.query(User).limit(3).all()

            # Tester le déchiffrement des champs sensibles des actifs
            for asset in assets:
                # Accéder aux champs chiffrés force le déchiffrement
                _ = asset.nom
                if asset.allocation:
                    _ = asset.allocation
                if asset.geo_allocation:
                    _ = asset.geo_allocation
                if asset.notes:
                    _ = asset.notes

            # Tester le déchiffrement des champs sensibles des banques
            for bank in banks:
                _ = bank.nom
                if bank.notes:
                    _ = bank.notes

            # Tester le déchiffrement des champs sensibles des comptes
            for account in accounts:
                _ = account.libelle

            # Tester le déchiffrement des champs sensibles des utilisateurs
            for user in users:
                _ = user.email

            logger.info("Vérification d'intégrité réussie: échantillon de données déchiffré avec succès")
            return True
        except DataCorruptionError as e:
            logger.critical(f"Corruption détectée lors de la vérification d'intégrité: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'intégrité: {str(e)}")
            return False

    @staticmethod
    @catch_exceptions
    def perform_complete_integrity_scan(db: Session) -> dict:
        """
        Effectue une analyse complète de l'intégrité de la base de données

        Cette méthode parcourt toutes les données chiffrées et tente de les déchiffrer
        pour détecter d'éventuelles corruptions. Elle peut être longue sur de grandes bases.

        Args:
            db: Session de base de données

        Returns:
            Dictionnaire contenant les résultats du scan
        """
        results = {
            "total_scanned": 0,
            "corrupted": 0,
            "corrupted_items": [],
            "passed": True
        }

        try:
            # Scan complet des actifs
            assets = db.query(Asset).all()
            results["total_scanned"] += len(assets)

            for asset in assets:
                try:
                    # Tenter de déchiffrer tous les champs sensibles
                    _ = asset.nom
                    if asset.allocation:
                        _ = asset.allocation
                    if asset.geo_allocation:
                        _ = asset.geo_allocation
                    if asset.notes:
                        _ = asset.notes
                    if asset.todo:
                        _ = asset.todo
                except DataCorruptionError as e:
                    results["corrupted"] += 1
                    results["corrupted_items"].append({
                        "type": "Asset",
                        "id": asset.id,
                        "error": str(e)
                    })
                    results["passed"] = False

            # Scan des banques
            banks = db.query(Bank).all()
            results["total_scanned"] += len(banks)

            for bank in banks:
                try:
                    _ = bank.nom
                    if bank.notes:
                        _ = bank.notes
                except DataCorruptionError as e:
                    results["corrupted"] += 1
                    results["corrupted_items"].append({
                        "type": "Bank",
                        "id": bank.id,
                        "error": str(e)
                    })
                    results["passed"] = False

            # Scan des comptes
            accounts = db.query(Account).all()
            results["total_scanned"] += len(accounts)

            for account in accounts:
                try:
                    _ = account.libelle
                except DataCorruptionError as e:
                    results["corrupted"] += 1
                    results["corrupted_items"].append({
                        "type": "Account",
                        "id": account.id,
                        "error": str(e)
                    })
                    results["passed"] = False

            # Scan des utilisateurs
            users = db.query(User).all()
            results["total_scanned"] += len(users)

            for user in users:
                try:
                    _ = user.email
                except DataCorruptionError as e:
                    results["corrupted"] += 1
                    results["corrupted_items"].append({
                        "type": "User",
                        "id": user.id,
                        "error": str(e)
                    })
                    results["passed"] = False

            logger.info(
                f"Scan d'intégrité terminé: {results['total_scanned']} éléments scannés, {results['corrupted']} corruptions détectées")
            return results
        except Exception as e:
            logger.error(f"Erreur lors du scan d'intégrité: {str(e)}")
            results["passed"] = False
            results["error"] = str(e)
            return results


# Créer une instance singleton du service
integrity_service = IntegrityService()
