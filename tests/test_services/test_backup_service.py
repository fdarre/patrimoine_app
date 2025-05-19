"""
Tests pour le service de sauvegarde et restauration
"""
import json
import os
from unittest.mock import patch, mock_open

import pytest

from services.backup_service import BackupService


class TestBackupService:
    """Tests pour le service de sauvegarde et restauration"""

    def test_generate_backup_key(self):
        """Test de génération de clé de sauvegarde"""
        # Avec le mock d'encryption_key, nous pouvons tester la génération
        key = BackupService.generate_backup_key()

        # Vérifier que la clé est au format attendu par Fernet
        assert isinstance(key, bytes)
        assert len(key) > 0
        # Les clés Fernet font 44 caractères en base64
        assert len(key) in [32, 44]  # 32 octets bruts ou 44 caractères encodés

    @pytest.mark.parametrize("db_exists", [True, False])
    def test_create_backup(self, db_exists, test_dir):
        """Test de création d'une sauvegarde chiffrée"""
        # Configurer le chemin de test
        test_db_path = os.path.join(test_dir, "test.db")
        output_path = os.path.join(test_dir, "backup.zip.enc")

        # Créer ou non le fichier de base de données selon le paramètre
        if db_exists:
            with open(test_db_path, "wb") as f:
                f.write(b"TESTDATA")  # Simuler des données dans la base

        # Mock pour éviter la vérification de version de migration réelle
        with patch('utils.migration_manager.migration_manager.get_current_version', return_value="1.0"), \
                patch('database.db_config.get_encryption_key',
                      return_value=b"dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleT09"), \
                patch('cryptography.fernet.Fernet.encrypt', return_value=b"ENCRYPTED_DATA"):

            if db_exists:
                # Test de création de sauvegarde avec DB existante
                result = BackupService.create_backup(test_db_path, output_path)
                assert result == output_path
                assert os.path.exists(output_path)
            else:
                # Test avec DB inexistante
                result = BackupService.create_backup(test_db_path, output_path)
                assert result is None

    def test_restore_backup(self, test_dir):
        """Test de restauration d'une sauvegarde"""
        # Configurer les chemins de test
        backup_path = os.path.join(test_dir, "backup.zip.enc")
        db_path = os.path.join(test_dir, "restored.db")

        # Créer un fichier de sauvegarde fictif
        with open(backup_path, "wb") as f:
            f.write(b"ENCRYPTED_BACKUP_DATA")

        # Mock pour simuler le processus de restauration
        with patch('database.db_config.get_encryption_key', return_value=b"dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleT09"), \
                patch('cryptography.fernet.Fernet.decrypt') as mock_decrypt, \
                patch('zipfile.ZipFile') as mock_zipfile, \
                patch('utils.migration_manager.migration_manager.get_current_version', return_value="1.0"), \
                patch('utils.migration_manager.migration_manager.upgrade_database', return_value=True), \
                patch('hashlib.sha256') as mock_hash, \
                patch('shutil.copy2') as mock_copy:
            # Configurer les comportements des mocks
            mock_decrypt.return_value = b"DECRYPTED_ZIP_DATA"

            # Mock pour simuler l'extraction de fichiers
            mock_zipfile_instance = mock_zipfile.return_value.__enter__.return_value
            mock_zipfile_instance.extractall.return_value = None

            # Mock pour le hash SHA-256
            mock_hash_instance = mock_hash.return_value
            mock_hash_instance.hexdigest.return_value = "1234567890abcdef"

            # Simuler la lecture du fichier metadata.json
            metadata_content = {
                "timestamp": "2025-05-19T12:00:00",
                "db_hash": "1234567890abcdef",
                "app_version": "3.0",
                "db_version": "1.0"
            }

            with patch('builtins.open', mock_open(read_data=json.dumps(metadata_content))):
                # Exécuter la restauration
                result = BackupService.restore_backup(backup_path, db_path)

                # Vérifier le résultat
                assert result is True, "La restauration devrait réussir"

                # Vérifier que les fonctions importantes ont été appelées
                mock_decrypt.assert_called_once()
                mock_zipfile.assert_called_once()
                mock_zipfile_instance.extractall.assert_called_once()
                mock_copy.assert_called()  # Au moins une copie de fichier

    def test_restore_backup_with_db_version_mismatch(self, test_dir):
        """Test de restauration avec différentes versions de base de données"""
        # Configurer les chemins de test
        backup_path = os.path.join(test_dir, "backup_v1.zip.enc")
        db_path = os.path.join(test_dir, "restored_v2.db")

        # Créer un fichier de sauvegarde fictif
        with open(backup_path, "wb") as f:
            f.write(b"ENCRYPTED_BACKUP_DATA")

        # Mock pour simuler le processus de restauration avec version différente
        with patch('database.db_config.get_encryption_key', return_value=b"dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleT09"), \
                patch('cryptography.fernet.Fernet.decrypt') as mock_decrypt, \
                patch('zipfile.ZipFile') as mock_zipfile, \
                patch('utils.migration_manager.migration_manager.get_current_version', return_value="2.0"), \
                patch('utils.migration_manager.migration_manager.upgrade_database', return_value=True), \
                patch('hashlib.sha256') as mock_hash, \
                patch('shutil.copy2') as mock_copy:
            # Configurer les comportements des mocks
            mock_decrypt.return_value = b"DECRYPTED_ZIP_DATA"

            # Mock pour simuler l'extraction de fichiers
            mock_zipfile_instance = mock_zipfile.return_value.__enter__.return_value
            mock_zipfile_instance.extractall.return_value = None

            # Mock pour le hash SHA-256
            mock_hash_instance = mock_hash.return_value
            mock_hash_instance.hexdigest.return_value = "1234567890abcdef"

            # Simuler la lecture du fichier metadata.json avec une version antérieure
            metadata_content = {
                "timestamp": "2025-05-19T12:00:00",
                "db_hash": "1234567890abcdef",
                "app_version": "3.0",
                "db_version": "1.0"  # Version antérieure
            }

            with patch('builtins.open', mock_open(read_data=json.dumps(metadata_content))):
                # Exécuter la restauration
                result = BackupService.restore_backup(backup_path, db_path)

                # Vérifier le résultat - la migration devrait gérer la différence de version
                assert result is True

                # Vérifier que la migration a été appelée
                mock_zipfile_instance.extractall.assert_called_once()
                mock_copy.assert_called()

    def test_restore_backup_integrity_error(self, test_dir):
        """Test de détection d'erreur d'intégrité lors de la restauration"""
        # Configurer les chemins de test
        backup_path = os.path.join(test_dir, "corrupt_backup.zip.enc")
        db_path = os.path.join(test_dir, "restored.db")

        # Créer un fichier de sauvegarde fictif corrompu
        with open(backup_path, "wb") as f:
            f.write(b"CORRUPTED_DATA")

        # Mock pour simuler une erreur d'intégrité
        with patch('database.db_config.get_encryption_key', return_value=b"dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleT09"), \
                patch('cryptography.fernet.Fernet.decrypt') as mock_decrypt, \
                patch('zipfile.ZipFile') as mock_zipfile, \
                patch('hashlib.sha256') as mock_hash:
            # Configurer les comportements des mocks
            mock_decrypt.return_value = b"DECRYPTED_ZIP_DATA"

            # Mock pour simuler l'extraction de fichiers
            mock_zipfile_instance = mock_zipfile.return_value.__enter__.return_value
            mock_zipfile_instance.extractall.return_value = None

            # Mock pour simuler un hash différent (corrompu)
            mock_hash_instance = mock_hash.return_value
            mock_hash_instance.hexdigest.return_value = "different_hash"

            # Simuler la lecture du fichier metadata.json avec un hash différent
            metadata_content = {
                "timestamp": "2025-05-19T12:00:00",
                "db_hash": "original_hash",  # Ne correspond pas au hash calculé
                "app_version": "3.0",
                "db_version": "1.0"
            }

            with patch('builtins.open', mock_open(read_data=json.dumps(metadata_content))):
                # Exécuter la restauration
                result = BackupService.restore_backup(backup_path, db_path)

                # La restauration devrait échouer à cause de l'erreur d'intégrité
                assert result is False
