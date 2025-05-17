"""
Définitions des exceptions personnalisées pour l'application
"""

class AppError(Exception):
    """Classe de base pour toutes les exceptions de l'application"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DatabaseError(AppError):
    """Exception levée lors d'erreurs de base de données"""
    pass


class ValidationError(AppError):
    """Exception levée lors d'erreurs de validation"""
    pass


class AuthenticationError(AppError):
    """Exception levée lors d'erreurs d'authentification"""
    pass


class ConfigurationError(AppError):
    """Exception levée lors d'erreurs de configuration"""
    pass


class SyncError(AppError):
    """Exception levée lors d'erreurs de synchronisation"""
    pass


class FileError(AppError):
    """Exception levée lors d'erreurs de manipulation de fichiers"""
    pass