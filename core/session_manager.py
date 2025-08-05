# === core/session_manager.py ===
from core.session import GameSession

class SessionManager:
    """
    Gestionnaire singleton pour éviter les multiples instances de GameSession
    """
    _instance = None
    _session = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_session(cls, name=None):
        """
        Récupère ou crée une session unique
        """
        if cls._session is None and name:
            print(f"[SESSION_MGR] Création unique session pour: {name}")
            cls._session = GameSession(name)
        elif cls._session and name and cls._session.name != name:
            print(f"[SESSION_MGR] Changement de session: {cls._session.name} → {name}")
            cls._session = GameSession(name)
        elif cls._session:
            print(f"[SESSION_MGR] Réutilisation session existante: {cls._session.name}")
        
        return cls._session
    
    @classmethod
    def has_session(cls):
        """Vérifie si une session existe"""
        return cls._session is not None
    
    @classmethod
    def get_current_session(cls):
        """Récupère la session actuelle sans en créer une nouvelle"""
        return cls._session
    
    @classmethod
    def reset(cls):
        """Remet à zéro la session (pour debug/tests)"""
        print("[SESSION_MGR] Reset session")
        cls._session = None
