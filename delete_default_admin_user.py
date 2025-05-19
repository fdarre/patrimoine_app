from database.db_config import get_db_session
from services.auth_service import AuthService

# Supprimer l'utilisateur admin par défaut
with get_db_session() as db:
    # Récupérer l'utilisateur admin
    admin_user = AuthService.get_user_by_username(db, "admin")

    if admin_user:
        # Supprimer l'utilisateur
        if AuthService.delete_user(db, admin_user.id):
            print("Utilisateur admin par défaut supprimé avec succès")
        else:
            print("Échec de la suppression de l'utilisateur admin")
    else:
        print("Utilisateur admin non trouvé")
