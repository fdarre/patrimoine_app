"""
Tests pour le gestionnaire de migrations
"""
import os
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from alembic.config import Config

from utils.migration_manager import MigrationManager


class TestMigrationManager:
    """Tests pour le gestionnaire de migrations de base de données"""

    def test_init(self, test_dir):
        """Test d'initialisation du gestionnaire de migrations"""
        # Créer un fichier alembic.ini fictif
        ini_path = os.path.join(test_dir, "alembic.ini")
        with open(ini_path, "w") as f:
            f.write("[alembic]\nscript_location = migrations\n")

        # Tester l'initialisation réussie
        db_path = Path(os.path.join(test_dir, "test.db"))
        manager = MigrationManager(db_path, ini_path)

        assert manager.db_path == db_path
        assert manager.alembic_ini_path == ini_path

        # Tester l'initialisation avec un fichier inexistant
        with pytest.raises(FileNotFoundError):
            MigrationManager(db_path, "nonexistent.ini")

    def test_get_alembic_config(self, test_dir):
        """Test de récupération de la configuration Alembic"""
        # Créer un fichier alembic.ini fictif
        ini_path = os.path.join(test_dir, "alembic.ini")
        with open(ini_path, "w") as f:
            f.write("[alembic]\nscript_location = migrations\n")

        # Initialiser le gestionnaire
        db_path = Path(os.path.join(test_dir, "test.db"))
        manager = MigrationManager(db_path, ini_path)

        # Récupérer la configuration
        config = manager.get_alembic_config()

        # Vérifier que c'est bien un objet Config
        assert isinstance(config, Config)
        assert config.config_file_name == ini_path

    @patch('alembic.command.revision')
    def test_create_migration(self, mock_revision, test_dir):
        """Test de création d'une migration"""
        # Créer un fichier alembic.ini fictif
        ini_path = os.path.join(test_dir, "alembic.ini")
        with open(ini_path, "w") as f:
            f.write("[alembic]\nscript_location = migrations\n")

        # Initialiser le gestionnaire
        db_path = Path(os.path.join(test_dir, "test.db"))
        manager = MigrationManager(db_path, ini_path)

        # Mock pour le retour de la fonction revision
        mock_rev = MagicMock()
        mock_rev.revision = "abc123"
        mock_revision.return_value = mock_rev

        # Tester la création de migration automatique
        rev = manager.create_migration("Test Migration", True)

        # Vérifier que la commande revision a été appelée
        mock_revision.assert_called_once()
        mock_revision.assert_called_with(mock_revision.call_args[0][0], message="Test Migration", autogenerate=True)
        assert rev == "abc123"

        # Réinitialiser le mock
        mock_revision.reset_mock()
        mock_revision.return_value = mock_rev

        # Tester la création de migration manuelle
        rev = manager.create_migration("Manual Migration", False)

        # Vérifier que la commande revision a été appelée
        mock_revision.assert_called_once()
        mock_revision.assert_called_with(mock_revision.call_args[0][0], message="Manual Migration", autogenerate=False)
        assert rev == "abc123"

    @patch('alembic.command.upgrade')
    def test_upgrade_database(self, mock_upgrade, test_dir):
        """Test de mise à jour de la base de données"""
        # Créer un fichier alembic.ini fictif
        ini_path = os.path.join(test_dir, "alembic.ini")
        with open(ini_path, "w") as f:
            f.write("[alembic]\nscript_location = migrations\n")

        # Initialiser le gestionnaire
        db_path = Path(os.path.join(test_dir, "test.db"))
        manager = MigrationManager(db_path, ini_path)

        # Tester la mise à jour
        result = manager.upgrade_database("head")

        # Vérifier que la commande upgrade a été appelée
        mock_upgrade.assert_called_once()
        mock_upgrade.assert_called_with(mock_upgrade.call_args[0][0], "head")
        assert result is True

        # Tester la gestion d'erreur
        mock_upgrade.side_effect = Exception("Migration error")
        result = manager.upgrade_database("head")

        # La fonction devrait retourner False en cas d'erreur
        assert result is False

    @patch('alembic.command.downgrade')
    def test_downgrade_database(self, mock_downgrade, test_dir):
        """Test de rétrogradation de la base de données"""
        # Créer un fichier alembic.ini fictif
        ini_path = os.path.join(test_dir, "alembic.ini")
        with open(ini_path, "w") as f:
            f.write("[alembic]\nscript_location = migrations\n")

        # Initialiser le gestionnaire
        db_path = Path(os.path.join(test_dir, "test.db"))
        manager = MigrationManager(db_path, ini_path)

        # Tester la rétrogradation
        result = manager.downgrade_database("base")

        # Vérifier que la commande downgrade a été appelée
        mock_downgrade.assert_called_once()
        mock_downgrade.assert_called_with(mock_downgrade.call_args[0][0], "base")
        assert result is True

        # Tester la gestion d'erreur
        mock_downgrade.side_effect = Exception("Downgrade error")
        result = manager.downgrade_database("base")

        # La fonction devrait retourner False en cas d'erreur
        assert result is False

    def test_get_current_version_no_db(self, test_dir):
        """Test de récupération de version sans base de données"""
        # Créer un fichier alembic.ini fictif
        ini_path = os.path.join(test_dir, "alembic.ini")
        with open(ini_path, "w") as f:
            f.write("[alembic]\nscript_location = migrations\n")

        # Initialiser le gestionnaire avec un chemin de DB inexistant
        db_path = Path(os.path.join(test_dir, "nonexistent.db"))
        manager = MigrationManager(db_path, ini_path)

        # La version devrait être None si la base n'existe pas
        version = manager.get_current_version()
        assert version is None

    def test_get_current_version_with_db(self, test_dir):
        """Test de récupération de version avec base de données"""
        # Créer un fichier alembic.ini fictif
        ini_path = os.path.join(test_dir, "alembic.ini")
        with open(ini_path, "w") as f:
            f.write("[alembic]\nscript_location = migrations\n")

        # Créer une base SQLite avec une table alembic_version
        db_path = os.path.join(test_dir, "test_with_version.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        cursor.execute("INSERT INTO alembic_version VALUES ('abc123')")
        conn.commit()
        conn.close()

        # Initialiser le gestionnaire
        db_path = Path(db_path)
        manager = MigrationManager(db_path, ini_path)

        # Obtenir la version
        version = manager.get_current_version()

        # Vérifier que la version est correcte
        assert version == "abc123"

    def test_check_migration_compatibility(self, test_dir):
        """Test de vérification de compatibilité des migrations"""
        # Créer un fichier alembic.ini fictif
        ini_path = os.path.join(test_dir, "alembic.ini")
        with open(ini_path, "w") as f:
            f.write("[alembic]\nscript_location = migrations\n")

        # Créer une base SQLite avec une table alembic_version
        db_path = os.path.join(test_dir, "test_migration_compat.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        cursor.execute("INSERT INTO alembic_version VALUES ('abc123')")
        conn.commit()
        conn.close()

        # Initialiser le gestionnaire avec notre base existante
        db_path = Path(db_path)
        manager = MigrationManager(db_path, ini_path)

        # Patcher ScriptDirectory.from_config pour retourner un mock qui ne lève pas d'exception
        with patch('alembic.script.ScriptDirectory.from_config') as mock_from_config:
            # Configurer le mock pour retourner un ScriptDirectory simulé
            mock_script_dir = MagicMock()
            mock_from_config.return_value = mock_script_dir

            # Le mock get_revision doit retourner quelque chose sans lever d'exception
            mock_script_dir.get_revision.return_value = "some_revision"

            # Exécuter la méthode
            compatibility = manager.check_migration_compatibility()

            # Vérifier que get_revision a été appelé avec la bonne version
            mock_script_dir.get_revision.assert_called_with("abc123")

            # La compatibilité devrait être True
            assert compatibility is True

    @patch('alembic.command.upgrade')
    def test_initialize_database(self, mock_upgrade, test_dir):
        """Test d'initialisation de la base de données"""
        # Créer un fichier alembic.ini fictif
        ini_path = os.path.join(test_dir, "alembic.ini")
        with open(ini_path, "w") as f:
            f.write("[alembic]\nscript_location = migrations\n")

        # Initialiser le gestionnaire avec un chemin de BD inexistante
        db_path = Path(os.path.join(test_dir, "nonexistent.db"))
        manager = MigrationManager(db_path, ini_path)

        # Simuler l'initialisation
        result = manager.initialize_database()

        # Vérifier que command.upgrade a été appelé
        mock_upgrade.assert_called_once()
        mock_upgrade.assert_called_with(mock_upgrade.call_args[0][0], "head")

        # Le résultat devrait être True
        assert result is True

    @patch('alembic.script.ScriptDirectory.from_config')
    def test_get_available_migrations(self, mock_script_dir, test_dir):
        """Test de récupération des migrations disponibles"""
        # Créer un fichier alembic.ini fictif
        ini_path = os.path.join(test_dir, "alembic.ini")
        with open(ini_path, "w") as f:
            f.write("[alembic]\nscript_location = migrations\n")

        # Initialiser le gestionnaire
        db_path = Path(os.path.join(test_dir, "test.db"))
        manager = MigrationManager(db_path, ini_path)

        # Configurer le mock pour retourner une liste de révisions
        mock_revs = [MagicMock(), MagicMock()]
        mock_script_dir_instance = mock_script_dir.return_value
        mock_script_dir_instance.get_revisions.return_value = mock_revs

        # Exécuter la méthode
        revs = manager.get_available_migrations()

        # Vérifier que script_directory.get_revisions a été appelé
        mock_script_dir_instance.get_revisions.assert_called_once_with("head")
        assert revs == mock_revs

        @patch('services.backup_service.BackupService.create_backup')
        @patch('alembic.command.upgrade')
        def test_upgrade_database_with_backup(self, mock_upgrade, mock_backup, test_dir):
            """Test de mise à jour avec sauvegarde automatique"""
            # Créer un fichier alembic.ini fictif
            ini_path = os.path.join(test_dir, "alembic.ini")
            with open(ini_path, "w") as f:
                f.write("[alembic]\nscript_location = migrations\n")

            # Initialiser le gestionnaire
            db_path = Path(os.path.join(test_dir, "test.db"))
            manager = MigrationManager(db_path, ini_path)

            # Configurer le mock
            mock_backup.return_value = os.path.join(test_dir, "pre_migration_backup.zip.enc")

            # Tester la mise à jour
            result = manager.upgrade_database("head")

            # Vérifier que les fonctions ont été appelées
            mock_backup.assert_called_once()
            assert "pre_migration_" in mock_backup.call_args[1]['output_path']
            mock_upgrade.assert_called_once()

            # Vérifier le résultat
            assert result is True

        @patch('services.backup_service.BackupService.create_backup')
        @patch('alembic.command.downgrade')
        def test_downgrade_database_with_backup(self, mock_downgrade, mock_backup, test_dir):
            """Test de rétrogradation avec sauvegarde automatique"""
            # Créer un fichier alembic.ini fictif
            ini_path = os.path.join(test_dir, "alembic.ini")
            with open(ini_path, "w") as f:
                f.write("[alembic]\nscript_location = migrations\n")

            # Initialiser le gestionnaire
            db_path = Path(os.path.join(test_dir, "test.db"))
            manager = MigrationManager(db_path, ini_path)

            # Configurer le mock
            mock_backup.return_value = os.path.join(test_dir, "pre_downgrade_backup.zip.enc")

            # Tester la rétrogradation
            result = manager.downgrade_database("base")

            # Vérifier que les fonctions ont été appelées
            mock_backup.assert_called_once()
            assert "pre_downgrade_" in mock_backup.call_args[1]['output_path']
            mock_downgrade.assert_called_once()

            # Vérifier le résultat
            assert result is True

        @patch('services.backup_service.BackupService.create_backup')
        @patch('alembic.command.upgrade')
        def test_upgrade_database_backup_failure(self, mock_upgrade, mock_backup, test_dir):
            """Test de mise à jour avec échec de sauvegarde"""
            # Créer un fichier alembic.ini fictif
            ini_path = os.path.join(test_dir, "alembic.ini")
            with open(ini_path, "w") as f:
                f.write("[alembic]\nscript_location = migrations\n")

            # Initialiser le gestionnaire
            db_path = Path(os.path.join(test_dir, "test.db"))
            manager = MigrationManager(db_path, ini_path)

            # Configurer le mock pour simuler un échec de sauvegarde
            mock_backup.return_value = None

            # Tester la mise à jour
            result = manager.upgrade_database("head")

            # Vérifier que les fonctions ont été appelées
            mock_backup.assert_called_once()
            mock_upgrade.assert_called_once()

            # La migration doit quand même réussir même si le backup échoue
            assert result is True
