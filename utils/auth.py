"""
Authentication and password security utilities using bcrypt.
Manages current logged-in farmer session state.
"""

import bcrypt
from database.models import Farmer


class AuthManager:
    """Manages password hashing and current farmer session."""
    _current_farmer: Farmer = None

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash plain text password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify plain text password against bcrypt hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    @classmethod
    def set_current_farmer(cls, farmer: Farmer):
        """Set active logged-in farmer profile."""
        cls._current_farmer = farmer

    @classmethod
    def get_current_farmer(cls) -> Farmer:
        """Get active logged-in farmer profile."""
        return cls._current_farmer

    @classmethod
    def logout(cls):
        """Clear active session."""
        cls._current_farmer = None
