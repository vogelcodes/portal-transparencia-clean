"""
Security Utilities - Salt, Pepper, and Hash
"""
import os
import bcrypt
import hashlib
import secrets
import hmac
import json
import time
from base64 import urlsafe_b64encode, urlsafe_b64decode
from collections import defaultdict


def generate_salt() -> str:
    """Generate a cryptographically secure random salt."""
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """Hash password using bcrypt with a per-user salt."""
    password_with_salt = f"{password}{salt}".encode('utf-8')
    hashed = bcrypt.hashpw(password_with_salt, bcrypt.gensalt(rounds=12))
    return hashed.decode('utf-8')


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """Verify a password against stored hash."""
    try:
        password_with_salt = f"{password}{salt}".encode('utf-8')
        stored_hash = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_with_salt, stored_hash)
    except Exception:
        return False


def generate_token() -> str:
    """Generate a secure random token for sessions"""
    return secrets.token_urlsafe(64)


def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"ptk_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, api_key_hash: str) -> bool:
    """Verify an API key against stored hash"""
    return hash_api_key(api_key) == api_key_hash


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets security requirements."""
    if len(password) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres"
    if not any(c.isupper() for c in password):
        return False, "A senha deve conter pelo menos 1 letra maiúscula"
    if not any(c.islower() for c in password):
        return False, "A senha deve conter pelo menos 1 letra minúscula"
    if not any(c.isdigit() for c in password):
        return False, "A senha deve conter pelo menos 1 número"
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "A senha deve conter pelo menos 1 caractere especial (!@#$%)"
    return True, ""


def sanitize_username(username: str) -> str:
    """Sanitize username to prevent injection"""
    return ''.join(c for c in username if c.isalnum() or c in '_-').lower()


def sanitize_email(email: str) -> str:
    """Basic email sanitization"""
    return email.strip().lower()


class RateLimiter:
    """Simple in-memory rate limiter for login attempts."""
    
    _instance = None
    _attempts = defaultdict(list)
    _lockout_until = defaultdict(float)
    
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 300
    WINDOW = 300
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def is_locked_out(self, identifier: str) -> bool:
        if identifier in self._lockout_until:
            if time.time() < self._lockout_until[identifier]:
                return True
            else:
                del self._lockout_until[identifier]
                if identifier in self._attempts:
                    self._attempts[identifier] = []
        return False
    
    def record_attempt(self, identifier: str) -> None:
        current_time = time.time()
        self._attempts[identifier].append(current_time)
        self._attempts[identifier] = [
            t for t in self._attempts[identifier]
            if current_time - t < self.WINDOW
        ]
        if len(self._attempts[identifier]) >= self.MAX_ATTEMPTS:
            self._lockout_until[identifier] = current_time + self.LOCKOUT_DURATION
    
    def record_success(self, identifier: str) -> None:
        if identifier in self._attempts:
            del self._attempts[identifier]
        if identifier in self._lockout_until:
            del self._lockout_until[identifier]
    
    def get_remaining_lockout(self, identifier: str) -> int:
        if identifier in self._lockout_until:
            remaining = self._lockout_until[identifier] - time.time()
            return max(0, int(remaining))
        return 0
