Instructions pour les tests unitaires
Prérequis

Python 3.8 ou supérieur
pip (gestionnaire de paquets Python)

Installation des dépendances

Créez un environnement virtuel (recommandé):
bashpython -m venv venv

Activez l'environnement virtuel:

Sous Windows:
bashvenv\Scripts\activate

Sous Linux/MacOS:
bashsource venv/bin/activate

Installez les dépendances de test en utilisant setup.py:
bashpip install -e .
Ou installez directement les dépendances spécifiques pour les tests:
bashpip install -r requirements-test.txt

Organisez les fichiers de test dans la structure correcte (si ce n'est pas déjà fait):
bashpython organize_tests.py

Exécution des tests

Pour exécuter tous les tests:
bashpython -m pytest

Pour exécuter les tests avec rapport de couverture:
bashpython -m pytest --cov=.

Pour exécuter un fichier de test spécifique:
bashpython -m pytest tests/test_services/test_auth_service.py

Pour exécuter un test spécifique:
bashpython -m pytest tests/test_services/test_auth_service.py::TestAuthService::test_authenticate_user

Pour exécuter les tests avec rapport détaillé:
bashpython -m pytest -v

Pour générer un rapport de couverture HTML:
bashpython -m pytest --cov=. --cov-report=html
Les résultats seront disponibles dans le dossier htmlcov/.
Vous pouvez également utiliser le script helper fourni:
bashpython run_tests.py

Dépannage courant
Si vous rencontrez des erreurs:

Erreur "module not found": Vérifiez que vous êtes dans le répertoire racine du projet et que l'environnement virtuel est
activé.
Erreur "UNIQUE constraint failed": Les tests essaient de créer plusieurs utilisateurs avec le même nom. Assurez-vous que
les fixtures dans conftest.py génèrent des identifiants uniques.
Erreur "name 'X' is not defined": Vérifiez que tous les imports nécessaires sont présents dans les fichiers de test.
Test exact match assertions: Pour les tests de formatage, préférez des assertions souples (vérifier qu'une chaîne
contient certains éléments) plutôt que des égalités strictes.

Structure des tests

conftest.py: contient les fixtures partagées entre les tests
test_services/: tests pour les services principaux
test_utils/: tests pour les fonctions utilitaires

Conseils pour l'écriture de tests

Utilisez les fixtures pour réutiliser les configurations et données de test
Isolez les tests avec des mocks pour éviter les dépendances externes
Pour les tests nécessitant une base de données, utilisez des transactions qui sont annulées après chaque test
Pour les fonctions avec des effets secondaires (envoi d'emails, etc.), utilisez des mocks