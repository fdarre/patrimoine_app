python
"""
Script de réinitialisation du chiffrement de la base de données
"""
import base64
import secrets
from pathlib import Path

# Chemin du fichier salt
DATA_DIR = Path("data")
salt_file = DATA_DIR / ".salt"

# Créer un nouveau sel et l'enregistrer
new_salt = secrets.token_bytes(16)
encoded_salt = base64.urlsafe_b64encode(new_salt).decode()

print(f"Création d'un nouveau sel: {encoded_salt}")
with open(salt_file, "w") as f:
    f.write(encoded_salt)

print(f"Nouveau sel enregistré dans {salt_file}")
print("IMPORTANT: Vous devez maintenant recréer votre base de données!")
