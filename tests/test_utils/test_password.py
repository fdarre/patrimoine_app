"""
Tests pour les utilitaires de hachage et vérification des mots de passe
"""

from utils.password import hash_password, verify_password


class TestPassword:
    """Tests pour les utilitaires de mots de passe"""

    def test_hash_password(self):
        """Test du hachage de mot de passe"""
        # Cas 1: Hachage réussi
        password = "testpassword"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2")  # Format bcrypt

        # Cas 2: Hachage d'une chaîne vide
        empty_password = ""
        hashed_empty = hash_password(empty_password)

        assert hashed_empty is not None
        assert len(hashed_empty) > 0

        # Cas 3: Unicité des hashs
        password2 = "testpassword"
        hashed2 = hash_password(password2)

        assert hashed2 != hashed  # Les hashs doivent être différents même pour le même mot de passe (salt différent)

    def test_verify_password(self):
        """Test de vérification de mot de passe"""
        # Cas 1: Vérification réussie
        password = "testpassword"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

        # Cas 2: Mot de passe incorrect
        wrong_password = "wrongpassword"
        assert verify_password(wrong_password, hashed) is False

        # Cas 3: Hash invalide
        invalid_hash = "invalid_hash"
        assert verify_password(password, invalid_hash) is False

        # Cas 4: Mot de passe vide
        empty_password = ""
        hashed_empty = hash_password(empty_password)

        assert verify_password(empty_password, hashed_empty) is True
        assert verify_password("not_empty", hashed_empty) is False
